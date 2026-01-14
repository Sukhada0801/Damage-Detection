"""
Google Cloud Vision API Integration
===================================
Functions to integrate Google Vision API for text extraction and object detection
in the Vehicle Damage Detection project.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path

try:
    from google.cloud import vision
    from google.cloud.vision_v1 import types
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Warning: google-cloud-vision not installed. Install with: pip install google-cloud-vision")


def get_vision_client():
    """
    Initialize and return a Google Vision API client.
    
    Returns:
        vision.ImageAnnotatorClient: Vision API client
        
    Raises:
        Exception: If credentials are not properly configured
    """
    if not GOOGLE_VISION_AVAILABLE:
        raise ImportError("google-cloud-vision package is not installed. Install with: pip install google-cloud-vision")
    
    try:
        client = vision.ImageAnnotatorClient()
        return client
    except Exception as e:
        error_msg = str(e)
        if "credentials" in error_msg.lower():
            raise Exception(
                "Google Cloud credentials not found!\n"
                "Please set GOOGLE_APPLICATION_CREDENTIALS environment variable:\n"
                "  Windows (PowerShell): $env:GOOGLE_APPLICATION_CREDENTIALS=\"path/to/key.json\"\n"
                "  Linux/Mac: export GOOGLE_APPLICATION_CREDENTIALS=\"/path/to/key.json\"\n"
                "Or place the key file at: ~/.config/gcloud/application_default_credentials.json"
            )
        raise Exception(f"Failed to initialize Vision API client: {error_msg}")


def extract_text_from_image(image_path: str) -> Dict[str, any]:
    """
    Extract text from an image using Google Vision API OCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dict containing:
            - 'full_text': Complete extracted text
            - 'text_blocks': List of text blocks with bounding boxes
            - 'words': List of individual words with positions
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    client = get_vision_client()
    
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        texts = response.text_annotations
        
        if not texts:
            return {
                'full_text': '',
                'text_blocks': [],
                'words': []
            }
        
        # First annotation contains the full text
        full_text = texts[0].description
        
        # Extract individual text blocks and words
        text_blocks = []
        words = []
        
        for text in texts[1:]:  # Skip first (it's the full text)
            vertices = text.bounding_poly.vertices
            text_blocks.append({
                'text': text.description,
                'bounding_box': {
                    'x1': vertices[0].x if len(vertices) > 0 else 0,
                    'y1': vertices[0].y if len(vertices) > 0 else 0,
                    'x2': vertices[2].x if len(vertices) > 2 else 0,
                    'y2': vertices[2].y if len(vertices) > 2 else 0,
                }
            })
        
        # Extract words from full text response
        document = response.full_text_annotation
        if document:
            for page in document.pages:
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = ''.join([
                                symbol.text for symbol in word.symbols
                            ])
                            vertices = word.bounding_box.vertices
                            words.append({
                                'text': word_text,
                                'confidence': word.confidence if hasattr(word, 'confidence') else 1.0,
                                'bounding_box': {
                                    'x1': vertices[0].x if len(vertices) > 0 else 0,
                                    'y1': vertices[0].y if len(vertices) > 0 else 0,
                                    'x2': vertices[2].x if len(vertices) > 2 else 0,
                                    'y2': vertices[2].y if len(vertices) > 2 else 0,
                                }
                            })
        
        return {
            'full_text': full_text,
            'text_blocks': text_blocks,
            'words': words
        }
        
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")


