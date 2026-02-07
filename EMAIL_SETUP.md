# Email Setup Guide 📧

To enable email alerts, you need to configure either **SendGrid** (recommended) or **SMTP** (Gmail, etc.).

## Option 1: SendGrid (Recommended - Easiest)

SendGrid offers a free tier with 100 emails/day - perfect for testing!

### Steps:

1. **Sign up for SendGrid** (free):
   - Go to https://sendgrid.com
   - Create a free account
   - Verify your email

2. **Create an API Key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Name it "StockWise" or similar
   - Select "Full Access" or "Mail Send" permissions
   - Copy the API key (you'll only see it once!)

3. **Create `.env` file** in your project root:
   ```bash
   SENDGRID_API_KEY=SG.your_actual_api_key_here
   ALERT_EMAIL_FROM=your-verified-email@yourdomain.com
   ```

4. **Restart your Flask app**

That's it! Emails will now be sent via SendGrid.

---

## Option 2: SMTP (Gmail)

### Steps:

1. **Enable 2-Factor Authentication** on your Gmail account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "StockWise"
   - Copy the 16-character password

3. **Create `.env` file** in your project root:
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-character-app-password
   ALERT_EMAIL_FROM=your-email@gmail.com
   ```

4. **Restart your Flask app**

---

## Quick Setup (Copy-Paste)

Create a `.env` file in your project root with one of these:

### For SendGrid:
```bash
SENDGRID_API_KEY=SG.your_key_here
ALERT_EMAIL_FROM=your@email.com
```

### For Gmail SMTP:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_FROM=your-email@gmail.com
```

---

## Testing

After setting up, upload the sample CSV again. You should see:
- ✓ Email alerts sent successfully (instead of "Email not configured")
- An actual email in your inbox!

---

## Troubleshooting

**SendGrid errors?**
- Make sure you verified your sender email in SendGrid
- Check that the API key is correct (starts with `SG.`)
- Verify you have "Mail Send" permissions

**Gmail SMTP errors?**
- Make sure you're using an App Password, not your regular password
- Check that 2FA is enabled
- Try using `smtp.gmail.com` port `465` with SSL if 587 doesn't work

**Still not working?**
- Check the Flask console for error messages
- Verify your `.env` file is in the project root (same folder as `app.py`)
- Make sure you restarted Flask after creating `.env`
