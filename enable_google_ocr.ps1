# PowerShell script to enable Google OCR
# Run this script before starting your Flask server

Write-Host "=== Enabling Google OCR ===" -ForegroundColor Cyan

# Get the project root directory
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$keyFilePath = Join-Path $projectRoot "google-vision-key.json"

# Check if key file exists
if (Test-Path $keyFilePath) {
    Write-Host "✅ Found Google Vision key file: $keyFilePath" -ForegroundColor Green
    
    # Set environment variables
    $env:OCR_PROVIDER = "google"
    $env:GOOGLE_APPLICATION_CREDENTIALS = $keyFilePath
    
    Write-Host ""
    Write-Host "✅ Environment variables set:" -ForegroundColor Green
    Write-Host "   OCR_PROVIDER = google" -ForegroundColor Yellow
    Write-Host "   GOOGLE_APPLICATION_CREDENTIALS = $keyFilePath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "⚠️  These settings will only last for this PowerShell session." -ForegroundColor Yellow
    Write-Host "⚠️  To make them permanent, add them to your system environment variables." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🚀 You can now start your Flask server. Google OCR will be used for:" -ForegroundColor Cyan
    Write-Host "   - Document Translation" -ForegroundColor White
    Write-Host "   - Vehicle Information Extraction" -ForegroundColor White
} else {
    Write-Host "❌ ERROR: Key file not found at: $keyFilePath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please make sure google-vision-key.json is in the project root directory." -ForegroundColor Yellow
    Write-Host "Download it from: https://console.cloud.google.com/iam-admin/serviceaccounts" -ForegroundColor Yellow
}