def detect_objects_in_image(image_path: str) -> List[Dict]:
    """
    Detect objects in an image using Google Vision API.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of detected objects with their locations and labels
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    client = get_vision_client()
    
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.object_localization(image=image)
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        objects = []
        for obj in response.localized_object_annotations:
            vertices = obj.bounding_poly.normalized_vertices
            objects.append({
                'name': obj.name,
                'score': obj.score,  # Confidence score
                'bounding_box': {
                    'x1': vertices[0].x if len(vertices) > 0 else 0,
                    'y1': vertices[0].y if len(vertices) > 0 else 0,
                    'x2': vertices[2].x if len(vertices) > 2 else 1,
                    'y2': vertices[2].y if len(vertices) > 2 else 1,
                }
            })
        
        return objects
        
    except Exception as e:
        raise Exception(f"Error detecting objects in image: {str(e)}")


def detect_labels_in_image(image_path: str, max_results: int = 10) -> List[Dict]:
    """
    Detect labels (categories) in an image.
    
    Args:
        image_path: Path to the image file
        max_results: Maximum number of labels to return
        
    Returns:
        List of labels with confidence scores
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    client = get_vision_client()
    
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.label_detection(image=image, max_results=max_results)
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        labels = []
        for label in response.label_annotations:
            labels.append({
                'description': label.description,
                'score': label.score,  # Confidence score (0-1)
                'mid': label.mid  # Machine-generated identifier
            })
        
        return labels
        
    except Exception as e:
        raise Exception(f"Error detecting labels in image: {str(e)}")


def extract_text_from_pdf(pdf_path: str) -> Dict[str, any]:
    """
    Extract text from a PDF file using Google Vision API.
    
    Note: Vision API can process PDFs, but they must be converted to images first,
    or you can use Document AI API for better PDF handling.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dict with extracted text (similar to extract_text_from_image)
    """
    # Note: For PDF processing, Google Document AI API is recommended
    # This function is a placeholder - PDF support requires converting pages to images
    # or using Document AI API
    raise NotImplementedError(
        "PDF text extraction requires Google Document AI API or converting PDF pages to images first. "
        "Consider using Document AI API for better PDF handling."
    )


def analyze_vehicle_document(image_path: str) -> Dict[str, any]:
    """
    Analyze a vehicle document (registration, insurance, etc.) and extract structured information.
    
    This is a wrapper function that combines text extraction with basic parsing
    to extract vehicle information from documents.
    
    Args:
        image_path: Path to the document image
        
    Returns:
        Dict containing:
            - 'raw_text': Full extracted text
            - 'vehicle_info': Extracted vehicle information (if patterns are found)
            - 'text_blocks': Text blocks with locations
    """
    try:
        # Extract text using OCR
        text_result = extract_text_from_image(image_path)
        full_text = text_result['full_text']
        
        # Basic parsing for common vehicle document fields
        # You can enhance this with regex patterns or ML models
        vehicle_info = {}
        
        # Look for common patterns (enhance these based on your document formats)
        import re
        
        # License plate patterns (vary by country)
        plate_patterns = [
            r'[A-Z]{2,3}\s*[0-9]{1,4}\s*[A-Z]{1,2}\s*[0-9]{4}',  # Indian format
            r'[A-Z]{1,3}[0-9]{1,4}[A-Z]{1,3}',  # Generic format
        ]
        for pattern in plate_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                vehicle_info['registration_number'] = match.group().strip()
                break
        
        # Year patterns
        year_match = re.search(r'(19|20)\d{2}', full_text)
        if year_match:
            vehicle_info['year'] = year_match.group()
        
        # Extract any structured data you can identify
        # This is a basic example - enhance based on your document formats
        
        return {
            'raw_text': full_text,
            'vehicle_info': vehicle_info,
            'text_blocks': text_result['text_blocks'],
            'words': text_result['words']
        }
        
    except Exception as e:
        raise Exception(f"Error analyzing vehicle document: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python google_vision_integration.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    try:
        print("=" * 70)
        print("Google Vision API - Text Extraction Test")
        print("=" * 70)
        
        # Test text extraction
        print("\n1. Extracting text...")
        text_result = extract_text_from_image(image_path)
        print(f"\nFull Text:\n{text_result['full_text']}")
        print(f"\nNumber of text blocks: {len(text_result['text_blocks'])}")
        print(f"Number of words: {len(text_result['words'])}")
        
        # Test label detection
        print("\n" + "=" * 70)
        print("2. Detecting labels...")
        labels = detect_labels_in_image(image_path, max_results=5)
        for label in labels:
            print(f"  - {label['description']}: {label['score']:.2%}")
        
        # Test object detection
        print("\n" + "=" * 70)
        print("3. Detecting objects...")
        objects = detect_objects_in_image(image_path)
        for obj in objects[:5]:  # Show first 5
            print(f"  - {obj['name']}: {obj['score']:.2%}")
        
        print("\n" + "=" * 70)
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)







