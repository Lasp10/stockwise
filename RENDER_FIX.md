# Render Python Version Fix

## Problem
Render is using Python 3.13.4, which is incompatible with pandas. We need Python 3.11.9.

## Solution

### Option 1: Manual Configuration in Render Dashboard (RECOMMENDED)

1. **Go to your Render service**: https://dashboard.render.com
2. **Click on your `stockwise` service**
3. **Go to Settings tab**
4. **Find "Python Version" or "Environment" section**
5. **Manually set**: `3.11.9` or `3.11`
6. **Save changes**
7. **Redeploy** (or it will auto-redeploy)

### Option 2: Use Build Command to Force Python Version

Update your Render service build command to:
```bash
pip install --upgrade pip && python3.11 -m pip install -r requirements.txt
```

### Option 3: Create a Build Script

Create `build.sh`:
```bash
#!/bin/bash
python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt
```

Then set build command to: `bash build.sh`

## Verify Python Version

After deployment, check logs to confirm Python version:
- Should show: `Python 3.11.x`
- Should NOT show: `Python 3.13.x`

## If Still Failing

1. **Delete and recreate the service** in Render
2. **During creation**, explicitly select Python 3.11
3. **Don't use auto-detection** - manually set everything

---

**Current Status**: Files updated, but Render dashboard needs manual Python version setting.
