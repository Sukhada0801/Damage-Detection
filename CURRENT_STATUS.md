# Current OCR Status

## ❌ Google OCR is NOT Currently Active

**Current Configuration:**
- `OCR_PROVIDER`: Not set → **Defaults to 'openai'**
- `GOOGLE_APPLICATION_CREDENTIALS`: Not set

**What's Being Used:**
- ✅ **Translation**: OpenAI GPT-4 Vision
- ✅ **Vehicle Info Extraction**: OpenAI GPT-4 Vision

---

## ✅ To Enable Google OCR

### Option 1: Use the PowerShell Script (Easiest)
```powershell
# Run this script before starting your Flask server
.\enable_google_ocr.ps1
```

Then start your server:
```powershell
.venv\Scripts\activate
python frontend_damage_detection
```

### Option 2: Set Environment Variables Manually

**In PowerShell (before starting server):**
```powershell
$env:OCR_PROVIDER = "google"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Car Damage Detection Project\google-vision-key.json"
```

**Then start your server:**
```powershell
.venv\Scripts\activate
python frontend_damage_detection
```

### Option 3: Make Permanent (Windows System Environment Variables)

1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to "Advanced" tab → "Environment Variables"
3. Under "User variables" or "System variables", click "New"
4. Add:
   - Variable: `OCR_PROVIDER`
   - Value: `google`
5. Add:
   - Variable: `GOOGLE_APPLICATION_CREDENTIALS`
   - Value: `C:\Car Damage Detection Project\google-vision-key.json`
6. Click OK and restart your terminal/IDE

---

## 📋 Requirements Checklist

- [x] Google Vision API key file downloaded (`google-vision-key.json`)
- [ ] Key file placed in project root: `C:\Car Damage Detection Project\google-vision-key.json`
- [ ] `OCR_PROVIDER` environment variable set to `"google"`
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` environment variable set to key file path
- [ ] Google Cloud Vision API enabled in your Google Cloud project
- [ ] Google Cloud Translate API enabled in your Google Cloud project

---

## 🔍 How to Verify It's Working

1. Set the environment variables (see above)
2. Start your Flask server
3. Check the server startup logs - you should see Google Vision initialization
4. Upload a document for translation or vehicle info extraction
5. Check the response - it should say `"provider": "Google Cloud Vision"` instead of `"OpenAI"`

---

## 🔄 Switching Between Providers

To switch back to OpenAI:
```powershell
$env:OCR_PROVIDER = "openai"
# Or just unset it (it defaults to 'openai')
$env:OCR_PROVIDER = $null
```

To use Google:
```powershell
$env:OCR_PROVIDER = "google"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Car Damage Detection Project\google-vision-key.json"
```


