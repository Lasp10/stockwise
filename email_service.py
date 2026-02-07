"""
Email service for sending low-stock alerts
Supports both SendGrid and SMTP
"""
import os
from config import Config

def send_low_stock_alert(to_email, ingredient, days_remaining, daily_usage):
    """
    Send low-stock alert email
    
    Args:
        to_email: Recipient email address
        ingredient: Name of ingredient (e.g., 'milk')
        days_remaining: Projected days until stock runs out
        daily_usage: Average daily usage in ounces
    """
    # Clean subject line without special characters (better deliverability)
    subject = f"Low Stock Alert - {ingredient.capitalize()} - {days_remaining:.1f} days remaining"
    
    # Plain text version (avoid spam trigger words)
    plain_message = f"""Hello,

This is an automated notification from StockWise.

Inventory Update

Ingredient: {ingredient.capitalize()}
Projected days remaining: approximately {days_remaining:.1f} days
Average daily usage: {daily_usage:.2f} oz

Please consider restocking soon.

---
StockWise Inventory Management System
"""
    
    # HTML version (better deliverability)
    html_message = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #fff; border-radius: 8px; padding: 30px; border: 1px solid #e0e0e0;">
        <h2 style="color: #dc3545; margin-top: 0; font-size: 24px;">Low Stock Alert</h2>
        
        <p>Hello,</p>
        
        <p>This is an automated alert from <strong>StockWise</strong>.</p>
        
        <div style="background: #e7f3ff; border-left: 4px solid #0052CC; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #0052CC;">Inventory Status Update</h3>
            <p style="margin-bottom: 5px;"><strong>Ingredient:</strong> {ingredient.capitalize()}</p>
            <p style="margin-bottom: 5px;"><strong>Projected days remaining:</strong> approximately {days_remaining:.1f} days</p>
            <p style="margin-bottom: 0;"><strong>Average daily usage:</strong> {daily_usage:.2f} oz</p>
        </div>
        
        <p>Please consider restocking soon to maintain inventory levels.</p>
        
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="color: #666; font-size: 12px; margin-bottom: 0;">
            StockWise - Automated Inventory Management<br>
            This is an automated message. Please do not reply to this email.
        </p>
        <p style="color: #999; font-size: 11px; margin-top: 20px; text-align: center;">
            <a href="mailto:{Config.ALERT_EMAIL_FROM}?subject=Unsubscribe" style="color: #999; text-decoration: none;">Unsubscribe</a> | 
            <a href="mailto:{Config.ALERT_EMAIL_FROM}?subject=Support" style="color: #999; text-decoration: none;">Contact Support</a>
        </p>
    </div>
