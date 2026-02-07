# StockWise MVP ☕

A microSaaS tool that prevents cafes from running out of key ingredients by analyzing sales data and sending low-stock alerts.

## Features

- 📤 **CSV Upload**: Upload Square POS (or any POS) sales data via web interface
- 🗺️ **Custom Ingredient Mapping**: Web UI to map menu items to ingredients and quantities
- 📊 **Usage Forecasting**: Calculates 7-day rolling average to predict ingredient depletion
- 📧 **Email Alerts**: Sends automated alerts when ingredients are projected to run out in < 2 days
- 💾 **MongoDB Storage**: Stores all data for historical tracking
- ⚙️ **Configurable Stock Levels**: Set current stock levels per ingredient
- 📊 **Data Table View**: View detailed usage data in table format

## Tech Stack

- **Backend**: Python + Flask
- **Data Processing**: Pandas
- **Database**: MongoDB
- **Email**: SendGrid or SMTP
- **Frontend**: Simple HTML/CSS

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB (local or cloud like MongoDB Atlas)
- Email service (SendGrid API key OR SMTP credentials)

### Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and add your MongoDB URI and email credentials
```

5. **Start MongoDB** (if running locally):
```bash
# macOS (with Homebrew)
brew services start mongodb-community

# Or use MongoDB Atlas (cloud) - update MONGODB_URI in .env
```

6. **Run the application**:
```bash
python app.py
```

7. **Open your browser**:
```
http://localhost:5001/upload
```

## Configuration

### MongoDB Setup

**Option 1: Local MongoDB**
```bash
# Install MongoDB locally, then use:
MONGODB_URI=mongodb://localhost:27017/
```

**Option 2: MongoDB Atlas (Cloud)**
1. Create free account at https://www.mongodb.com/cloud/atlas
2. Create a cluster and get connection string
3. Update `.env`:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### Email Setup

**Option 1: SendGrid (Recommended)**
1. Sign up at https://sendgrid.com
2. Create API key
3. Update `.env`:
```
SENDGRID_API_KEY=SG.your_api_key_here
ALERT_EMAIL_FROM=alerts@yourdomain.com
```

**Option 2: SMTP (Gmail)**
1. Enable 2-factor authentication on Gmail
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Update `.env`:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Note**: If email is not configured, alerts will print to console (useful for testing).

## Testing

1. **Use the sample CSV**:
   - Located at `sample_data/sample_sales.csv`
   - Contains 7 days of sales data for Latte, Cappuccino, and Mocha

2. **Upload the sample CSV**:
   - Go to http://localhost:5000/upload
   - Enter your email address
   - Upload `sample_data/sample_sales.csv`
   - View forecast results

3. **Check alerts**:
   - If any ingredient is projected to run out in < 2 days, an email alert will be sent
   - Check your email inbox (or console output if email not configured)

## Ingredient Mapping

The MVP includes a hardcoded mapping for one cafe:

- **Latte** → 8 oz milk
- **Cappuccino** → 6 oz milk
- **Mocha** → 8 oz milk

This mapping is stored in MongoDB and can be extended later. The CSV processing looks for "Item Name" column and matches against these menu items.

## CSV Format

Expected CSV format (Square POS export):
```csv
Date,Item Name,Quantity,Price
2024-01-01,Latte,15,5.50
2024-01-01,Cappuccino,8,5.00
```

Required columns:
- **Date** (or any column with "date" in name)
- **Item Name** (or any column with "item", "name", or "product" in name)
- **Quantity** (optional - defaults to 1 per row)

## API Endpoints

- `GET /` - Redirects to upload page
- `GET /upload` - Upload form page
- `POST /upload` - Process CSV upload
- `GET /api/forecast?email=user@example.com` - Get latest forecast for an email

## Project Structure

```
StockWise!/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── email_service.py        # Email sending logic
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── templates/
│   └── upload.html       # Upload form page
├── sample_data/
│   └── sample_sales.csv  # Sample CSV for testing
└── uploads/              # Uploaded CSV files (created automatically)
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Render

1. **Push to GitHub** (make sure `.env` and `keys.env` are NOT committed)
2. **Create Render account** at https://render.com
3. **Create new Web Service** → Connect GitHub repo
4. **Set environment variables** in Render dashboard:
   - `MONGODB_URI` (from MongoDB Atlas)
   - `SENDGRID_API_KEY` (from SendGrid)
   - `ALERT_EMAIL_FROM` (your verified email)
   - `SECRET_KEY` (generate random key)
   - `PORT` (Render sets this automatically)
5. **Deploy!**

**Full guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## How It Works

1. **CSV Upload**: User uploads Square POS CSV with sales data
2. **Data Processing**: Pandas reads CSV and extracts daily sales by menu item
3. **Ingredient Mapping**: Each menu item is mapped to ingredients (e.g., Latte → 8oz milk)
4. **Usage Calculation**: Calculates daily usage of each ingredient
5. **Forecasting**: Uses 7-day rolling average to predict when stock will run out
6. **Alerting**: If projected days remaining < 2, sends email alert

## Current Features

✅ **Custom Ingredient Mapping** - Web UI to create/edit mappings  
✅ **Configurable Stock Levels** - Set current stock per ingredient  
✅ **Square POS Support** - Optimized CSV parsing for Square exports  
✅ **Data Table View** - View detailed usage data  
✅ **Email Alerts** - Automated low-stock notifications  
✅ **MongoDB Storage** - Persistent data storage  

## Future Enhancements

- Multi-cafe support with user accounts
- Dashboard with charts and trends
- Real-time Square POS API integration
- Multiple alert recipients
- SMS alerts
- Inventory tracking (not just forecasting)

## Troubleshooting

**MongoDB Connection Error**:
- Ensure MongoDB is running locally OR
- Check MongoDB Atlas connection string in `.env`

**Email Not Sending**:
- Check SendGrid API key or SMTP credentials in `.env`
- For testing, alerts will print to console if email not configured

**CSV Processing Error**:
- Ensure CSV has "Date" and "Item Name" columns
- Check that menu items match the ingredient mapping (Latte, Cappuccino, Mocha)

## License

MIT License - Feel free to use and modify for your needs.

## Support

For issues or questions, check the code comments or create an issue in the repository.

---

Built with ❤️ for cafe owners who never want to run out of milk again.
