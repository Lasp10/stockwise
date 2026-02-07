# Deployment Guide - StockWise

## Deploy to Render

### Prerequisites
- GitHub account
- Render account (free tier available)
- MongoDB Atlas account (free tier available)
- SendGrid account (free tier: 100 emails/day)

### Step 1: Push to GitHub

1. **Initialize Git** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create GitHub repository**:
   - Go to https://github.com/new
   - Create a new repository (e.g., `stockwise`)
   - Don't initialize with README

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/stockwise.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Set Up MongoDB Atlas

1. **Create MongoDB Atlas account**:
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free tier

2. **Create a cluster**:
   - Choose free tier (M0)
   - Select region closest to you
   - Create cluster

3. **Get connection string**:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database password

### Step 3: Set Up SendGrid

1. **Create SendGrid account**:
   - Go to https://sendgrid.com
   - Sign up for free account

2. **Create API Key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Name it "StockWise"
   - Select "Full Access" or "Mail Send" permissions
   - Copy the API key (starts with `SG.`)

3. **Verify Sender Email**:
   - Go to Settings → Sender Authentication
   - Verify a Single Sender
   - Enter your email address
   - Verify via email

### Step 4: Deploy on Render

1. **Create New Web Service**:
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**:
   - **Name**: `stockwise` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free (or paid if you need more resources)

3. **Add Environment Variables**:
   Click "Environment" tab and add:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DB_NAME=stockwise
   SENDGRID_API_KEY=SG.your_api_key_here
   ALERT_EMAIL_FROM=your-verified-email@yourdomain.com
   SECRET_KEY=generate-a-random-secret-key-here
   ```
   
   **Generate SECRET_KEY**:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

4. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Wait for deployment to complete (2-5 minutes)

5. **Get Your URL**:
   - Once deployed, you'll get a URL like: `https://stockwise.onrender.com`
   - Update port in `app.py` if needed (Render uses PORT env var)

### Step 5: Update App for Render

Render provides a `PORT` environment variable. Update `app.py`:

```python
import os
port = int(os.environ.get('PORT', 5001))
app.run(debug=False, host='0.0.0.0', port=port)
```

## Post-Deployment

### Test Your Deployment

1. **Visit your Render URL**
2. **Upload a sample CSV**
3. **Check email alerts**

### Monitor

- **Render Dashboard**: Check logs and metrics
- **MongoDB Atlas**: Monitor database usage
- **SendGrid**: Check email delivery stats

## Troubleshooting

### App Won't Start
- Check Render logs for errors
- Verify all environment variables are set
- Check MongoDB connection string

### Emails Not Sending
- Verify SendGrid API key in environment variables
- Check SendGrid sender verification
- Check Render logs for email errors

### MongoDB Connection Failed
- Verify connection string format
- Check MongoDB Atlas IP whitelist (add 0.0.0.0/0 for Render)
- Verify database user credentials

## Security Checklist

- ✅ Never commit `.env` or `keys.env` files
- ✅ Use environment variables for all secrets
- ✅ Use strong SECRET_KEY
- ✅ Keep dependencies updated
- ✅ Use HTTPS (Render provides automatically)

## Cost Estimate

**Free Tier:**
- Render: Free (with limitations)
- MongoDB Atlas: Free (512MB storage)
- SendGrid: Free (100 emails/day)

**Total: $0/month** for small-scale use!

## Scaling

When you outgrow free tier:
- **Render**: $7/month for better performance
- **MongoDB Atlas**: $9/month for more storage
- **SendGrid**: $15/month for 40k emails

---

**Need Help?** Check Render docs: https://render.com/docs
