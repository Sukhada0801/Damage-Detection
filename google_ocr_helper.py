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
        prompt = """# ROLE
You are an **EXPERT document analyst** specializing in **Sri Lankan vehicle repair estimation and insurance approval documents**.

These documents contain **garage estimates** and **insurance inspector approvals**, often handwritten, corrected, and partially overwritten.

---

## DOCUMENT CHARACTERISTICS
The OCR text below was extracted from a **TABULAR DOCUMENT**. Visual layout may be imperfect due to OCR, but the logical structure is:

- **LEFT COLUMN**: Line item descriptions (repair parts, labour items)
- **PRICE / ESTIMATE COLUMN**:
  - Contains **both Estimated and Approved values**
  - Values may appear **left or right of each other**
  - Values may be **scratched, crossed, ticked, or overwritten**
- **SECTIONS MAY INCLUDE**:
  - Labour
  - Repair & Straight
  - Booth Painting
  - Material / Spare Parts

---

## LANGUAGE RULES
- Item descriptions may be in **Sinhala or English**
- Column headers like **"Price", "Estimate", "Estimated Amount"** may appear in **Sinhala or English**
- Translate **all extracted content into English**

---

## COLUMN SEMANTIC HEURISTIC (IMPORTANT)
- Numeric values appearing **directly below or nearest to column headers** such as  
  **"Price", "Estimate", "Estimated Amount"** (English or Sinhala)  
  should be treated as the **ORIGINAL GARAGE ESTIMATE by default**.
- These estimate values are typically written in **BLACK or BLUE ink**.
- If a **RED ink value** appears near the same row, it usually represents the  
  **INSPECTOR-APPROVED amount overriding the estimate**.
- This is a **heuristic, not an absolute rule**. Always validate using:
  - Color semantics
  - Scratches / crossings
  - Tick marks
  - Relative value comparison

---

## COLOR & SEMANTIC RULES
- **BLACK / BLUE ink → ESTIMATED amount**
  - Original garage quotation
  - May be **scratched or crossed out** if reduced
- **RED ink → APPROVED amount**
  - Inspector-approved value
- **Tick mark (✓)** → Inspector accepted the estimate as-is
- **Scratched estimate** → Approved amount is **lower than estimate**
- Keywords like **"deleted", "jacked", "cut", "rejected"** → Item not approved

---

## NUMERIC INTERPRETATION RULES
1. Each numbered row may contain:
   - **Two numbers** → Estimate and Approved
   - **One number** → Determine type using context
2. **Do NOT assume numeric order** (estimate may appear before or after approved)
3. Amounts may end with `/=`, `/-`, `Rs`, or no suffix
4. **Negative values** indicate deductions
5. Common Sri Lankan repair amounts include (not exhaustive):  
   `500, 800, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000, 4200, 5000, 8000, 8500, 10000, 12000, 18500`
6. `"SH"` refers to **Spare Parts**

---

## ROW MATCHING RULES
- Match numeric values to the **nearest logical item description**
- Prefer values located **under or near "Price / Estimate" columns**
- If two values exist:
  - The **higher value** is usually the **estimate**
  - The **lower value** (often red) is the **approved**
- If only one value exists:
  - If ticked → approved = estimate
  - Otherwise → estimate only

---

## CRITICAL CONSTRAINTS
- ❌ Do NOT invent numbers
- ❌ Do NOT guess missing values
- ✅ Copy numeric values **exactly as they appear**
- ✅ Extract **EVERY numbered row**, even if rejected

---

## OUTPUT FORMAT (STRICT)
Return **ONLY valid JSON** in the following structure:

{
  "source_language": "Sinhala / English / Mixed",
  "translated_text": "English translation of company header and handwritten notes",
  "document_info": {
    "company_name": "Workshop name",
    "reference_number": "Estimate / Quotation number",
    "document_date": "Date",
    "vehicle_info": "Vehicle details if present"
  },
  "table_data": [
    {
      "description": "Translated item name",
      "estimate": "Numeric amount or '-'",
      "approved": "Numeric amount or '✓' or '-'"
    }
  ],
  "totals": {
    "estimate_total": "As written or '-'",
    "approved_total": "As written or '-'",
    "grand_total": "As written or '-'",
    "difference": "Approved minus estimate"
  }
}

---

## FINAL VERIFICATION

Before responding:
- Ensure all numbered rows were processed
- Ensure Sinhala text is translated
- Ensure reduced / rejected items are accurately reflected
- Ensure no values were invented or inferred

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


