"""
Clarifai Vehicle Damage Detection Integration
==============================================
Clarifai offers pre-built AI models and the ability to train custom models.

Setup:
1. Sign up at https://clarifai.com (free tier: 1,000 operations/month)
2. Create an app in the portal
3. Get your Personal Access Token (PAT)
4. Set environment variable: CLARIFAI_PAT=your_pat

Features:
- Pre-trained general object detection
- Custom model training on your damage images
- Visual search capabilities
"""

import os
import json
import base64
from typing import Dict, List, Optional

# Check if clarifai is installed
try:
    from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
    from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
    from clarifai_grpc.grpc.api.status import status_code_pb2
    CLARIFAI_AVAILABLE = True
except ImportError:
    CLARIFAI_AVAILABLE = False
    print("[Clarifai] Package not installed. Install with: pip install clarifai-grpc")


def detect_damage_clarifai(
    image_path: str,
    pat: str = None,
    user_id: str = "clarifai",
    app_id: str = "main",
    model_id: str = "general-image-detection"
) -> Dict:
    """
    Detect vehicle damage using Clarifai's models.
    
    Args:
        image_path: Path to the vehicle image
        pat: Personal Access Token (or uses CLARIFAI_PAT env var)
        user_id: Clarifai user ID (default: "clarifai" for pre-built models)
        app_id: App ID (default: "main")
        model_id: Model to use for detection
    
    Returns:
        Dictionary with detected objects and potential damages
    """
    if not CLARIFAI_AVAILABLE:
        return {
            'success': False,
            'error': 'Clarifai package not installed. Run: pip install clarifai-grpc',
            'damages': []
        }
    
    pat = pat or os.environ.get('CLARIFAI_PAT')
    if not pat:
        return {
            'success': False,
            'error': 'CLARIFAI_PAT environment variable not set. Get PAT from https://clarifai.com/settings/security',
            'damages': []
        }
    
    try:
        # Setup gRPC channel
        channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)
        
        # Create metadata with PAT
        metadata = (('authorization', f'Key {pat}'),)
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Create request
        request = service_pb2.PostModelOutputsRequest(
            user_app_id=resources_pb2.UserAppIDSet(user_id=user_id, app_id=app_id),
            model_id=model_id,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        image=resources_pb2.Image(base64=image_bytes)
                    )
                )
            ]
        )
        
        # Make prediction
        response = stub.PostModelOutputs(request, metadata=metadata)
        
        if response.status.code != status_code_pb2.SUCCESS:
            return {
                'success': False,
                'error': f"Clarifai API error: {response.status.description}",
                'damages': []
            }
        
        # Parse results
        damages = []
        output = response.outputs[0]
        
        # Handle detection models (with bounding boxes)
        if output.data.regions:
            for region in output.data.regions:
                bbox = region.region_info.bounding_box
                
                # Get the top concept for this region
                concepts = region.data.concepts
                if concepts:
                    top_concept = max(concepts, key=lambda c: c.value)
                    
                    damage = {
                        'label': top_concept.name,
                        'confidence': top_concept.value * 100,
                        'extent': classify_severity_clarifai(top_concept.value),
                        'box': {
                            'x_percent': bbox.left_col * 100,
                            'y_percent': bbox.top_row * 100,
                            'width_percent': (bbox.right_col - bbox.left_col) * 100,
                            'height_percent': (bbox.bottom_row - bbox.top_row) * 100
                        }
                    }
                    damages.append(damage)
        
        # Handle classification models (concepts without boxes)
        elif output.data.concepts:
            # Filter for damage-related concepts
            damage_keywords = ['damage', 'dent', 'scratch', 'crack', 'broken', 'bent', 'crushed', 'collision']
            
            for concept in output.data.concepts:
                if any(kw in concept.name.lower() for kw in damage_keywords) or concept.value > 0.5:
                    damage = {
                        'label': concept.name,
                        'confidence': concept.value * 100,
                        'extent': classify_severity_clarifai(concept.value),
                        'location': 'General (classification model)'
                    }
                    damages.append(damage)
        
        return {
            'success': True,
            'provider': 'Clarifai',
            'model': model_id,
            'damages': damages,
            'total_damages': len(damages)
        }
        
    except Exception as e:
        return {
            'success': False,
            'provider': 'Clarifai',
            'error': str(e),
            'damages': []
        }


def classify_severity_clarifai(confidence: float) -> str:
    """Classify severity based on confidence."""
    if confidence > 0.8:
        return 'Severe'
    elif confidence > 0.5:
        return 'Moderate'
    else:
        return 'Minor'


# ============================================================================
# CLARIFAI MODELS FOR DAMAGE DETECTION
# ============================================================================
"""
Pre-built models to try:
1. "general-image-detection" - General object detection
2. "general-image-recognition" - Image classification
3. "vehicle-recognition" - Vehicle-specific recognition

For best results with vehicle damage, you should train a custom model:
1. Go to https://clarifai.com
2. Create an app
3. Upload vehicle damage images with labels
4. Train a custom detection model
5. Use your app_id and model_id in this script

Custom model training guide:
https://docs.clarifai.com/portal-guide/model/deep-training
"""


if __name__ == "__main__":
    print("Clarifai Vehicle Damage Detection")
    print("=" * 50)
    print("\nSetup instructions:")
    print("1. Sign up at https://clarifai.com")
    print("2. Go to Settings > Security")
    print("3. Create a Personal Access Token (PAT)")
    print("4. Set environment variable:")
    print("   $env:CLARIFAI_PAT='your_pat'")
    print("\n5. Install package: pip install clarifai-grpc")
    print("\nUsage:")
    print("   from clarifai_damage_detection import detect_damage_clarifai")
    print("   result = detect_damage_clarifai('car_image.jpg')")




