"""
Google Vision API OCR Helper for Translation and Information Extraction
=======================================================================
This module provides functions to use Google Vision API for OCR,
then process the extracted text with GPT for translation and information extraction.
"""

import os
import json
from typing import Dict, Optional

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_google_vision_client():
    """
    Initialize and return a Google Vision API client.
    Uses the service account key file explicitly to ensure the correct project is used.
    
    Returns:
        vision.ImageAnnotatorClient: Vision API client
    """
    if not GOOGLE_VISION_AVAILABLE:
        raise ImportError(
            "google-cloud-vision package is not installed.\n"
            "Install with: pip install google-cloud-vision\n"
            "See GOOGLE_VISION_SETUP.md for setup instructions."
        )
    
    try:
        # Get credentials file path from environment variable
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        
        if credentials_path and os.path.exists(credentials_path):
            # Explicitly load credentials from the service account key file
            # This ensures we use the correct project (gen-lang-client-0996165938)
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = vision.ImageAnnotatorClient(credentials=credentials)
            print(f"[Google Vision] Using credentials from: {credentials_path}")
            print(f"[Google Vision] Project: {credentials.project_id}")
            return client
        else:
            # Fall back to default credentials (not recommended)
            print("[Google Vision] Warning: Using default credentials")
            client = vision.ImageAnnotatorClient()
            return client
    except Exception as e:
        error_msg = str(e)
        if "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
            raise Exception(
                "Google Cloud credentials not found!\n\n"
                "Please set GOOGLE_APPLICATION_CREDENTIALS environment variable:\n"
                "  Windows (PowerShell): $env:GOOGLE_APPLICATION_CREDENTIALS=\"C:\\path\\to\\key.json\"\n"
                "  Windows (CMD): set GOOGLE_APPLICATION_CREDENTIALS=C:\\path\\to\\key.json\n"
                "  Linux/Mac: export GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/key.json\"\n\n"
                "Or download your service account JSON key from Google Cloud Console.\n"
                "See GOOGLE_VISION_SETUP.md for detailed setup instructions."
            )
        raise Exception(f"Failed to initialize Vision API client: {error_msg}")


