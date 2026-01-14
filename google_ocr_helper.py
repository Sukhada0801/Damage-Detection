"""
Google Vision API OCR Helper - PURE GOOGLE IMPLEMENTATION
==========================================================
This module uses ONLY Google Cloud services for OCR and translation.
NO GPT/OpenAI is used in this module.

Pipeline:
1. Google Cloud Vision API - OCR (text extraction)
2. Google Cloud Translate API - Translation (Sinhala/Tamil → English)
3. Custom pattern matching - Table data extraction
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple

# Google Cloud Vision
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

# Google Cloud Translate
try:
    from google.cloud import translate_v2 as translate
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False


def get_credentials():
    """
    Get Google Cloud credentials from service account key file.
    
    Returns:
        Tuple of (credentials, credentials_path)
    """
    possible_paths = [
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', ''),
        os.path.join(os.path.dirname(__file__), 'google-vision-key.json'),
        r'C:\Car Damage Detection Project\google-vision-key.json',
    ]
    
    credentials_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            credentials_path = path
            break
    
    if not credentials_path:
        raise Exception(
            "Google Cloud credentials not found!\n\n"
            "Please ensure google-vision-key.json exists in the project directory.\n"
            "Or set GOOGLE_APPLICATION_CREDENTIALS environment variable."
        )
    
    from google.oauth2 import service_account
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    
    return credentials, credentials_path


def get_google_vision_client():
    """
    Initialize and return a Google Vision API client.
    
    Returns:
        vision.ImageAnnotatorClient: Vision API client
    """
    if not GOOGLE_VISION_AVAILABLE:
        raise ImportError(
            "google-cloud-vision package is not installed.\n"
            "Install with: pip install google-cloud-vision"
        )
    
    credentials, credentials_path = get_credentials()
    client = vision.ImageAnnotatorClient(credentials=credentials)
    print(f"[Google Vision] Using credentials from: {credentials_path}")
    print(f"[Google Vision] Project: {credentials.project_id}")
    return client


def get_google_translate_client():
    """
    Initialize and return a Google Translate API client.
    
    Returns:
        translate.Client: Translate API client
    """
    if not GOOGLE_TRANSLATE_AVAILABLE:
        raise ImportError(
            "google-cloud-translate package is not installed.\n"
            "Install with: pip install google-cloud-translate"
        )
    
    credentials, credentials_path = get_credentials()
    
    # Add required scopes for Translate API
    scoped_credentials = credentials.with_scopes([
        'https://www.googleapis.com/auth/cloud-translation',
        'https://www.googleapis.com/auth/cloud-platform'
    ])
    
    # Pass credentials explicitly to ensure the correct project is used
    client = translate.Client(credentials=scoped_credentials)
    print(f"[Google Translate] Initialized with project: {credentials.project_id}")
    return client


def extract_text_with_google_vision(image_path: str) -> Tuple[str, List[Dict]]:
    """
    Extract text from an image using Google Vision API OCR.
    Also returns word-level bounding boxes for layout analysis.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (full_text, word_annotations)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    client = get_google_vision_client()
    
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    
    # Use document_text_detection for better table/form extraction
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"Google Vision API error: {response.error.message}")
    
    # Get full text
    full_text = ""
    if response.full_text_annotation:
        full_text = response.full_text_annotation.text
    elif response.text_annotations:
        full_text = response.text_annotations[0].description
    
    # Get word-level annotations with positions
    word_annotations = []
    if response.text_annotations:
        for annotation in response.text_annotations[1:]:  # Skip first (full text)
            bounds = annotation.bounding_poly.vertices
            if bounds:
                word_annotations.append({
                    'text': annotation.description,
                    'x': bounds[0].x if bounds[0].x else 0,
                    'y': bounds[0].y if bounds[0].y else 0,
                    'width': (bounds[2].x - bounds[0].x) if bounds else 0,
                    'height': (bounds[2].y - bounds[0].y) if bounds else 0
                })
    
    return full_text, word_annotations


