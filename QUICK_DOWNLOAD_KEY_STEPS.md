# Quick Steps to Download Google Cloud JSON Key

## ⚠️ Important: You Cannot Manually Create This File

The JSON key file **must be downloaded** from Google Cloud Console. It contains encrypted credentials that only Google can generate.

---

## 📥 Download Steps (2 minutes)

### 1. Open Service Accounts Page
- Go to: **https://console.cloud.google.com/iam-admin/serviceaccounts**
- Or: Menu (☰) → **IAM & Admin** → **Service Accounts**

### 2. Click on Your Service Account
- Find the service account you created
- Click on its **name/email** (not the checkbox)

### 3. Go to Keys Tab
- At the top, click the **KEYS** tab
- You should see a list (might be empty if no keys yet)

### 4. Create New Key
- Click **+ ADD KEY** button
- Select **Create new key**
- Choose **JSON** format
- Click **CREATE**

### 5. File Downloads Automatically
- Browser downloads a file like: `your-project-name-abc123.json`
- This is your service account key!

### 6. Move and Rename
- **Rename** the downloaded file to: `google-vision-key.json`
- **Move** it to: `C:\Car Damage Detection Project\`

---

## ✅ What the File Should Look Like

When you open `google-vision-key.json`, it should start with:

```json
{
  "type": "service_account",
  "project_id": "your-project-name",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "...@...iam.gserviceaccount.com",
  ...
}
```

**If your file doesn't have `"type": "service_account"` at the top, it's not the right file!**

---

## 🔄 After Downloading

1. Place `google-vision-key.json` in your project root
2. Set environment variable (already done!):
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\Car Damage Detection Project\google-vision-key.json"
   ```
3. Restart your Flask server
4. Test with a document upload!

---

## 🆘 If You Can't Find the Keys Tab

- Make sure you **clicked on the service account name** (not just selected it)
- The service account details page should open
- The **KEYS** tab is at the top of that page

---

**Note:** Delete the file you created manually - it won't work. Only the downloaded JSON key from Google will work!



