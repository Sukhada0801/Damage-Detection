"""
Multi-Provider Vehicle Damage Detection
========================================
Combines multiple AI providers for improved accuracy.
Uses ensemble/voting approach to reduce false positives and catch more damages.

Supported Providers:
1. OpenAI GPT-4o (current) - Best for understanding context
2. Roboflow - Pre-trained object detection models  
3. Clarifai - General and custom models
4. Google Cloud Vision - Object detection and labels

Usage:
    from multi_provider_damage_detection import analyze_with_multiple_providers
    
    result = analyze_with_multiple_providers(
        image_path="car.jpg",
        providers=['openai', 'roboflow']
    )
"""

import os
import json
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def analyze_with_openai(image_path: str, damage_hints: List = None) -> Dict:
    """Use OpenAI GPT-4o for damage detection."""
    try:
        from openai_gpt_vision import analyze_vehicle_damage
        report, annotated_path, damages = analyze_vehicle_damage(
            image_path, 
            damage_hints=damage_hints
        )
        return {
            'success': True,
            'provider': 'OpenAI GPT-4o',
            'damages': damages,
            'report': report,
            'annotated_path': annotated_path
        }
    except Exception as e:
        return {'success': False, 'provider': 'OpenAI', 'error': str(e), 'damages': []}


def analyze_with_roboflow(image_path: str, model_id: str = None) -> Dict:
    """Use Roboflow for damage detection."""
    try:
        from roboflow_damage_detection import detect_damage_roboflow
        return detect_damage_roboflow(image_path, model_id=model_id or "car-damage-detection")
    except Exception as e:
        return {'success': False, 'provider': 'Roboflow', 'error': str(e), 'damages': []}


def analyze_with_clarifai(image_path: str) -> Dict:
    """Use Clarifai for damage detection."""
    try:
        from clarifai_damage_detection import detect_damage_clarifai
        return detect_damage_clarifai(image_path)
    except Exception as e:
        return {'success': False, 'provider': 'Clarifai', 'error': str(e), 'damages': []}


def analyze_with_google_vision(image_path: str) -> Dict:
    """Use Google Cloud Vision for object detection."""
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        
        # Get credentials
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            creds_path = os.path.join(os.path.dirname(__file__), 'google-vision-key.json')
        
        if os.path.exists(creds_path):
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            return {'success': False, 'provider': 'Google Vision', 'error': 'Credentials not found', 'damages': []}
        
        # Read image
        with open(image_path, 'rb') as f:
            content = f.read()
        
        image = vision.Image(content=content)
        
        # Detect objects
        response = client.object_localization(image=image)
        objects = response.localized_object_annotations
        
        # Filter for vehicle-related and damage-related objects
        damage_keywords = ['damage', 'dent', 'scratch', 'car', 'vehicle', 'bumper', 'fender', 'hood', 'door']
        
        damages = []
        for obj in objects:
            if any(kw in obj.name.lower() for kw in damage_keywords) or obj.score > 0.7:
                vertices = obj.bounding_poly.normalized_vertices
                if len(vertices) >= 4:
                    damages.append({
                        'label': obj.name,
                        'confidence': obj.score * 100,
                        'extent': 'Moderate' if obj.score > 0.6 else 'Minor',
                        'box': {
                            'x_percent': vertices[0].x * 100,
                            'y_percent': vertices[0].y * 100,
                            'width_percent': (vertices[2].x - vertices[0].x) * 100,
                            'height_percent': (vertices[2].y - vertices[0].y) * 100
                        }
                    })
        
        return {
            'success': True,
            'provider': 'Google Cloud Vision',
            'damages': damages,
            'total_objects': len(objects)
        }
        
    except Exception as e:
        return {'success': False, 'provider': 'Google Vision', 'error': str(e), 'damages': []}


def analyze_with_multiple_providers(
    image_path: str,
    providers: List[str] = None,
    damage_hints: List = None,
    parallel: bool = True
) -> Dict:
    """
    Run damage detection with multiple providers and combine results.
    
    Args:
        image_path: Path to vehicle image
        providers: List of providers to use ['openai', 'roboflow', 'clarifai', 'google']
        damage_hints: Optional hints from estimation document
        parallel: Run providers in parallel for speed
    
    Returns:
        Combined results from all providers with ensemble scoring
    """
    if providers is None:
        providers = ['openai']  # Default to OpenAI only
    
    provider_funcs = {
        'openai': lambda: analyze_with_openai(image_path, damage_hints),
        'roboflow': lambda: analyze_with_roboflow(image_path),
        'clarifai': lambda: analyze_with_clarifai(image_path),
        'google': lambda: analyze_with_google_vision(image_path)
    }
    
    results = {}
    all_damages = []
    
    if parallel and len(providers) > 1:
        # Run in parallel
        with ThreadPoolExecutor(max_workers=len(providers)) as executor:
            futures = {
                executor.submit(provider_funcs[p]): p 
                for p in providers if p in provider_funcs
            }
            for future in as_completed(futures):
                provider = futures[future]
                try:
                    result = future.result()
                    results[provider] = result
                    if result.get('success') and result.get('damages'):
                        for d in result['damages']:
                            d['source_provider'] = provider
                            all_damages.append(d)
                except Exception as e:
                    results[provider] = {'success': False, 'error': str(e)}
    else:
        # Run sequentially
        for provider in providers:
            if provider in provider_funcs:
                result = provider_funcs[provider]()
                results[provider] = result
                if result.get('success') and result.get('damages'):
                    for d in result['damages']:
                        d['source_provider'] = provider
                        all_damages.append(d)
    
    # Combine and deduplicate damages (simple approach)
    combined_damages = merge_overlapping_damages(all_damages)
    
    return {
        'success': any(r.get('success') for r in results.values()),
        'providers_used': list(results.keys()),
        'provider_results': results,
        'combined_damages': combined_damages,
        'total_damages': len(combined_damages),
        'all_damages_raw': all_damages
    }


