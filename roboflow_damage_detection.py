"""
Roboflow Vehicle Damage Detection Integration
==============================================
Uses pre-trained computer vision models specifically trained for vehicle damage.

Setup:
1. Sign up at https://roboflow.com (free tier: 1,000 inferences/month)
2. Get your API key from Settings > API Keys
3. Set environment variable: ROBOFLOW_API_KEY=your_key

Models to try (search on Roboflow Universe):
- "car-damage-detection" 
- "vehicle-damage-detection"
- "auto-damage-classifier"
"""

import os
import json
import base64
from typing import Dict, List, Optional

# Check if roboflow is installed
try:
    from roboflow import Roboflow
    ROBOFLOW_AVAILABLE = True
except ImportError:
    ROBOFLOW_AVAILABLE = False
    print("[Roboflow] Package not installed. Install with: pip install roboflow")


def get_roboflow_client(api_key: str = None):
    """
    Initialize Roboflow client.
    
    Args:
        api_key: Roboflow API key (or uses ROBOFLOW_API_KEY env var)
    """
    if not ROBOFLOW_AVAILABLE:
        raise ImportError("Roboflow package not installed. Run: pip install roboflow")
    
    api_key = api_key or os.environ.get('ROBOFLOW_API_KEY')
    if not api_key:
        raise ValueError(
            "Roboflow API key not found!\n"
            "Get your key at: https://app.roboflow.com/settings/api\n"
            "Then set: $env:ROBOFLOW_API_KEY='your_key'"
        )
    
    return Roboflow(api_key=api_key)


def detect_damage_roboflow(
    image_path: str,
    api_key: str = None,
    model_id: str = "car-damage-detection",
    model_version: int = 1,
    confidence: int = 40,
    overlap: int = 30
) -> Dict:
    """
    Detect vehicle damage using Roboflow's pre-trained models.
    
    Args:
        image_path: Path to the vehicle image
        api_key: Roboflow API key
        model_id: The model ID from Roboflow Universe
        model_version: Model version number
        confidence: Minimum confidence threshold (0-100)
        overlap: NMS overlap threshold (0-100)
    
    Returns:
        Dictionary with detected damages and bounding boxes
    """
    try:
        rf = get_roboflow_client(api_key)
        
        # Load the model
        project = rf.workspace().project(model_id)
        model = project.version(model_version).model
        
        # Run inference
        result = model.predict(image_path, confidence=confidence, overlap=overlap).json()
        
        # Parse results into our standard format
        damages = []
        predictions = result.get('predictions', [])
        
        for pred in predictions:
            damage = {
                'label': pred.get('class', 'Damage'),
                'confidence': pred.get('confidence', 0) * 100,
                'location': f"x:{pred.get('x', 0):.0f}, y:{pred.get('y', 0):.0f}",
                'extent': classify_severity(pred.get('confidence', 0)),
                'box': {
                    'x_percent': (pred.get('x', 0) - pred.get('width', 0)/2) / result.get('image', {}).get('width', 1) * 100,
                    'y_percent': (pred.get('y', 0) - pred.get('height', 0)/2) / result.get('image', {}).get('height', 1) * 100,
                    'width_percent': pred.get('width', 0) / result.get('image', {}).get('width', 1) * 100,
                    'height_percent': pred.get('height', 0) / result.get('image', {}).get('height', 1) * 100
                }
            }
            damages.append(damage)
        
        return {
            'success': True,
            'provider': 'Roboflow',
            'model': model_id,
            'damages': damages,
            'total_damages': len(damages),
            'raw_response': result
        }
        
    except Exception as e:
        return {
            'success': False,
            'provider': 'Roboflow',
            'error': str(e),
            'damages': []
        }


def classify_severity(confidence: float) -> str:
    """Classify damage severity based on detection confidence."""
    if confidence > 0.8:
        return 'Severe'
    elif confidence > 0.6:
        return 'Moderate'
    else:
        return 'Minor'


# Alternative: Use Roboflow's hosted inference API directly (no SDK needed)
def detect_damage_roboflow_api(
    image_path: str,
    api_key: str = None,
    model_id: str = "car-damage-detection",
    model_version: int = 1
) -> Dict:
    """
    Direct API call to Roboflow (doesn't require roboflow package).
    
    This is useful if you don't want to install the SDK.
    """
    import requests
    
    api_key = api_key or os.environ.get('ROBOFLOW_API_KEY')
    if not api_key:
        raise ValueError("ROBOFLOW_API_KEY environment variable not set")
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # API endpoint
    url = f"https://detect.roboflow.com/{model_id}/{model_version}"
    
    response = requests.post(
        url,
        params={'api_key': api_key},
        data=image_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if response.status_code == 200:
        result = response.json()
        return {
            'success': True,
            'provider': 'Roboflow API',
            'predictions': result.get('predictions', []),
            'raw_response': result
        }
    else:
        return {
            'success': False,
            'error': f"API error: {response.status_code} - {response.text}"
        }


# ============================================================================
# POPULAR ROBOFLOW MODELS FOR VEHICLE DAMAGE
# ============================================================================
"""
Search these on https://universe.roboflow.com:

1. "car-damage-detection" - General car damage
2. "vehicle-damage-detection" - Multiple damage types
3. "dent-detection" - Specifically for dents
4. "scratch-detection" - Specifically for scratches
5. "broken-glass-detection" - For windshield/window damage

To use a specific model:
    result = detect_damage_roboflow(
        image_path="car.jpg",
        model_id="your-model-id",
        model_version=1
    )
"""


if __name__ == "__main__":
    # Example usage
    print("Roboflow Vehicle Damage Detection")
    print("=" * 50)
    print("\nSetup instructions:")
    print("1. Sign up at https://roboflow.com")
    print("2. Get API key from Settings > API Keys")
    print("3. Set environment variable:")
    print("   $env:ROBOFLOW_API_KEY='your_api_key'")
    print("\n4. Install package: pip install roboflow")
    print("\nUsage:")
    print("   from roboflow_damage_detection import detect_damage_roboflow")
    print("   result = detect_damage_roboflow('car_image.jpg')")




