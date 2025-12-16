# Deployment Guide for Car Damage Detection System

This guide covers multiple deployment options for your Flask-based car damage detection application.

## Prerequisites

1. **OpenAI API Key**: You'll need to set this as an environment variable
2. **Python 3.8+**: Required for the application
3. **Git**: For version control and deployment

---

## Option 1: Railway (Recommended - Easiest)

Railway is great for Python apps with file uploads.

### Steps:

1. **Sign up**: Go to https://railway.app and sign up with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository

3. **Configure Environment Variables**:
   - Go to your project settings
   - Add environment variable:
     - `OPENAI_API_KEY` = your OpenAI API key

4. **Deploy**:
   - Railway auto-detects Python apps
   - It will install dependencies from `requirements.txt`
   - Your app will be live at `https://your-app.railway.app`

5. **Configure Port** (if needed):
   - Railway uses `PORT` environment variable
   - Update `frontend_damage_detection` to use: `port = int(os.environ.get('PORT', 5000))`

**Cost**: Free tier available, then pay-as-you-go

---

## Option 2: Render

Render is another excellent option with free tier.

### Steps:

1. **Sign up**: Go to https://render.com

2. **Create New Web Service**:
   - Connect your GitHub repository
   - Select "Web Service"

3. **Configure**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python frontend_damage_detection`
   - **Environment**: Python 3

4. **Add Environment Variables**:
   - `OPENAI_API_KEY` = your OpenAI API key

5. **Deploy**:
   - Render will automatically deploy
   - Your app will be at `https://your-app.onrender.com`

**Cost**: Free tier (spins down after inactivity), paid plans available

---

## Option 3: Heroku

Heroku is a classic choice (note: free tier discontinued, but still popular).

### Steps:

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Login**:
   ```bash
   heroku login
   ```

3. **Create App**:
   ```bash
   heroku create your-app-name
   ```

4. **Set Environment Variables**:
   ```bash
   heroku config:set OPENAI_API_KEY=your-api-key-here
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

6. **Open App**:
   ```bash
   heroku open
   ```

**Note**: Update `frontend_damage_detection` to use Heroku's PORT:
```python
port = int(os.environ.get('PORT', 5000))
app.run(host="0.0.0.0", port=port, debug=False)
```

**Cost**: Paid plans starting at $7/month

---

## Option 4: PythonAnywhere

Good for beginners, Python-focused hosting.

### Steps:

1. **Sign up**: https://www.pythonanywhere.com

2. **Upload Files**:
   - Use the Files tab to upload your project
   - Or use Git: `git clone https://github.com/your-repo.git`

3. **Create Web App**:
   - Go to Web tab
   - Click "Add a new web app"
   - Choose Flask, Python 3.11

4. **Configure**:
   - Set source code directory
   - Set WSGI file to point to your Flask app

5. **Set Environment Variables**:
   - In Web app settings, add `OPENAI_API_KEY`

6. **Reload**:
   - Click the green "Reload" button

**Cost**: Free tier available, paid plans from $5/month

---

## Option 5: DigitalOcean App Platform

Modern platform with good performance.

### Steps:

1. **Sign up**: https://www.digitalocean.com

2. **Create App**:
   - Connect GitHub repository
   - Select Python as runtime

3. **Configure**:
   - Build command: `pip install -r requirements.txt`
   - Run command: `python frontend_damage_detection`
   - Add environment variable: `OPENAI_API_KEY`

4. **Deploy**:
   - Automatic deployment on git push

**Cost**: Starting at $5/month

---

## Option 6: Docker + Any Cloud Provider

Deploy using Docker for maximum portability.

### Steps:

1. **Build Docker Image**:
   ```bash
   docker build -t car-damage-detection .
   ```

2. **Run Locally** (test):
   ```bash
   docker run -p 5000:5000 -e OPENAI_API_KEY=your-key car-damage-detection
   ```

3. **Deploy to Cloud**:
   - **AWS**: Use ECS or Elastic Beanstalk
   - **Google Cloud**: Use Cloud Run or Compute Engine
   - **Azure**: Use Container Instances or App Service
   - **DigitalOcean**: Use App Platform with Docker

---

## Important Configuration Updates

### 1. Update Port Configuration

For cloud platforms, update `frontend_damage_detection`:

```python
if __name__ == '__main__':
    # ... existing code ...
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # debug=False for production
```

### 2. Environment Variables

Always set these in your hosting platform:
- `OPENAI_API_KEY` - Your OpenAI API key (REQUIRED)

### 3. File Storage

For production, consider:
- **Cloud Storage**: AWS S3, Google Cloud Storage, or Azure Blob Storage
- **Database**: For storing feedback logs and annotations
- **CDN**: For serving images faster

### 4. Security Checklist

Before going live:
- [ ] Set `debug=False` in production
- [ ] Use HTTPS (most platforms provide this)
- [ ] Add rate limiting
- [ ] Consider adding authentication
- [ ] Set up proper error logging
- [ ] Configure CORS properly if needed

---

## Quick Start (Railway - Recommended)

1. Push your code to GitHub
2. Go to https://railway.app
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Add environment variable: `OPENAI_API_KEY`
6. Deploy!

Your app will be live in minutes! 🚀

---

## Troubleshooting

### Common Issues:

1. **Port Error**: Update code to use `os.environ.get('PORT', 5000)`
2. **OpenCV Issues**: Some platforms need additional system packages (see Dockerfile)
3. **File Upload Limits**: Check platform limits (usually 100MB+ is fine)
4. **Timeout**: Some platforms have request timeouts - consider async processing for large images

---

## Need Help?

- Check platform-specific documentation
- Review error logs in your hosting platform's dashboard
- Ensure all dependencies are in `requirements.txt`