</body>
</html>"""
    
    # Try SendGrid first if API key is configured
    if Config.SENDGRID_API_KEY and Config.SENDGRID_API_KEY.strip():
        try:
            send_via_sendgrid(to_email, subject, plain_message, html_message)
            print(f"✓ Alert sent via SendGrid to {to_email}")
            return
        except Exception as e:
            error_msg = str(e)
            print(f"⚠ SendGrid failed: {error_msg}")
            # Don't try SMTP if SendGrid is configured but failed - show the error
            if "sender" in error_msg.lower() or "from" in error_msg.lower() or "verify" in error_msg.lower():
                print(f"\n⚠️ IMPORTANT: You may need to verify your sender email in SendGrid:")
                print(f"   1. Go to: https://app.sendgrid.com/settings/sender_auth")
                print(f"   2. Verify: {Config.ALERT_EMAIL_FROM}")
                print(f"   3. Or use Single Sender Verification\n")
            raise  # Re-raise so the error is shown in the UI
    
    # Fallback to SMTP
    if Config.SMTP_USERNAME and Config.SMTP_PASSWORD and Config.SMTP_USERNAME.strip() and Config.SMTP_PASSWORD.strip():
        try:
            send_via_smtp(to_email, subject, plain_message, html_message)
            print(f"✓ Alert sent via SMTP to {to_email}")
            return
        except Exception as e:
            print(f"⚠ SMTP failed: {e}")
    
    # If both fail, print to console (for development/testing)
    print("\n" + "="*50)
    print("EMAIL ALERT (Console Output - Email not configured)")
    print("="*50)
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Message:\n{plain_message}")
    print("="*50 + "\n")

def send_via_sendgrid(to_email, subject, plain_message, html_message=None):
    """Send email using SendGrid API"""
    # Fix SSL certificate issues
    import ssl
    import urllib3
    import warnings
    
    # Disable SSL verification warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    # Set unverified SSL context globally (for testing - not recommended for production)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except:
        pass
    
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        # Create email with both plain text and HTML for better deliverability
        message_obj = Mail(
            from_email=Config.ALERT_EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            plain_text_content=plain_message,
            html_content=html_message if html_message else None
        )
        
        # Add better headers to avoid spam
        if Config.ALERT_EMAIL_FROM:
            message_obj.reply_to = Config.ALERT_EMAIL_FROM
        
        sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
        response = sg.send(message_obj)
        
        if response.status_code not in [200, 201, 202]:
            # Get error details from response body
            error_body = ""
            try:
                error_body = response.body.decode('utf-8')
            except:
                pass
            raise Exception(f"SendGrid API returned status {response.status_code}: {error_body}")
            
    except ImportError as ie:
        if "certifi" in str(ie):
            # Try without certifi
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                import ssl
                import urllib3
                urllib3.disable_warnings()
                
                message_obj = Mail(
                    from_email=Config.ALERT_EMAIL_FROM,
                    to_emails=to_email,
                    subject=subject,
                    plain_text_content=message
                )
                
                sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
                response = sg.send(message_obj)
                
                if response.status_code not in [200, 201, 202]:
                    error_body = ""
                    try:
                        error_body = response.body.decode('utf-8')
                    except:
                        pass
                    raise Exception(f"SendGrid API returned status {response.status_code}: {error_body}")
            except Exception as e2:
                raise Exception(f"SendGrid error (no certifi): {str(e2)}")
        else:
            raise Exception("SendGrid package not installed. Run: pip install sendgrid")
    except Exception as e:
        # Re-raise with more context
        error_msg = str(e)
        if "SSL" in error_msg or "CERTIFICATE" in error_msg or "certificate" in error_msg:
            # Try with unverified SSL context
            try:
                import ssl
                import urllib3
                urllib3.disable_warnings()
                
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                
                message_obj = Mail(
                    from_email=Config.ALERT_EMAIL_FROM,
                    to_emails=to_email,
                    subject=subject,
                    plain_text_content=message
                )
                
                # Disable SSL verification warnings
                import warnings
                warnings.filterwarnings('ignore', message='Unverified HTTPS request')
                
                sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
                response = sg.send(message_obj)
                
                if response.status_code not in [200, 201, 202]:
                    error_body = ""
                    try:
                        error_body = response.body.decode('utf-8')
                    except:
                        pass
                    raise Exception(f"SendGrid API returned status {response.status_code}: {error_body}")
                
                print("⚠ Email sent with SSL verification disabled (testing mode)")
                return  # Success!
            except Exception as e2:
                raise Exception(f"SendGrid SSL error (retry failed): {str(e2)}")
        elif "401" in error_msg or "Unauthorized" in error_msg:
            raise Exception(f"SendGrid authentication failed. Check your API key. Error: {error_msg}")
        elif "403" in error_msg or "Forbidden" in error_msg:
            raise Exception(f"SendGrid permission denied. Check API key permissions. Error: {error_msg}")
        elif "sender" in error_msg.lower() or "from" in error_msg.lower():
            raise Exception(f"SendGrid sender email issue. Verify '{Config.ALERT_EMAIL_FROM}' in SendGrid dashboard. Error: {error_msg}")
        else:
            raise Exception(f"SendGrid error: {error_msg}")

def send_via_smtp(to_email, subject, plain_message, html_message=None):
    """Send email using SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    msg = MIMEMultipart('alternative')
    msg['From'] = Config.ALERT_EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['Reply-To'] = Config.ALERT_EMAIL_FROM
    
    # Add both plain text and HTML versions
    part1 = MIMEText(plain_message, 'plain')
    msg.attach(part1)
    
    if html_message:
        part2 = MIMEText(html_message, 'html')
        msg.attach(part2)
    
    server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
    server.starttls()
    server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()
