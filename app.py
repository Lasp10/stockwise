"""
StockWise MVP - MicroSaaS tool to prevent cafes from running out of ingredients
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from dotenv import load_dotenv

# Import email service
from email_service import send_low_stock_alert

# Import configuration
from config import Config

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
# Add TEST_MODE to app config
app.config['TEST_MODE'] = Config.TEST_MODE

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB connection
try:
    mongo_client = MongoClient(app.config['MONGODB_URI'])
    db = mongo_client[app.config['MONGODB_DB_NAME']]
    csv_collection = db['csv_uploads']
    mappings_collection = db['ingredient_mappings']
    alerts_collection = db['alerts']
    print("✓ Connected to MongoDB")
except Exception as e:
    print(f"⚠ MongoDB connection error: {e}")
    print("⚠ Continuing without MongoDB - using local storage fallback")
    db = None

# Hardcoded ingredient mapping for MVP
# Format: {menu_item: {ingredient: amount_in_oz}}
DEFAULT_INGREDIENT_MAPPING = {
    'Latte': {'milk': 8},
    'Cappuccino': {'milk': 6},
    'Mocha': {'milk': 8},
    'latte': {'milk': 8},  # Case variations
    'cappuccino': {'milk': 6},
    'mocha': {'milk': 8},
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_ingredient_mapping(email):
    """Get ingredient mapping from MongoDB, or return default"""
    if db is not None:
        mapping_doc = mappings_collection.find_one(
            {'email': email},
            sort=[('updated_at', -1)]
        )
        if mapping_doc and 'mapping' in mapping_doc:
            return mapping_doc['mapping']
    return DEFAULT_INGREDIENT_MAPPING

def store_ingredient_mapping(email, mapping=None):
    """Store ingredient mapping in MongoDB"""
    if mapping is None:
        mapping = DEFAULT_INGREDIENT_MAPPING
    
    if db is not None:
        # Check if mapping exists
        existing = mappings_collection.find_one({'email': email})
        
        mapping_doc = {
            'email': email,
            'mapping': mapping,
            'updated_at': datetime.utcnow()
        }
        
        if existing:
            # Update existing mapping
            mappings_collection.update_one(
                {'email': email},
                {'$set': mapping_doc}
            )
        else:
            # Create new mapping
            mapping_doc['created_at'] = datetime.utcnow()
            mappings_collection.insert_one(mapping_doc)
    
    return mapping

def detect_csv_format(file_path):
    """
    Intelligently detect CSV format and read it appropriately
    Handles various encodings, delimiters, and malformed formats
    Optimized for Square POS exports
    """
    import csv
    from io import StringIO
    
    # Square POS common formats:
    # 1. Standard CSV with headers
    # 2. TSV (tab-separated)
    # 3. Excel-exported CSV (may have BOM)
    # 4. Quoted rows format
    
    # Try different encodings (Square POS often uses UTF-8 with BOM)
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first few lines to detect format
                first_lines = [f.readline() for _ in range(5)]
                f.seek(0)
                
                # Check if it's Square POS format (common headers)
                sample_text = ''.join(first_lines[:3])
                is_square_pos = any(keyword in sample_text.lower() for keyword in 
                                  ['item name', 'item_name', 'product name', 'sku', 
                                   'quantity sold', 'net sales', 'gross sales'])
                
                # Detect delimiter - Square POS usually uses comma or tab
                sample = f.read(2048)  # Read more for better detection
                f.seek(0)
                
                # Try comma first (most common for Square)
                if ',' in sample:
                    delimiter = ','
                elif '\t' in sample:
                    delimiter = '\t'
                else:
                    # Use sniffer as fallback
                    try:
                        sniffer = csv.Sniffer()
                        delimiter = sniffer.sniff(sample).delimiter
                    except:
                        delimiter = ','
                
                # Try reading with pandas - Square POS specific handling
                try:
                    # Square POS exports often have headers in first row
                    df = pd.read_csv(f, encoding=encoding, delimiter=delimiter, 
                                    quotechar='"', skipinitialspace=True, 
                                    on_bad_lines='skip', engine='python',
                                    skip_blank_lines=True)
                except (TypeError, ValueError):
                    # Fallback for older pandas versions
                    f.seek(0)
                    df = pd.read_csv(f, encoding=encoding, delimiter=delimiter, 
                                    quotechar='"', skipinitialspace=True, 
                                    engine='python')
                
                # Clean up Square POS specific issues
                if not df.empty:
                    # Remove completely empty rows
                    df = df.dropna(how='all')
                    # Remove rows where all values are the same (often headers repeated)
                    if len(df) > 1:
                        df = df[df.astype(str).nunique(axis=1) > 1]
                
                if len(df.columns) > 1 and not df.empty:
                    print(f"✓ Detected CSV format: {encoding} encoding, {delimiter} delimiter")
                    if is_square_pos:
                        print("✓ Detected Square POS format")
                    return df
                    
        except Exception as e:
            continue
    
    # If standard reading fails, try manual parsing
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check if entire rows are quoted
        if lines and lines[0].strip().startswith('"') and ',' in lines[0]:
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                cleaned_lines.append(line)
            
            csv_string = '\n'.join(cleaned_lines)
            df = pd.read_csv(StringIO(csv_string))
            return df
    except:
        pass
    
    # Last resort: try reading with default settings
    return pd.read_csv(file_path, on_bad_lines='skip', engine='python')

def find_column_by_keywords(df, keywords_list, priority_order=None):
    """
    Find column by matching keywords (case-insensitive, partial match)
    Returns best match based on priority
    """
    df_cols_lower = [col.lower() for col in df.columns]
    
    # If priority order specified, use it
    if priority_order:
        for priority_keyword in priority_order:
            for i, col_lower in enumerate(df_cols_lower):
                if priority_keyword.lower() in col_lower:
                    return df.columns[i]
    
    # Otherwise, find first match
    for keywords in keywords_list:
        for keyword in keywords:
            for i, col_lower in enumerate(df_cols_lower):
                if keyword.lower() in col_lower:
                    return df.columns[i]
    
    return None

def process_csv(file_path, email, stock_levels=None):
    """
    Process CSV file and calculate ingredient usage
    Adapts to various CSV formats automatically
    
    Args:
        file_path: Path to CSV file
        email: User email address
        stock_levels: Dict of {ingredient: stock_amount_in_oz}, defaults to 1000oz per ingredient
    """
    # Default stock levels if not provided
    if stock_levels is None:
        stock_levels = {}
    try:
        # Intelligently detect and read CSV
        df = detect_csv_format(file_path)
        
        if df.empty:
            raise ValueError("CSV file is empty or could not be parsed")
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.strip('"').str.strip("'").str.lower()
        
        # Intelligently find columns using multiple strategies
        # Date column - try various date-related keywords
        date_col = find_column_by_keywords(
            df, 
            [['date', 'time', 'timestamp', 'created', 'sold', 'order'], 
             ['day', 'when', 'dt']],
            priority_order=['date', 'time', 'timestamp']
        )
        
        # Item column - try product/item related keywords
        item_col = find_column_by_keywords(
            df,
            [['item', 'product', 'name', 'menu', 'sku'],
             ['description', 'title', 'product_name', 'item_name']],
            priority_order=['item', 'product', 'name']
        )
        
        # Quantity column
        qty_col = find_column_by_keywords(
            df,
            [['quantity', 'qty', 'amount', 'count', 'units'],
             ['qty', 'num', 'number']],
            priority_order=['quantity', 'qty', 'amount']
        )
        
        # If still not found, try using first few columns as fallback
        if not date_col and len(df.columns) > 0:
            # Check if first column looks like dates
            first_col = df.columns[0]
            sample_values = df[first_col].head(5).astype(str)
            if any(pd.to_datetime(sample_values, errors='coerce').notna().any()):
                date_col = first_col
        
        if not item_col and len(df.columns) > 1:
            # Use second column as item if date was first
            if date_col == df.columns[0] and len(df.columns) > 1:
                item_col = df.columns[1]
            else:
                item_col = df.columns[0] if df.columns[0] != date_col else (df.columns[1] if len(df.columns) > 1 else None)
        
        if not date_col or not item_col:
            available_cols = ', '.join(df.columns.tolist())
            raise ValueError(
                f"Could not automatically detect required columns.\n"
                f"Found columns: {available_cols}\n"
                f"Please ensure your CSV has date/time and item/product columns."
            )
        
        print(f"✓ Detected columns - Date: {date_col}, Item: {item_col}, Quantity: {qty_col if qty_col else 'N/A (using 1 per row)'}")
        
        # Clean data - strip quotes from all string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip().str.strip('"').str.strip("'")
        
        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        # Use quantity column if available, otherwise assume 1 per row
        if qty_col:
            df['quantity'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
        else:
            df['quantity'] = 1
        
        # Get ingredient mapping (from MongoDB or default)
        mapping = get_ingredient_mapping(email)
        
        # Create a case-insensitive lookup dictionary
        mapping_lookup = {}
        for key, value in mapping.items():
            mapping_lookup[key.lower().strip()] = value
        
        # Calculate daily ingredient usage
        daily_usage = {}
        found_items = set()
        all_items = set()
        
        for _, row in df.iterrows():
            item_name = str(row[item_col]).strip()
            item_name_lower = item_name.lower().strip()
            all_items.add(item_name)
            
            # Get quantity (already cleaned and converted)
            quantity = float(row['quantity'])
            
            # Get date (already parsed)
            date = row[date_col].date()
            
            # Find matching ingredient mapping (case-insensitive)
            if item_name_lower in mapping_lookup:
                found_items.add(item_name)
                ingredients = mapping_lookup[item_name_lower]
                for ingredient, amount_per_unit in ingredients.items():
                    if ingredient not in daily_usage:
                        daily_usage[ingredient] = {}
                    if date not in daily_usage[ingredient]:
                        daily_usage[ingredient][date] = 0
                    daily_usage[ingredient][date] += amount_per_unit * quantity
        
        # Convert to DataFrame for easier processing
        usage_data = []
        for ingredient, dates in daily_usage.items():
            for date, amount in dates.items():
                usage_data.append({
                    'date': date,
                    'ingredient': ingredient,
                    'usage_oz': amount
                })
        
        usage_df = pd.DataFrame(usage_data)
        
        if usage_df.empty:
            # Provide helpful error message
            found_items_str = ', '.join(sorted(all_items)) if all_items else 'none'
            mapped_items = ', '.join(sorted(set([k.title() for k in mapping.keys() if k[0].isupper()])))
            print(f"Debug: Items found in CSV: {found_items_str}")
            print(f"Debug: Mapped items: {mapped_items}")
            raise ValueError(
                f"No matching menu items found in CSV.\n\n"
                f"Items found in CSV: {found_items_str}\n"
                f"Expected items (mapped): {mapped_items}\n\n"
                f"Please ensure your CSV contains items like: Latte, Cappuccino, or Mocha"
            )
        
        # Calculate 7-day rolling average
        usage_df = usage_df.sort_values('date')
        usage_df['date'] = pd.to_datetime(usage_df['date'])
        
        # Group by ingredient and calculate rolling average
        forecast_results = {}
        
        for ingredient in usage_df['ingredient'].unique():
            ing_df = usage_df[usage_df['ingredient'] == ingredient].copy()
            ing_df = ing_df.set_index('date')
            ing_df = ing_df.resample('D').sum().fillna(0)
            
            # Calculate 7-day rolling average
            rolling_avg = ing_df['usage_oz'].rolling(window=7, min_periods=1).mean().iloc[-1]
            
            # Get stock level from user input or use default
            current_stock_oz = stock_levels.get(ingredient, 1000)  # Default 1000oz if not specified
            days_remaining = current_stock_oz / rolling_avg if rolling_avg > 0 else float('inf')
            
            forecast_results[ingredient] = {
                'daily_avg_usage_oz': round(rolling_avg, 2),
                'days_remaining': round(days_remaining, 2),
                'current_stock_oz': current_stock_oz
            }
        
        # Store results in MongoDB
        if db is not None:
            result_doc = {
                'email': email,
                'file_path': file_path,
                'processed_at': datetime.utcnow(),
                'forecast': forecast_results,
                'usage_data': usage_df.to_dict('records')
            }
            csv_collection.insert_one(result_doc)
        
        return forecast_results, usage_df
        
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")

def check_and_send_alerts(email, forecast_results):
    """Check forecast results and send alerts if needed"""
    alerts_sent = []
    alerts_info = {
        'low_stock_items': [],
        'alerts_triggered': 0,
        'alerts_sent': 0,
        'email_configured': False
    }
    
    # Check if email is configured
    from config import Config
    email_configured = bool(
        (Config.SENDGRID_API_KEY and Config.SENDGRID_API_KEY.strip()) or
        (Config.SMTP_USERNAME and Config.SMTP_PASSWORD and 
         Config.SMTP_USERNAME.strip() and Config.SMTP_PASSWORD.strip())
    )
    alerts_info['email_configured'] = email_configured
    
    # Get threshold - use test mode if enabled
    threshold = app.config['LOW_STOCK_THRESHOLD']
    if app.config.get('TEST_MODE', False):
        threshold = 999  # Effectively send alerts for all ingredients in test mode
        print("⚠️ TEST MODE ENABLED - Sending alerts for all ingredients")
    
    for ingredient, forecast in forecast_results.items():
        days_remaining = forecast['days_remaining']
        
        if days_remaining < threshold:
            alerts_info['low_stock_items'].append({
                'ingredient': ingredient,
                'days_remaining': days_remaining
            })
            alerts_info['alerts_triggered'] += 1
            
            # Send alert
            try:
                send_low_stock_alert(
                    to_email=email,
                    ingredient=ingredient,
                    days_remaining=days_remaining,
                    daily_usage=forecast['daily_avg_usage_oz']
                )
                alerts_sent.append({
                    'ingredient': ingredient,
                    'days_remaining': days_remaining,
                    'status': 'sent' if email_configured else 'printed_to_console'
                })
                alerts_info['alerts_sent'] += 1
                
                # Log alert in MongoDB
                if db is not None:
                    alert_doc = {
                        'email': email,
                        'ingredient': ingredient,
                        'days_remaining': days_remaining,
                        'sent_at': datetime.utcnow(),
                        'email_configured': email_configured
                    }
                    alerts_collection.insert_one(alert_doc)
                    
            except Exception as e:
                alerts_sent.append({
                    'ingredient': ingredient,
                    'days_remaining': days_remaining,
                    'status': f'error: {str(e)}'
                })
    
    return alerts_sent, alerts_info

@app.route('/')
def index():
    """Home page - redirect to upload"""
    return redirect(url_for('upload'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """CSV upload page"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        email = request.form.get('email', '').strip()
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not email:
            flash('Email address is required', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Save file
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Get stock levels from form (optional)
                stock_levels = {}
                # Parse stock levels from form (format: stock_ingredient_name)
                for key, value in request.form.items():
                    if key.startswith('stock_') and value.strip():
                        # Convert stock_milk -> milk, stock_coffee_beans -> coffee beans
                        ingredient = key.replace('stock_', '').replace('_', ' ')
                        try:
                            stock_amount = float(value)
                            if stock_amount >= 0:  # Only accept non-negative values
                                stock_levels[ingredient] = stock_amount
                        except ValueError:
                            pass
                
                # Process CSV
                forecast_results, usage_df = process_csv(file_path, email, stock_levels)
                
                # Check and send alerts
                alerts_sent, alerts_info = check_and_send_alerts(email, forecast_results)
                
                # Prepare response data
                response_data = {
                    'success': True,
                    'email': email,
                    'forecast': forecast_results,
                    'alerts_sent': alerts_sent,
                    'alerts_info': alerts_info,
                    'usage_data': usage_df.to_dict('records')  # Include usage data for table view
                }
                
                flash('Upload successful! Alerts activated.', 'success')
                return render_template('upload.html', result=response_data)
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a CSV file.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/api/forecast', methods=['GET'])
def api_forecast():
    """API endpoint to get latest forecast for an email"""
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email parameter required'}), 400
    
    if db is not None:
        latest = csv_collection.find_one(
            {'email': email},
            sort=[('processed_at', -1)]
        )
        if latest:
            return jsonify({
                'email': email,
                'forecast': latest['forecast'],
                'processed_at': latest['processed_at'].isoformat()
            })
    
    return jsonify({'error': 'No forecast found for this email'}), 404

@app.route('/test-email')
def test_email():
    """Test email configuration"""
    test_email_addr = request.args.get('email', 'ankith.s.gundimeda@gmail.com')
    
    try:
        from email_service import send_low_stock_alert
        from config import Config
        
        # Check configuration
        config_status = {
            'sendgrid_configured': bool(Config.SENDGRID_API_KEY and Config.SENDGRID_API_KEY.strip()),
            'smtp_configured': bool(Config.SMTP_USERNAME and Config.SMTP_PASSWORD),
            'alert_email_from': Config.ALERT_EMAIL_FROM
        }
        
        # Try sending test email
        send_low_stock_alert(
            to_email=test_email_addr,
            ingredient='milk',
            days_remaining=1.5,
            daily_usage=500.0
        )
        
        return jsonify({
            'success': True,
            'message': f'Test email sent to {test_email_addr}',
            'config': config_status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'config': config_status
        }), 400

@app.route('/mappings', methods=['GET', 'POST'])
def mappings():
    """Ingredient mapping management page"""
    email = request.args.get('email') or (request.form.get('email', '').strip() if request.method == 'POST' else '')
    
    if request.method == 'POST':
        # Handle mapping updates
        action = request.form.get('action')
        
        if action == 'save':
            # Parse mapping from form
            mapping = {}
            
            # Get all menu items and their ingredients
            menu_items = []
            for key in request.form.keys():
                if key.startswith('menu_item_'):
                    item_index = key.replace('menu_item_', '')
                    menu_items.append(item_index)
            
            # Build mapping structure
            for item_index in set(menu_items):
                menu_item = request.form.get(f'menu_item_{item_index}', '').strip()
                if not menu_item:
                    continue
                
                # Get ingredients for this menu item
                ingredients = {}
                # Find all ingredient fields for this menu item
                for key in request.form.keys():
                    if key.startswith(f'ingredient_{item_index}_') and not key.startswith(f'ingredient_name_{item_index}_'):
                        # Get the ingredient name and amount
                        ing_suffix = key.replace(f'ingredient_{item_index}_', '')
                        ing_name = request.form.get(f'ingredient_name_{item_index}_{ing_suffix}', '').strip()
                        ing_amount = request.form.get(key, '').strip()
                        
                        if ing_name and ing_amount:
                            try:
                                ingredients[ing_name] = float(ing_amount)
                            except ValueError:
                                pass
                
                if ingredients:
                    mapping[menu_item] = ingredients
                    # Also add lowercase version for case-insensitive matching
                    mapping[menu_item.lower()] = ingredients
            
            # Save to MongoDB
            if email:
                store_ingredient_mapping(email, mapping)
                flash('Ingredient mappings saved successfully!', 'success')
            else:
                flash('Email address required to save mappings', 'error')
            
            return redirect(url_for('mappings', email=email))
        
        elif action == 'delete':
            item_to_delete = request.form.get('delete_item', '').strip()
            if email and item_to_delete:
                current_mapping = get_ingredient_mapping(email)
                if item_to_delete in current_mapping:
                    del current_mapping[item_to_delete]
                if item_to_delete.lower() in current_mapping:
                    del current_mapping[item_to_delete.lower()]
                store_ingredient_mapping(email, current_mapping)
                flash(f'Deleted mapping for {item_to_delete}', 'success')
            
            return redirect(url_for('mappings', email=email))
    
    # GET request - show mapping page
    current_mapping = {}
    if email:
        current_mapping = get_ingredient_mapping(email)
        # Filter out lowercase duplicates for display
        display_mapping = {}
        for key, value in current_mapping.items():
            if key[0].isupper() or key == key.lower():
                # Only show if it's capitalized or all lowercase (not a duplicate)
                if key.lower() not in display_mapping or key[0].isupper():
                    display_mapping[key] = value
        current_mapping = display_mapping
    
    return render_template('mappings.html', 
                         email=email, 
                         mapping=current_mapping,
                         default_mapping=DEFAULT_INGREDIENT_MAPPING)

@app.route('/download-sample')
def download_sample():
    """Download sample CSV file for testing"""
    sample_type = request.args.get('type', 'low_stock')  # 'low_stock' or 'normal'
    
    if sample_type == 'low_stock':
        filename = 'sample_low_stock.csv'
    else:
        filename = 'sample_sales.csv'
    
    # Use absolute path
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_data', filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, 
                        download_name=f'sample_{sample_type}.csv',
                        mimetype='text/csv')
    else:
        flash('Sample file not found', 'error')
        return redirect(url_for('upload'))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("StockWise MVP - Starting Flask Application")
    print("="*50)
    print(f"MongoDB URI: {app.config['MONGODB_URI']}")
    print(f"Database: {app.config['MONGODB_DB_NAME']}")
    print("="*50 + "\n")
    
    # Use PORT environment variable for Render/Heroku deployment
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