def translate_text_with_google(text: str, target_language: str = 'en') -> Tuple[str, str]:
    """
    Translate text using Google Cloud Translate API.
    
    Args:
        text: Text to translate
        target_language: Target language code (default: 'en' for English)
        
    Returns:
        Tuple of (translated_text, detected_source_language)
    """
if not text.strip():
        return "", "unknown"
    
    try:
        client = get_google_translate_client()
        
        # Detect language and translate
        result = client.translate(text, target_language=target_language)
        
        translated_text = result['translatedText']
        source_language = result.get('detectedSourceLanguage', 'unknown')
        
        # Map language codes to names
        language_names = {
            'si': 'Sinhala',
            'ta': 'Tamil',
            'en': 'English',
            'hi': 'Hindi',
            'unknown': 'Unknown'
        }
        
        source_language_name = language_names.get(source_language, source_language)
        
        print(f"[Google Translate] Detected language: {source_language_name}")
        print(f"[Google Translate] Translated {len(text)} chars → {len(translated_text)} chars")
        
        return translated_text, source_language_name
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Google Translate Error] {error_msg}")
        # If translation fails, return original text
        return text, "Unknown (translation failed)"


def extract_numbers_from_text(text: str) -> List[str]:
    """Extract all number-like patterns from text."""
    # Match patterns like: 1800, 1,800, 1800/-, 1800.00, etc.
    patterns = [
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Numbers with commas and decimals
        r'\d+(?:\.\d+)?',  # Simple numbers
    ]
    
    numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        numbers.extend(matches)
    
    # Clean and deduplicate
    cleaned = []
    for n in numbers:
        n = n.replace(',', '')
        if n and n not in cleaned:
            cleaned.append(n)
    
    return cleaned


def parse_estimation_table(text: str, translated_text: str) -> List[Dict]:
    """
    Parse estimation document text to extract table rows.
    Uses pattern matching instead of AI.
    
    Args:
        text: Original OCR text
        translated_text: Translated text (if applicable)
        
    Returns:
        List of table row dictionaries
    """
    table_data = []
    
    # Use translated text for parsing
    working_text = translated_text if translated_text else text
    
    # Split into lines
    lines = working_text.split('\n')
    
    # Common part patterns
    part_patterns = [
        r'(?:Front|Rear|Left|Right|LH|RH|L/H|R/H)\s*(?:Bumper|Buffer|Fender|Door|Panel|Light|Lamp|Mirror|Guard|Grill|Hood|Bonnet)',
        r'(?:Head|Tail|Fog|Day)\s*(?:Light|Lamp)s?',
        r'(?:Side\s*)?Mirror',
        r'Fender(?:\s*Lamp)?',
        r'Buffer(?:\s*Retainer)?',
        r'(?:Number\s*)?Plate(?:\s*Holder)?',
        r'Shell',
        r'Grill',
        r'Paint(?:ing)?',
        r'Polish',
        r'Labour',
        r'Material',
        r'Spare\s*Parts?',
    ]
    
    # Find lines with parts and numbers
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if line contains a part name
        is_part_line = False
        part_name = ""
        
        for pattern in part_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                is_part_line = True
                part_name = match.group(0)
                break
        
        # Also check for numbered items (1., 2., etc.)
        numbered_match = re.match(r'^(\d+)[.\)]\s*(.+)', line)
        if numbered_match:
            is_part_line = True
            part_name = numbered_match.group(2).strip()
        
        if is_part_line:
            # Extract numbers from this line and nearby lines
            numbers = extract_numbers_from_text(line)
            
            # Get additional numbers from the next line if it looks like continuation
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^[\d,.\s/-]+$', next_line):
                    numbers.extend(extract_numbers_from_text(next_line))
            
            # Filter out very small numbers (likely not prices)
            prices = [n for n in numbers if float(n.replace(',', '')) >= 100]
            
            # Assign estimate and approved
            estimate = "-"
            approved = "-"
            
            if len(prices) >= 2:
                estimate = prices[0]
                approved = prices[1]
            elif len(prices) == 1:
                # Single number - could be either
                approved = prices[0]
            
            # Clean part name
            part_name = re.sub(r'^\d+[.\)]\s*', '', part_name)
            part_name = re.sub(r'[\d,.\s/-]+$', '', part_name).strip()
            
            if part_name:
                table_data.append({
                    'description': part_name,
                    'estimate': estimate,
                    'approved': approved
                })
    
    return table_data


