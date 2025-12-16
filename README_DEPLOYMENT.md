# Quick Deployment Guide

## 🚀 Fastest Way: Railway (Recommended)

1. **Push to GitHub** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

2. **Deploy on Railway**:
   - Go to https://railway.app
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Add environment variable: `OPENAI_API_KEY` = your key
   - Railway auto-deploys!

3. **Done!** Your app is live at `https://your-app.railway.app`

---

## 📋 Pre-Deployment Checklist

- [ ] Update `requirements.txt` (already done ✅)
- [ ] Set `OPENAI_API_KEY` as environment variable
- [ ] Test locally with `debug=False`
- [ ] Ensure all files are committed to Git
- [ ] Review `DEPLOYMENT.md` for detailed instructions

---

## 🔑 Environment Variables Needed

- `OPENAI_API_KEY` - Your OpenAI API key (REQUIRED)
- `PORT` - Automatically set by hosting platform
- `DEBUG_MODE` - Set to 'true' only for development

---

## 📚 Full Documentation

See `DEPLOYMENT.md` for:
- Detailed steps for 6+ hosting platforms
- Docker deployment
- Security best practices
- Troubleshooting guide