def extract_text_with_google_vision(image_path: str) -> str:
    """
    Extract text from an image using Google Vision API OCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text as a string
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    client = get_google_vision_client()
    
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")
        
        texts = response.text_annotations
        
        if not texts:
            return ""
        
        # First annotation contains the full text
        return texts[0].description
        
    except Exception as e:
        raise Exception(f"Error extracting text with Google Vision API: {str(e)}")


def translate_and_extract_with_gpt(extracted_text: str, document_type: str = "estimation") -> Dict:
    """
    Use GPT to translate and extract structured information from OCR'd text.
    
    Args:
        extracted_text: Text extracted from image via Google Vision OCR
        document_type: Type of document ("estimation" or "vehicle_info")
        
    Returns:
        Dict with translated text and extracted structured data
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package is not installed. Install with: pip install openai")
    
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not api_key:
        raise Exception("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    if document_type == "estimation":
        prompt = """You are an EXPERT document analyst for vehicle repair estimation documents from Sri Lanka.

The OCR text below was extracted from a TABULAR DOCUMENT with this structure:
- LEFT: Item descriptions (numbered rows)
- PRICE COLUMN: Contains BOTH estimate AND approved prices
  * ESTIMATE = BLACK ink numbers (original garage quote) - may be SCRATCHED/CROSSED OUT
  * APPROVED = RED ink numbers (inspector's corrected/approved amount)
- SECTIONS: Labour, Repair & Straight, Booth Painting, Material/Spare Parts

COLOR RULE: BLACK = Estimate (original), RED = Approved (corrected)

CRITICAL RULES:
===============
1. The OCR text may have numbers scattered - you must match them to the correct row
2. Common Sri Lankan repair amounts: 500, 800, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000, 4200, 5000, 8000, 8500, 10000, 12000, 18500
3. Look for patterns: item name followed by its estimate, then its approved amount
4. "/-" or "/=" suffix marks the end of amounts
5. Negative numbers = deductions or rejections
6. "SH" means spare parts reference
7. "deleted" or "jacked" means item was rejected

MATCHING NUMBERS TO ROWS:
========================
- Each numbered item (1, 2, 3, etc.) should have at most 2 numbers: estimate and approved
- If you see numbers near an item name, the FIRST is likely estimate, SECOND is approved
- If only one number, determine if it's estimate or approved based on context

Return ONLY this JSON format:
{
    "source_language": "English",
    "translated_text": "Company header and notes",
    "document_info": {
        "company_name": "Workshop name",
        "reference_number": "Est NO",
        "document_date": "Date",
        "vehicle_info": "Vehicle details"
    },
    "table_data": [
        {"description": "Item name", "estimate": "Amount or '-'", "approved": "Amount or '✓' or '-'"}
    ],
    "totals": {
        "estimate_total": "Sum of estimates",
        "approved_total": "Sum of approved",
        "grand_total": "Grand total from document",
        "difference": "Difference"
    }
}

VERIFICATION:
- Extract EVERY numbered row
- Copy numbers EXACTLY as they appear in the OCR text
- Don't invent or guess numbers

Extracted text from OCR:
"""
    else:  # vehicle_info
        prompt = """You are a document analysis expert specializing in insurance and vehicle accident reports.

I have extracted text from a vehicle document using OCR. Analyze this text and extract ALL visible information into structured JSON.

This could be an accident intimation form, insurance claim document, vehicle registration, repair estimate, or any vehicle-related document.

Extract the following categories of information:

**Document & Reference Information:**
- Reference Number / Claim Number
- Policy Number
- Document Type

**Accident/Incident Details:**
- Date and Time of Accident
- Location of Accident
- Police Division / Station
- Description of Accident

**Vehicle Information:**
- Registration Number
- Make/Manufacturer
- Model
- Year
- Chassis Number
- Engine Number
- Color
- Vehicle Type

**Driver Information:**
- Name
- License Number
- Contact Number
- Address

**Damage Information:**
- Parts damaged
- Description of damage
- Estimated repair cost

**Additional Details:**
- Insurance company
- Remarks/Notes

Return your response as JSON in this EXACT format:
{
    "summary": "Brief summary of the document",
    "document_info": {
        "reference_number": "...",
        "policy_number": "...",
        "document_type": "..."
    },
    "accident_details": {
        "date": "...",
        "time": "...",
        "location": "...",
        "police_station": "...",
        "description": "..."
    },
    "vehicle_info": {
        "registration_number": "...",
        "make": "...",
        "model": "...",
        "year": "...",
        "chassis_number": "...",
        "engine_number": "...",
        "color": "...",
        "vehicle_type": "..."
    },
    "driver_info": {
        "name": "...",
        "license_number": "...",
        "contact": "...",
        "address": "..."
    },
    "damage_info": {
        "parts_damaged": "...",
        "description": "...",
        "estimated_cost": "..."
    },
    "additional_info": {
        "insurance_company": "...",
        "remarks": "..."
    }
}

IMPORTANT:
- Return ALL sections, even if some fields are null/empty
- Extract ANY visible information from the OCR text
- Return ONLY valid JSON, no other text

Extracted text from OCR:
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n\n" + extracted_text
                }
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        # Sometimes GPT wraps JSON in markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            return {
                "translated_text": result_text if document_type == "estimation" else "",
                "error": "Could not parse GPT response as JSON",
                "raw_response": result_text
            }
            
    except Exception as e:
        raise Exception(f"Error processing text with GPT: {str(e)}")


def process_with_google_vision(filepath: str, document_type: str = "estimation") -> Dict:
    """
    Complete pipeline: Extract text with Google Vision OCR, then translate/extract with GPT.
    
    Args:
        filepath: Path to the image file
        document_type: "estimation" or "vehicle_info"
        
    Returns:
        Dict with translated text and extracted structured data
    """
    try:
        # Step 1: Extract text using Google Vision OCR
        print(f"[Google Vision OCR] Extracting text from: {filepath}")
        extracted_text = extract_text_with_google_vision(filepath)
        
        if not extracted_text:
            return {
                "translated_text": "",
                "source_language": "Unknown",
                "error": "No text could be extracted from the image",
                "table_data": [],
                "document_info": {},
                "totals": {}
            }
        
        print(f"[Google Vision OCR] Extracted {len(extracted_text)} characters")
        
        # Step 2: Translate and extract structured data using GPT
        print(f"[GPT Processing] Translating and extracting structured data...")
        result = translate_and_extract_with_gpt(extracted_text, document_type)
        
        # Add OCR confidence info
        result["ocr_provider"] = "Google Cloud Vision API"
        result["raw_ocr_text"] = extracted_text  # Include raw OCR text for debugging
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] {error_msg}")
        # Re-raise for API/credential errors so the caller can fall back to OpenAI
        if any(err in error_msg.lower() for err in ['billing', 'disabled', 'not been used', 'enable', 'credentials', '403', '401']):
            raise  # Re-raise to allow fallback
        # For other errors, return empty result
        return {
            "translated_text": "",
            "source_language": "Unknown",
            "error": error_msg,
            "table_data": [],
            "document_info": {},
            "totals": {}
        }


