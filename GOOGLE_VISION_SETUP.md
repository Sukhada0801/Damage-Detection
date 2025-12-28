# Google Cloud Vision API Integration Guide

This guide will help you integrate Google Cloud Vision API into your Vehicle Damage Detection project.

## Why Use Google Vision API?

Google Vision API offers:
- **Object Localization** - Detect objects and their locations in images
- **Text Detection (OCR)** - Extract text from images and documents
- **Image Labeling** - Automatically identify objects, scenes, and activities
- **Face Detection** - Detect faces and facial features
- **Image Properties** - Detect dominant colors, image quality
- **Safe Search Detection** - Detect inappropriate content

For your use case, it's particularly useful for:
1. **Document OCR** - Extract text from vehicle documents (registration, insurance papers)
2. **Object Detection** - Detect vehicle parts and components
3. **Text Extraction** - Better accuracy for extracting vehicle details from forms

---

## Step 1: Setup Google Cloud Project

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown → **New Project**
3. Enter project name (e.g., "vehicle-damage-detection")
4. Click **Create**

### 1.2 Enable Vision API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Cloud Vision API"
3. Click on **Cloud Vision API**
4. Click **Enable**

### 1.3 Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Fill in details:
   - **Name**: `vision-api-service`
   - **Description**: Service account for Vision API
4. Click **Create and Continue**
5. Grant role: **Cloud Vision API User**
6. Click **Done**

### 1.4 Create and Download JSON Key

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create** - This downloads a JSON key file
6. **IMPORTANT**: Save this file securely (e.g., `google-vision-key.json`)

---

## Step 2: Install Required Packages

Add Google Cloud Vision library to your requirements:

```bash
pip install google-cloud-vision
```

Or add to `requirements.txt`:
```
google-cloud-vision>=3.0.0
```

---

## Step 3: Setup Authentication

### Option A: Service Account Key File (Recommended for Development)

1. Save your downloaded JSON key file to your project directory (e.g., `google-vision-key.json`)
2. **IMPORTANT**: Add `google-vision-key.json` to `.gitignore` to avoid committing credentials
3. Set environment variable:

   **Windows (PowerShell):**
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\Car Damage Detection Project\google-vision-key.json"
   ```

   **Windows (CMD):**
   ```cmd
   set GOOGLE_APPLICATION_CREDENTIALS=C:\Car Damage Detection Project\google-vision-key.json
   ```

   **Linux/Mac:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google-vision-key.json"
   ```

### Option B: Application Default Credentials (Recommended for Production)

For production, use Application Default Credentials:
```bash
gcloud auth application-default login
```

---

## Step 4: Pricing Information

Google Cloud Vision API Pricing (as of 2024):
- **Text Detection**: $1.50 per 1,000 images
- **Label Detection**: $1.50 per 1,000 images
- **Object Localization**: $1.50 per 1,000 images
- **Face Detection**: $1.50 per 1,000 images
- **First 1,000 units/month**: FREE

Check current pricing: https://cloud.google.com/vision/pricing

---

## Step 5: Basic Usage Examples

See `google_vision_integration.py` for implementation examples.

### Text Detection (OCR)
```python
from google.cloud import vision

def extract_text_from_image(image_path):
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    
    if response.error.message:
        raise Exception(response.error.message)
    
    texts = response.text_annotations
    if texts:
        return texts[0].description  # Full text
    return ""
```

### Object Detection
```python
def detect_objects(image_path):
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.object_localization(image=image)
    
    objects = response.localized_object_annotations
    return objects
```

### Label Detection
```python
def detect_labels(image_path):
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.label_detection(image=image)
    
    labels = response.label_annotations
    return labels
```

---

## Step 6: Integration with Your Project

You can use Google Vision API for:

1. **Vehicle Document OCR** - Extract text from registration/insurance documents
2. **Text Extraction** - Better accuracy for extracting vehicle details from forms
3. **Object Detection** - Detect vehicle parts (bumpers, doors, windows, etc.)

You can either:
- **Replace** OpenAI for document text extraction (better OCR accuracy)
- **Use alongside** OpenAI (use Google for OCR, OpenAI for damage analysis)
- **Hybrid approach** - Use Google Vision for text extraction, OpenAI GPT-4 Vision for damage detection

---

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `google-vision-key.json` to `.gitignore`
   - Use environment variables in production

2. **Restrict API Access**
   - Use least privilege principle
   - Only grant necessary roles

3. **Rotate Keys Regularly**
   - Regenerate service account keys periodically

4. **Monitor Usage**
   - Set up billing alerts in Google Cloud Console
   - Monitor API usage and costs

---

## Troubleshooting

### Error: "Could not automatically determine credentials"
- Make sure `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly
- Verify the JSON key file path is correct
- Check that the service account has Cloud Vision API enabled

### Error: "Permission denied"
- Verify the service account has "Cloud Vision API User" role
- Check that Vision API is enabled for your project

### Rate Limits
- Default quota: 1,800 requests per minute per project
- For higher quotas, request increase in Google Cloud Console

---

## Next Steps

1. Complete the setup steps above
2. Review `google_vision_integration.py` for implementation
3. Test with sample images
4. Integrate into your Flask application
5. Update your API endpoints to use Google Vision for text extraction