def extract_document_info(text: str, translated_text: str) -> Dict:
    """
    Extract document metadata (company name, date, reference, etc.)
    
    Args:
        text: Original OCR text
        translated_text: Translated text
        
    Returns:
        Dictionary with document info
    """
    working_text = translated_text if translated_text else text
    
    info = {
        'company_name': '',
        'reference_number': '',
        'document_date': '',
        'vehicle_info': ''
    }
    
    # Try to find company name (usually first few lines, in caps)
    lines = working_text.split('\n')[:10]
    for line in lines:
        line = line.strip()
        # Company names often have "Motor", "Auto", "Service", "Engineering"
        if any(word in line.upper() for word in ['MOTOR', 'AUTO', 'SERVICE', 'ENGINEERING', 'GARAGE', 'WORKSHOP']):
            info['company_name'] = line
            break
    
    # Find reference/estimate number
    ref_patterns = [
        r'(?:Est\.?\s*No\.?|Ref\.?\s*No\.?|Reference|Estimate\s*#?)[:\s]*([A-Z0-9/-]+)',
        r'(?:No\.?|#)[:\s]*(\d+)',
    ]
    for pattern in ref_patterns:
        match = re.search(pattern, working_text, re.IGNORECASE)
        if match:
            info['reference_number'] = match.group(1)
            break
    
    # Find date
    date_patterns = [
        r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'(\d{4}[/.-]\d{1,2}[/.-]\d{1,2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, working_text)
        if match:
            info['document_date'] = match.group(1)
            break
    
    # Find vehicle info
    vehicle_patterns = [
        r'(?:Reg\.?\s*No\.?|Vehicle\s*No\.?|Registration)[:\s]*([A-Z0-9-]+)',
        r'([A-Z]{2,3}[-\s]?\d{4})',  # Sri Lankan format
    ]
    for pattern in vehicle_patterns:
        match = re.search(pattern, working_text, re.IGNORECASE)
        if match:
            info['vehicle_info'] = match.group(1)
            break
    
    return info


def calculate_totals(table_data: List[Dict]) -> Dict:
    """
    Calculate totals from table data.
    
    Args:
        table_data: List of table row dictionaries
        
    Returns:
        Dictionary with totals
    """
    estimate_total = 0
    approved_total = 0
    
    for row in table_data:
        # Parse estimate
        est = row.get('estimate', '-')
        if est and est != '-' and est != '✓':
            try:
                estimate_total += float(str(est).replace(',', '').replace('/-', '').replace('/=', ''))
            except ValueError:
                pass
        
        # Parse approved
        appr = row.get('approved', '-')
        if appr and appr != '-' and appr != '✓':
            try:
                approved_total += float(str(appr).replace(',', '').replace('/-', '').replace('/=', ''))
            except ValueError:
                pass
    
    return {
        'estimate_total': f"{estimate_total:.2f}" if estimate_total > 0 else "0.00",
        'approved_total': f"{approved_total:.2f}" if approved_total > 0 else "0.00",
        'grand_total': f"{approved_total:.2f}" if approved_total > 0 else f"{estimate_total:.2f}",
        'difference': f"{approved_total - estimate_total:.2f}"
    }


def process_with_google_vision_pure(filepath: str, document_type: str = "estimation") -> Dict:
    """
    Complete pipeline using ONLY Google services (no GPT/OpenAI).
    
    Pipeline:
    1. Google Vision OCR - Extract text
    2. Google Translate - Translate to English
    3. Pattern matching - Extract structured data
    
    Args:
        filepath: Path to the image file
        document_type: "estimation" or "vehicle_info"
        
    Returns:
        Dict with translated text and extracted structured data
    """
    result = {
        'success': True,
        'ocr_provider': 'Google Cloud Vision API (Pure)',
        'translator': 'Google Cloud Translate API',
        'ai_processing': 'None (Pattern Matching)',
        'raw_ocr_text': '',
        'translated_text': '',
        'source_language': 'Unknown',
        'table_data': [],
        'document_info': {},
        'totals': {}
    }
    
    try:
        # Step 1: Extract text using Google Vision OCR
        print(f"[Step 1/3] Google Vision OCR: Extracting text from: {filepath}")
        raw_text, word_annotations = extract_text_with_google_vision(filepath)
        
        if not raw_text:
            result['error'] = "No text could be extracted from the image"
            return result
        
        result['raw_ocr_text'] = raw_text
        print(f"[Step 1/3] Extracted {len(raw_text)} characters, {len(word_annotations)} words")
        
        # Step 2: Translate using Google Translate
        print(f"[Step 2/3] Google Translate: Translating text...")
        translated_text, source_language = translate_text_with_google(raw_text)
        
        result['translated_text'] = translated_text
        result['source_language'] = source_language
        
        # Step 3: Extract structured data using pattern matching
        print(f"[Step 3/3] Pattern Matching: Extracting table data...")
        
        if document_type == "estimation":
            # Parse estimation table
            table_data = parse_estimation_table(raw_text, translated_text)
            result['table_data'] = table_data
            
            # Extract document info
            result['document_info'] = extract_document_info(raw_text, translated_text)
            
            # Calculate totals
            result['totals'] = calculate_totals(table_data)
            
            print(f"[Step 3/3] Extracted {len(table_data)} items from table")
        
        else:  # vehicle_info
            # For vehicle info, extract key fields
            result['document_info'] = extract_document_info(raw_text, translated_text)
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Error] {error_msg}")
        result['success'] = False
        result['error'] = error_msg
        
        # Re-raise for API/credential errors
        if any(err in error_msg.lower() for err in ['billing', 'disabled', 'not been used', 'enable', 'credentials', '403', '401']):
            raise
        
        return result


