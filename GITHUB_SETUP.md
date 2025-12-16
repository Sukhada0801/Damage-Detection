# GitHub Repository Setup Guide

## Step-by-Step Instructions to Connect Your Project to GitHub

### Prerequisites
- Git installed on your computer
- GitHub account created
- Your project files ready

---

## Method 1: If GitHub Repository Already Exists

If you've already created the "Damage-Detection" repository on GitHub:

### Step 1: Check Current Git Status
```bash
cd "C:\Car Damage Detection Project"
git status
```

### Step 2: Add All Files
```bash
git add .
```

### Step 3: Commit Your Changes
```bash
git commit -m "Initial commit - Car Damage Detection System"
```

### Step 4: Add GitHub Remote
```bash
git remote add origin https://github.com/YOUR_USERNAME/Damage-Detection.git
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 5: Push to GitHub
```bash
git push -u origin main
```

If your default branch is `master` instead of `main`:
```bash
git push -u origin master
```

---

## Method 2: Create New Repository on GitHub First

### Step 1: Create Repository on GitHub
1. Go to https://github.com
2. Click the **"+"** icon in the top right → **"New repository"**
3. Repository name: `Damage-Detection`
4. Description: "Car Damage Detection System using OpenAI Vision API"
5. Choose **Public** or **Private**
6. **DO NOT** initialize with README, .gitignore, or license (you already have these)
7. Click **"Create repository"**

### Step 2: Initialize Git (if not already done)
```bash
cd "C:\Car Damage Detection Project"
git init
```

### Step 3: Add All Files
```bash
git add .
```

### Step 4: Create Initial Commit
```bash
git commit -m "Initial commit - Car Damage Detection System"
```

### Step 5: Rename Branch to Main (if needed)
```bash
git branch -M main
```

### Step 6: Add GitHub Remote
```bash
git remote add origin https://github.com/YOUR_USERNAME/Damage-Detection.git
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 7: Push to GitHub
```bash
git push -u origin main
```

---

## Method 3: Using GitHub CLI (gh)

If you have GitHub CLI installed:

```bash
cd "C:\Car Damage Detection Project"
gh repo create Damage-Detection --public --source=. --remote=origin --push
```

---

## Troubleshooting

### Issue: "remote origin already exists"
**Solution:**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/Damage-Detection.git
```

### Issue: "Authentication failed"
**Solution:**
- Use a Personal Access Token instead of password:
  1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. Generate new token with `repo` permissions
  3. Use the token as your password when pushing

### Issue: "Permission denied"
**Solution:**
- Make sure you're using the correct repository URL
- Check that the repository exists and you have access
- Verify your GitHub username is correct

### Issue: "Large file" error
**Solution:**
- The `dummy_indian_vehicle_repair_estimates.json` file (511KB) should be fine
- If you get errors about large files, check `.gitignore` is working properly

---

## Verify Connection

After pushing, verify it worked:

```bash
git remote -v
```

You should see:
```
origin  https://github.com/YOUR_USERNAME/Damage-Detection.git (fetch)
origin  https://github.com/YOUR_USERNAME/Damage-Detection.git (push)
```

Visit your repository: `https://github.com/YOUR_USERNAME/Damage-Detection`

---

## Future Updates

After making changes, push updates with:

```bash
git add .
git commit -m "Description of changes"
git push
```

---

## Quick Command Reference

```bash
# Check status
git status

# Add all files
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push

# Pull latest changes
git pull

# View remote repositories
git remote -v
```