def merge_overlapping_damages(damages: List[Dict], iou_threshold: float = 0.3) -> List[Dict]:
    """
    Merge overlapping damage detections from multiple providers.
    Damages from multiple providers in similar locations are combined.
    
    Args:
        damages: List of damage detections from all providers
        iou_threshold: Intersection over Union threshold for merging
    
    Returns:
        Merged list of damages with provider counts
    """
    if not damages:
        return []
    
    # Simple merging: group by rough location
    merged = []
    used = set()
    
    for i, d1 in enumerate(damages):
        if i in used:
            continue
        
        # Find similar damages
        similar = [d1]
        for j, d2 in enumerate(damages[i+1:], start=i+1):
            if j in used:
                continue
            if boxes_overlap(d1.get('box', {}), d2.get('box', {}), iou_threshold):
                similar.append(d2)
                used.add(j)
        
        # Merge similar damages
        if len(similar) > 1:
            merged_damage = {
                'label': similar[0].get('label', 'Damage'),
                'confidence': max(d.get('confidence', 0) for d in similar),
                'extent': max((d.get('extent', 'Minor') for d in similar), 
                             key=lambda x: {'Minor': 1, 'Moderate': 2, 'Severe': 3}.get(x, 0)),
                'location': similar[0].get('location', ''),
                'box': similar[0].get('box', {}),
                'detected_by': list(set(d.get('source_provider', 'unknown') for d in similar)),
                'detection_count': len(similar),
                'high_confidence': len(similar) > 1  # Multiple providers agree
            }
            merged.append(merged_damage)
        else:
            d1['detected_by'] = [d1.get('source_provider', 'unknown')]
            d1['detection_count'] = 1
            d1['high_confidence'] = False
            merged.append(d1)
    
    # Sort by confidence
    merged.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    return merged


def boxes_overlap(box1: Dict, box2: Dict, threshold: float = 0.3) -> bool:
    """Check if two bounding boxes overlap significantly."""
    if not box1 or not box2:
        return False
    
    try:
        x1_1, y1_1 = box1.get('x_percent', 0), box1.get('y_percent', 0)
        x2_1 = x1_1 + box1.get('width_percent', 0)
        y2_1 = y1_1 + box1.get('height_percent', 0)
        
        x1_2, y1_2 = box2.get('x_percent', 0), box2.get('y_percent', 0)
        x2_2 = x1_2 + box2.get('width_percent', 0)
        y2_2 = y1_2 + box2.get('height_percent', 0)
        
        # Calculate intersection
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return False
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        area1 = box1.get('width_percent', 0) * box1.get('height_percent', 0)
        area2 = box2.get('width_percent', 0) * box2.get('height_percent', 0)
        union = area1 + area2 - intersection
        
        if union <= 0:
            return False
        
        iou = intersection / union
        return iou > threshold
        
    except:
        return False


# ============================================================================
# CONFIGURATION
# ============================================================================

AVAILABLE_PROVIDERS = {
    'openai': {
        'name': 'OpenAI GPT-4o',
        'env_var': 'OPENAI_API_KEY',
        'signup_url': 'https://platform.openai.com',
        'free_tier': False,
        'best_for': 'Context understanding, document hints integration'
    },
    'roboflow': {
        'name': 'Roboflow',
        'env_var': 'ROBOFLOW_API_KEY',
        'signup_url': 'https://roboflow.com',
        'free_tier': True,
        'best_for': 'Object detection with bounding boxes'
    },
    'clarifai': {
        'name': 'Clarifai',
        'env_var': 'CLARIFAI_PAT',
        'signup_url': 'https://clarifai.com',
        'free_tier': True,
        'best_for': 'Custom model training'
    },
    'google': {
        'name': 'Google Cloud Vision',
        'env_var': 'GOOGLE_APPLICATION_CREDENTIALS',
        'signup_url': 'https://cloud.google.com/vision',
        'free_tier': True,  # 1000 units/month
        'best_for': 'Object localization, label detection'
    }
}


def check_provider_availability() -> Dict:
    """Check which providers are configured and available."""
    status = {}
    for provider, info in AVAILABLE_PROVIDERS.items():
        env_var = info['env_var']
        configured = bool(os.environ.get(env_var))
        status[provider] = {
            **info,
            'configured': configured,
            'status': '✓ Ready' if configured else f'✗ Set {env_var}'
        }
    return status


if __name__ == "__main__":
    print("Multi-Provider Damage Detection")
    print("=" * 60)
    print("\nAvailable Providers:")
    
    status = check_provider_availability()
    for provider, info in status.items():
        print(f"\n  {provider.upper()}: {info['status']}")
        print(f"    Name: {info['name']}")
        print(f"    Sign up: {info['signup_url']}")
        print(f"    Free tier: {'Yes' if info['free_tier'] else 'No'}")
        print(f"    Best for: {info['best_for']}")
    
    print("\n" + "=" * 60)
    print("\nUsage example:")
    print("  from multi_provider_damage_detection import analyze_with_multiple_providers")
    print("  result = analyze_with_multiple_providers('car.jpg', providers=['openai', 'roboflow'])")




