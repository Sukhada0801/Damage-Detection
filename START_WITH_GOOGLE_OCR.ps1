# Start Flask Server with Google OCR Enabled
# Run this script to start your server with Google OCR

Write-Host "=== Starting Flask Server with Google OCR ===" -ForegroundColor Cyan

# Set environment variables
$env:OCR_PROVIDER = "google"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Car Damage Detection Project\google-vision-key.json"

# Verify key file exists
$keyPath = "C:\Car Damage Detection Project\google-vision-key.json"
if (-not (Test-Path $keyPath)) {
    Write-Host "❌ ERROR: Key file not found at: $keyPath" -ForegroundColor Red
    Write-Host "Please download google-vision-key.json from Google Cloud Console" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment variables set:" -ForegroundColor Green
Write-Host "   OCR_PROVIDER = $env:OCR_PROVIDER" -ForegroundColor Yellow
Write-Host "   GOOGLE_APPLICATION_CREDENTIALS = $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment and start server
Write-Host "🚀 Starting Flask server..." -ForegroundColor Cyan
Write-Host ""

cd "C:\Car Damage Detection Project"
.venv\Scripts\activate
python frontend_damage_detection