# Legacy function for backwards compatibility
def process_with_google_vision(filepath_or_bytes, document_type: str = "estimation", is_bytes: bool = False) -> Dict:
    """
    Wrapper for backwards compatibility.
    Now uses pure Google implementation.
    
    Args:
        filepath_or_bytes: Path to image file OR bytes data
        document_type: "estimation" or "vehicle_info"
        is_bytes: If True, first arg is bytes data (not a filepath)
    """
    # Auto-detect if it's bytes
    if isinstance(filepath_or_bytes, bytes):
        is_bytes = True
    
    if is_bytes:
        # Handle bytes input
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(filepath_or_bytes)
            tmp_path = tmp_file.name
        try:
            return process_with_google_vision_pure(tmp_path, document_type)
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    else:
        return process_with_google_vision_pure(filepath_or_bytes, document_type)


# Keep the old GPT-based function available if needed
def translate_and_extract_with_gpt(extracted_text: str, document_type: str = "estimation") -> Dict:
    """
    DEPRECATED: Use GPT to translate and extract structured information.
    Kept for backwards compatibility but not used in pure Google mode.
    """
    try:
        from openai import OpenAI
        
        api_key = os.environ.get('OPENAI_API_KEY', '').strip()
        if not api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        
        prompt = """Analyze this OCR text from a vehicle repair estimation document.
        
Extract and return JSON with:
- translated_text: Brief summary
- table_data: Array of {description, estimate, approved}
- document_info: {company_name, reference_number, date, vehicle_info}
- totals: {estimate_total, approved_total, grand_total}

OCR Text:
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt + extracted_text}],
            max_tokens=4000,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(result_text)
        
    except Exception as e:
        return {"error": str(e), "raw_response": extracted_text}
