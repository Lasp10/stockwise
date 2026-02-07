# GitHub Setup & Deployment Checklist

## Pre-Push Checklist ✅

### 1. Security - Keys Protected
- ✅ `.env` is in `.gitignore`
- ✅ `keys.env` is in `.gitignore`
- ✅ `.env.example` created (no real keys)
- ✅ Removed `keys.env` loading from `config.py`
- ✅ No hardcoded API keys in code

### 2. Files Cleaned Up
- ✅ Removed `setup_email.sh`
- ✅ Removed duplicate documentation files
- ✅ Kept only essential docs: README.md, DEPLOYMENT.md, EMAIL_SETUP.md, IMPROVEMENTS.md

### 3. Production Ready
- ✅ Port configuration for Render (uses PORT env var)
- ✅ Debug mode disabled by default (uses FLASK_DEBUG env var)
- ✅ Error handling in place
- ✅ MongoDB fallback if not available

## Git Setup Steps

### 1. Initialize Git Repository

```bash
cd "/Users/_an.kith/Desktop/My_Apps/StockWise!"
git init
```

### 2. Verify .gitignore

Make sure these are ignored:
```bash
cat .gitignore
# Should include: .env, keys.env, *.env, uploads/, etc.
```

### 3. Add Files

```bash
git add .
git status  # Verify keys.env is NOT listed
```

### 4. Initial Commit

```bash
git commit -m "Initial commit: StockWise MVP - Production ready"
```

### 5. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `stockwise` (or your choice)
3. Description: "MicroSaaS tool for cafe inventory forecasting"
4. **Public** or **Private** (your choice)
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### 6. Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/stockwise.git
git branch -M main
git push -u origin main
```

### 7. Verify Push

- Go to your GitHub repo
- Check that `keys.env` is **NOT** visible
- Check that `.env` is **NOT** visible
- Verify all code files are there

## Deploy to Render

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

**Quick steps:**
1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo
4. Use settings from `render.yaml` (or configure manually)
5. Add environment variables:
   - `MONGODB_URI`
   - `SENDGRID_API_KEY`
   - `ALERT_EMAIL_FROM`
   - `SECRET_KEY` (generate random)
6. Deploy!

## Environment Variables for Render

Add these in Render dashboard → Environment:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=stockwise
SENDGRID_API_KEY=SG.your_key_here
ALERT_EMAIL_FROM=your-verified-email@yourdomain.com
SECRET_KEY=generate-random-key-here
PORT=5001
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

## Post-Deployment

1. ✅ Test CSV upload
2. ✅ Test ingredient mapping UI
3. ✅ Test email alerts
4. ✅ Verify MongoDB connection
5. ✅ Check Render logs for errors

## Security Reminders

⚠️ **NEVER commit:**
- `.env` files
- `keys.env` files
- Any file with API keys or passwords
- `__pycache__/` directories

✅ **Always commit:**
- `.env.example` (template only)
- `.gitignore` (protects secrets)
- Source code
- Documentation

---

**Ready to deploy!** 🚀
