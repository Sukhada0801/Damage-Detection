
"""
Vehicle Damage Detection System for Insurance Assessment
=========================================================
This application analyzes images and videos of vehicles to detect and assess
damage for insurance claim processing. It identifies both geometric (structural)
and cosmetic damage types.

Damage Categories:
- GEOMETRIC (Structural): Side mirror damage, shattered glass, headlight/taillight
  damage, dents, bumper damage, body panel damage
- COSMETIC: Scratches, paint chips, fading, minor surface damage

Author: Insurance AI Solutions
Version: 2.0
"""

from openai import OpenAI
import base64
import os
import sys
import argparse
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Try to import video processing libraries
try:
    import cv2
    VIDEO_SUPPORT = True
except ImportError:
    VIDEO_SUPPORT = False
    print("Warning: cv2 (opencv-python) not installed. Video support disabled.")
    print("Install with: pip install opencv-python")

# Import tkinter for file picker
try:
    import tkinter as tk
    from tkinter import filedialog
    FILE_PICKER_AVAILABLE = True
except ImportError:
    FILE_PICKER_AVAILABLE = False

# Load API key from environment variable only (security best practice)
api_key = os.getenv("OPENAI_API_KEY")

# Strip any whitespace or newlines from the API key (common copy-paste issue)
if api_key:
    api_key = api_key.strip()

# Require API key to be set via environment variable
if not api_key:
    print("=" * 70)
    print("ERROR: OpenAI API key not found!")
    print("=" * 70)
    print("\nPlease set your API key as an environment variable:")
    print("  Windows (PowerShell): $env:OPENAI_API_KEY=\"your-api-key-here\"")
    print("  Windows (CMD): set OPENAI_API_KEY=your-api-key-here")
    print("  Linux/Mac: export OPENAI_API_KEY=\"your-api-key-here\"")
    print("\nGet your API key from: https://platform.openai.com/api-keys")
    print("=" * 70)
    sys.exit(1)

# Validate API key format
if not api_key.startswith("sk-"):
    print("Warning: API key format may be incorrect. OpenAI API keys typically start with 'sk-'")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Error initializing OpenAI client: {str(e)}")
    sys.exit(1)

# Model Configuration
# Available models for vision tasks (in order of capability):
#   1. "gpt-4o" - Latest GPT-4 Omni (auto-updates to newest version)
#   2. "gpt-4o-2024-11-20" - Specific snapshot with consistent behavior
#   3. "gpt-4o-mini" - Faster and cheaper, slightly less accurate
#   4. "chatgpt-4o-latest" - ChatGPT's latest model version
#
# NOTE: o1/o1-preview models have limited vision support and different API parameters
# For best damage detection accuracy, use gpt-4o or its snapshots

# You can change this to try different models
GPT_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')  # Default to latest gpt-4o
IMAGE_DETAIL = "high"  # Use high detail for better damage detection accuracy
MAX_TOKENS_BOXES = 4000  # Increased for multiple damage descriptions
MAX_TOKENS_REPORT = 2000  # Increased to handle multiple damages
TEMPERATURE = 0.1  # Low temperature for consistent, precise results
TOP_P = 0.95  # Nucleus sampling for better quality

print(f"[OpenAI] Using model: {GPT_MODEL}")

# Simple Damage Assessment Prompt - Enhanced for comprehensive detection
SIMPLE_DAMAGE_PROMPT = """You are an expert vehicle damage inspector. Analyze this vehicle image THOROUGHLY and identify ALL visible damage.

CRITICAL INSTRUCTIONS:
1. Examine the ENTIRE image systematically - check all areas: front, back, sides, roof, windows, lights, mirrors, bumpers, doors, panels
2. Identify EVERY instance of damage - do not miss any scratches, dents, cracks, or other damage
3. If there are MULTIPLE damages, you MUST list ALL of them separately
4. Be thorough and comprehensive - even minor damage should be reported
5. Count each distinct damage area as a separate item

For EACH damage found, provide:
1. LOCATION: Where on the vehicle (e.g., "Front left door", "Rear bumper", "Windshield", "Right side panel")
2. DAMAGE TYPE: What kind of damage (e.g., "Dent", "Scratch", "Crack", "Shattered glass", "Paint chip", "Bumper damage")
3. EXTENT: Severity level (Minor / Moderate / Severe)

Format your response EXACTLY like this:

DAMAGE FOUND: [Yes/No]

If damage found, list EACH damage separately (even if there are multiple):
---
DAMAGE 1:
- Location: [specific location on vehicle]
- Type: [type of damage]
- Extent: [Minor/Moderate/Severe]
---
DAMAGE 2:
- Location: [specific location on vehicle]
- Type: [type of damage]
- Extent: [Minor/Moderate/Severe]
---
DAMAGE 3:
- Location: [specific location on vehicle]
- Type: [type of damage]
- Extent: [Minor/Moderate/Severe]
---
(Continue numbering for ALL damages found - do not skip any)

IMPORTANT: If you see 2 damages, list both. If you see 3 damages, list all 3. Be exhaustive and complete.

If NO damage found, simply state:
NO DAMAGE DETECTED - Vehicle appears to be in good condition."""

# Prompt to get bounding box coordinates for damage highlighting - tuned for generous, human-correctable boxes
BOUNDING_BOX_PROMPT = """You are a precise damage localization expert. Analyze this vehicle image SYSTEMATICALLY and provide COMPLETE bounding box coordinates that fully encompass EACH AND EVERY visible damage area.

🚨 CRITICAL INSPECTION CHECKLIST - CHECK THESE AREAS FIRST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. BUMPERS (front & rear) - Most commonly damaged! Look for:
   - Crushed/pushed-in sections
   - Cracked plastic
   - Misalignment with body
   - Missing pieces
2. CORNERS (all 4) - Second most common:
   - Front left corner (fender + bumper junction)
   - Front right corner
   - Rear left corner
   - Rear right corner
3. FENDERS - Check for dents, creases, pushed-in metal
4. HOOD - Dents, creases, paint damage
5. DOORS - Dents, scratches, dings
6. LIGHTS - Cracked, broken, misaligned headlights/taillights
7. GRILLE - Broken, missing pieces
8. MIRRORS - Cracked, missing, damaged
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIMARY GOAL:
- Draw boxes that COMPLETELY COVER the full damaged region, even if the box is slightly larger than necessary.
- It is MUCH BETTER for a box to be TOO LARGE (but tightly centered on the damage) than to cut off any part of the damage.
- PAY SPECIAL ATTENTION TO BUMPERS AND CORNERS - these are often missed!

CRITICAL: You MUST identify ALL distinct damages in the image. If there are 2 damages, return 2 boxes. If there are 3 damages, return 3 boxes. Do not miss any damage areas.

IMAGE COORDINATE SYSTEM:
1. The image coordinate system: (0,0) is TOP-LEFT corner, (100,100) is BOTTOM-RIGHT corner
2. x_percent: horizontal position from LEFT edge (0=far left, 100=far right)
3. y_percent: vertical position from TOP edge (0=top, 100=bottom)

BOX DESIGN RULES FOR COMPLETE COVERAGE:
1. The box MUST cover the ENTIRE damaged area - include ALL edges, boundaries, and affected regions.
2. For scratches: include the full length from start to end AND a bit of clean area around it.
3. For dents: include the complete dented area including any paint cracks, deformation, and shadowed contours.
4. For cracks (glass, lights, body): include the entire crack length and any branching.
5. Always add a generous margin of at LEAST 5–8% around the damage on all sides to ensure nothing is cut off.
6. When in doubt, expand the box further until you are SURE the whole damage is inside.
7. Avoid tiny boxes: very narrow or very short boxes are almost always too small – expand them.
8. Do NOT tightly hug only the most obvious center; include edges and subtle extensions of the damage.

STEP-BY-STEP PROCESS FOR EACH DAMAGE:
1. Identify the damage type and its full spatial extent (look carefully for faint edges, long scratches, hairline cracks, etc.).
2. Find the LEFT-MOST point of the damage (including any edges) → this is the base for x_percent.
3. Find the TOP-MOST point of the damage (including any edges) → this is the base for y_percent.
4. Find the RIGHT-MOST and BOTTOM-MOST points of the damage.
5. Compute width_percent and height_percent to cover from LEFT-MOST to RIGHT-MOST and TOP-MOST to BOTTOM-MOST.
6. Then EXPAND the box in all directions by at least 5–8% (more if the damage is complex or uncertain).
7. Verify: If the box were drawn on the image, NO PART of the damage should touch or cross the box border. There should always be a small buffer of clean area around the damage.

EXAMPLE: If a scratch extends from center-left to center-right:
- Scratch starts 20% from left edge and ends at 50% → after margins, you might use:
  - x_percent ≈ 16
  - width_percent ≈ 40
- Scratch is around the vertical middle and 2% high → after margins:
  - y_percent ≈ 40
  - height_percent ≈ 10

EXAMPLE: If a dent is in the center:
- Dent center is at 50% from left, dent radius is 8% → base box might be from 42% to 58%.
- After adding margins, you might use:
  - x_percent ≈ 38
  - width_percent ≈ 24
- Do the same vertically so the dent (and subtle edges) are comfortably inside.

Return ONLY this JSON format, no other text. Include ALL damages found:
{
    "damages": [
        {
            "label": "Brief damage description (e.g., Dent, Scratch, Crack)",
            "location": "Location on vehicle",
            "extent": "Minor/Moderate/Severe",
            "box": {
                "x_percent": <number 0-100>,
                "y_percent": <number 0-100>,
                "width_percent": <number 0-100>,
                "height_percent": <number 0-100>
            }
        },
        {
            "label": "Second damage description",
            "location": "Location on vehicle",
            "extent": "Minor/Moderate/Severe",
            "box": {
                "x_percent": <number 0-100>,
                "y_percent": <number 0-100>,
                "width_percent": <number 0-100>,
                "height_percent": <number 0-100>
            }
        }
        ... (add more objects for each additional damage found)
    ]
}

CRITICAL REQUIREMENTS:
- If you see 2 damages, the "damages" array must contain exactly 2 objects
- If you see 3 damages, the "damages" array must contain exactly 3 objects
- Do NOT combine multiple damages into one box
- Each distinct damage area gets its own separate entry
- Be exhaustive - check the entire image for all damage

If no damage is found, return: {"damages": []}

IMPORTANT: 
- Return ONLY valid JSON
- Ensure boxes COMPLETELY cover the entire damage area with a VISUAL MARGIN of clean area around it
- Include generous margins to prevent any part of damage from being outside the box
- For linear damage (scratches, cracks), ensure the box spans the full length PLUS side margins
- For area damage (dents, paint chips), ensure the box covers the complete affected region PLUS surrounding buffer"""


def extract_video_frames(video_path, num_frames=5):
    """
    Extract multiple frames from a video for comprehensive analysis.
    
    Args:
        video_path (str): Path to the video file
        num_frames (int): Number of frames to extract
        
    Returns:
        list: List of paths to extracted frame images
    """
    if not VIDEO_SUPPORT:
        return []
    
    frames = []
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            return []
        
        # Calculate frame intervals
        interval = max(1, total_frames // num_frames)
        frame_positions = [i * interval for i in range(num_frames)]
        
        for pos in frame_positions:
            if pos >= total_frames:
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_path = temp_file.name
                temp_file.close()
                cv2.imwrite(temp_path, frame)
                frames.append(temp_path)
        
        cap.release()
        return frames
        
    except Exception as e:
        print(f"Error extracting video frames: {str(e)}")
        return []


def extract_single_frame(video_path, frame_number=0):
    """Extract a single frame from a video file."""
    if not VIDEO_SUPPORT:
        return None
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_number >= total_frames:
            frame_number = 0
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_path = temp_file.name
        temp_file.close()
        cv2.imwrite(temp_path, frame)
        return temp_path
        
    except Exception as e:
        print(f"Error extracting video frame: {str(e)}")
        return None


def encode_image(image_path):
    """Load and encode an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_mime_type(file_path):
    """Determine the MIME type based on file extension."""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def analyze_vehicle_damage(file_path, is_video=False, multi_frame=False, damage_hints=None):
    """
    Analyze a vehicle image or video for damage assessment.
    
    Args:
        file_path (str): Path to the image or video file
        is_video (bool): Whether the file is a video
        multi_frame (bool): For videos, analyze multiple frames
        damage_hints (list): Optional list of damaged parts/areas from estimation document.
                            If provided, helps guide the model to focus on these specific areas.
        
    Returns:
        Tuple of (report_text, annotated_image_path, damages_list)
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found.", None, []
    
    temp_frames = []
    annotated_path = None
    
    if damage_hints:
        print(f"[Damage Detection] Received {len(damage_hints)} damage hints from estimation document")
    
    try:
        if is_video:
            if not VIDEO_SUPPORT:
                return "Error: Video support not available. Install opencv-python: pip install opencv-python", None, []
            
            if multi_frame:
                print("Extracting multiple frames from video for comprehensive analysis...")
                temp_frames = extract_video_frames(file_path, num_frames=5)
                if not temp_frames:
                    return "Error: Could not extract frames from video.", None, []
                
                # Analyze multiple frames and combine results
                all_analyses = []
                for i, frame_path in enumerate(temp_frames):
                    print(f"  Analyzing frame {i+1}/{len(temp_frames)}...")
                    analysis, _, _ = _analyze_single_image(frame_path, highlight_damage=False, damage_hints=damage_hints)
                    all_analyses.append(f"### Frame {i+1} Analysis:\n{analysis}")
                
                combined = "\n\n" + "="*70 + "\n\n".join(all_analyses)
                return f"MULTI-FRAME VIDEO ANALYSIS\n{'='*70}\n{combined}", None, []
            else:
                print("Extracting frame from video...")
                frame_path = extract_single_frame(file_path, 0)
                if not frame_path:
                    return "Error: Could not extract frame from video.", None, []
                temp_frames.append(frame_path)
                report, annotated_path, damages_list = _analyze_single_image(frame_path, damage_hints=damage_hints)
                return report, annotated_path, damages_list
        else:
            report, annotated_path, damages_list = _analyze_single_image(file_path, damage_hints=damage_hints)
            return report, annotated_path, damages_list
            
    finally:
        # Clean up temporary files
        for temp_path in temp_frames:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass


def draw_damage_boxes(image_path, damages, output_path=None):
    """
    Draw rectangular boxes around detected damage areas on the image.
    
    Args:
        image_path: Path to the original image
        damages: List of damage dictionaries with bounding box info
        output_path: Path to save annotated image (optional)
    
    Returns:
        Path to the annotated image
    """
    if not VIDEO_SUPPORT:
        print("Warning: OpenCV not available. Cannot draw damage boxes.")
        return None
    
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        height, width = img.shape[:2]
        
        # Colors for different severity levels (BGR format)
        colors = {
            'severe': (0, 0, 255),      # Red
            'moderate': (0, 165, 255),  # Orange
            'minor': (0, 255, 255),     # Yellow
            'default': (0, 255, 0)      # Green
        }
        
        # Create overlay for semi-transparent boxes
        overlay = img.copy()
        
        for i, damage in enumerate(damages):
            box = damage.get('box', {})
            
            # Convert percentages to pixel coordinates
            x = float(box.get('x_percent', 0)) * width / 100
            y = float(box.get('y_percent', 0)) * height / 100
            w = float(box.get('width_percent', 10)) * width / 100
            h = float(box.get('height_percent', 10)) * height / 100
            
            # Ensure minimum box size (at least 30 pixels for better visibility)
            min_pixels = 30
            if w < min_pixels:
                # Expand width while keeping center
                expansion = (min_pixels - w) / 2
                x = max(0, x - expansion)
                w = min(width - x, min_pixels)
            if h < min_pixels:
                # Expand height while keeping center
                expansion = (min_pixels - h) / 2
                y = max(0, y - expansion)
                h = min(height - y, min_pixels)
            
            # Convert to integers after all calculations
            x = int(x)
            y = int(y)
            w = int(w)
            h = int(h)
            
            # Ensure box stays within image bounds
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = min(w, width - x)
            h = min(h, height - y)
            
            # Get color based on severity
            extent = damage.get('extent', 'default').lower()
            color = colors.get(extent, colors['default'])
            
            # Draw semi-transparent filled rectangle
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
            
            # Draw thick border rectangle
            thickness = max(2, int(min(width, height) / 200))  # Scale thickness with image size
            cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness)
            
            # Draw corner brackets for emphasis
            corner_len = min(20, w // 4, h // 4)
            # Top-left corner
            cv2.line(img, (x, y), (x + corner_len, y), color, thickness + 2)
            cv2.line(img, (x, y), (x, y + corner_len), color, thickness + 2)
            # Top-right corner
            cv2.line(img, (x + w, y), (x + w - corner_len, y), color, thickness + 2)
            cv2.line(img, (x + w, y), (x + w, y + corner_len), color, thickness + 2)
            # Bottom-left corner
            cv2.line(img, (x, y + h), (x + corner_len, y + h), color, thickness + 2)
            cv2.line(img, (x, y + h), (x, y + h - corner_len), color, thickness + 2)
            # Bottom-right corner
            cv2.line(img, (x + w, y + h), (x + w - corner_len, y + h), color, thickness + 2)
            cv2.line(img, (x + w, y + h), (x + w, y + h - corner_len), color, thickness + 2)
            
            # Create label
            label = damage.get('label', f'Damage {i+1}')
            extent_text = damage.get('extent', '')
            full_label = f"{i+1}. {label} ({extent_text})" if extent_text else f"{i+1}. {label}"
            
            # Draw label with background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.5, min(width, height) / 1500)  # Scale font with image
            label_thickness = max(1, int(font_scale * 2))
            (text_width, text_height), baseline = cv2.getTextSize(full_label, font, font_scale, label_thickness)
            
            # Position label above the box (or below if too close to top)
            if y > text_height + 15:
                label_y = y - 8
                label_bg_y1 = label_y - text_height - 8
                label_bg_y2 = label_y + 5
            else:
                label_y = y + h + text_height + 5
                label_bg_y1 = y + h + 2
                label_bg_y2 = label_y + 8
            
            # Draw label background (black with colored border)
            cv2.rectangle(img, (x - 2, label_bg_y1), (x + text_width + 8, label_bg_y2), (0, 0, 0), -1)
            cv2.rectangle(img, (x - 2, label_bg_y1), (x + text_width + 8, label_bg_y2), color, 2)
            cv2.putText(img, full_label, (x + 2, label_y), font, font_scale, (255, 255, 255), label_thickness)
        
        # Blend the overlay with original image for semi-transparent effect
        alpha = 0.15  # Transparency level
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        # Generate output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(image_path).stem
            output_dir = Path(image_path).parent
            output_path = str(output_dir / f"{base_name}_annotated_{timestamp}.jpg")
        
        # Save annotated image with high quality
        cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return output_path
        
    except Exception as e:
        print(f"Error drawing damage boxes: {str(e)}")
        return None


def get_damage_boxes(image_path, damage_hints=None):
    """
    Get bounding box coordinates for damage areas from GPT-4 Vision.
    Includes validation and expansion to ensure complete coverage.
    
    Args:
        image_path: Path to the image file
        damage_hints: Optional list of damaged parts/areas from estimation document.
                     If provided, the model will focus on finding damage in these areas.
    
    Returns:
        List of damage dictionaries with bounding box info
    """
    try:
        image_data = encode_image(image_path)
        mime_type = get_mime_type(image_path)
        
        # Build the prompt - add damage hints if provided
        prompt = BOUNDING_BOX_PROMPT
        
        if damage_hints and len(damage_hints) > 0:
            hints_text = "\n\n" + "=" * 70 + "\n"
            hints_text += "🚨 MANDATORY: DAMAGE AREAS FROM INSURANCE ESTIMATION DOCUMENT\n"
            hints_text += "=" * 70 + "\n"
            hints_text += "The insurance estimation document has identified these SPECIFIC damaged parts.\n"
            hints_text += "You MUST create a bounding box for EACH of these areas:\n\n"
            
            for i, hint in enumerate(damage_hints, 1):
                if isinstance(hint, dict):
                    part = hint.get('part', hint.get('description', str(hint)))
                    damage_type = hint.get('type', hint.get('damage_type', ''))
                    if damage_type:
                        hints_text += f"  📍 REQUIRED BOX {i}: {part} ({damage_type})\n"
                    else:
                        hints_text += f"  📍 REQUIRED BOX {i}: {part}\n"
                else:
                    hints_text += f"  📍 REQUIRED BOX {i}: {hint}\n"
            
            hints_text += "\n" + "⚠️" * 10 + " CRITICAL REQUIREMENTS " + "⚠️" * 10 + "\n"
            hints_text += "1. CREATE A BOUNDING BOX FOR EACH ITEM LISTED ABOVE - This is MANDATORY\n"
            hints_text += "2. The 'location' field in your JSON MUST use the EXACT part name from the document\n"
            hints_text += "   - If document says 'FRONT LHS - BUFFER', use 'FRONT LHS - BUFFER' as location\n"
            hints_text += "   - If document says 'Front Bumper', use 'Front Bumper' as location\n"
            hints_text += "3. 'Buffer' = 'Bumper' (same part, different terminology)\n"
            hints_text += "4. 'LHS' = Left Hand Side, 'RHS' = Right Hand Side\n"
            hints_text += "5. Look at the FRONT BUMPER area specifically if 'buffer' is mentioned\n"
            hints_text += "6. You may also detect additional damages visible but not in the document\n"
            hints_text += "7. MINIMUM BOXES: You must return at least " + str(len(damage_hints)) + " boxes\n"
            hints_text += "=" * 70 + "\n"
            
            prompt = prompt + hints_text
            print(f"[Damage Detection] Using {len(damage_hints)} damage hints from estimation document")
            for hint in damage_hints:
                if isinstance(hint, dict):
                    print(f"  - {hint.get('part', hint.get('description', str(hint)))}")
                else:
                    print(f"  - {hint}")
        
        # Use optimized parameters for maximum accuracy in damage detection
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": IMAGE_DETAIL
                            }
                        }
                    ]
                }
            ],
            max_tokens=MAX_TOKENS_BOXES,
            temperature=TEMPERATURE,
            top_p=TOP_P
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        # Parse JSON
        data = json.loads(response_text)
        damages = data.get('damages', [])
        
        # Validate and expand boxes to ensure complete coverage
        validated_damages = []
        for damage in damages:
            box = damage.get('box', {})
            x = float(box.get('x_percent', 0))
            y = float(box.get('y_percent', 0))
            w = float(box.get('width_percent', 0))
            h = float(box.get('height_percent', 0))
            
            # Ensure minimum size (at least 3% of image dimension)
            min_size = 3.0
            if w < min_size:
                # Expand width while keeping center
                expansion = (min_size - w) / 2
                x = max(0, x - expansion)
                w = min(100 - x, min_size)
            if h < min_size:
                # Expand height while keeping center
                expansion = (min_size - h) / 2
                y = max(0, y - expansion)
                h = min(100 - y, min_size)
            
            # Add additional safety margin (2% on each side)
            margin = 2.0
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(100 - x, w + (margin * 2))
            h = min(100 - y, h + (margin * 2))
            
            # Ensure box stays within bounds
            if x + w > 100:
                w = 100 - x
            if y + h > 100:
                h = 100 - y
            
            # Update the box with validated coordinates
            damage['box'] = {
                'x_percent': round(x, 2),
                'y_percent': round(y, 2),
                'width_percent': round(w, 2),
                'height_percent': round(h, 2)
            }
            
            validated_damages.append(damage)
        
        return validated_damages
        
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse damage coordinates: {e}")
        try:
            print(f"Response was: {response_text[:200]}...")
        except:
            pass
        return []
    except Exception as e:
        print(f"Warning: Could not get damage boxes: {e}")
        return []


def _analyze_single_image(image_path, highlight_damage=True, damage_hints=None):
    """
    Analyze a single image for vehicle damage.
    
    Args:
        image_path: Path to the image file
        highlight_damage: Whether to create annotated image with damage boxes
        damage_hints: Optional list of damaged parts/areas from estimation document
    
    Returns:
        Tuple of (report_text, annotated_image_path, damages_list) where damages_list contains structured damage data
    """
    annotated_path = None
    damages_list = []
    
    try:
        image_data = encode_image(image_path)
        mime_type = get_mime_type(image_path)
        
        # Get damage boxes FIRST - this will be our source of truth for damage count and details
        if highlight_damage and VIDEO_SUPPORT:
            print("Detecting damage locations and details...")
            damages_list = get_damage_boxes(image_path, damage_hints=damage_hints)
            
            if damages_list:
                print(f"Found {len(damages_list)} damage area(s). Creating annotated image...")
                annotated_path = draw_damage_boxes(image_path, damages_list)
                if annotated_path:
                    print(f"Annotated image saved: {annotated_path}")
            else:
                print("No damage areas detected.")
        
        # Generate text report - either from bounding boxes (for consistency) or from prompt
        if damages_list and len(damages_list) > 0:
            # Generate report FROM the bounding box results for consistency
            report = "DAMAGE FOUND: Yes\n\n"
            for i, damage in enumerate(damages_list, 1):
                report += "---\n"
                report += f"DAMAGE {i}:\n"
                report += f"- Location: {damage.get('location', 'Not specified')}\n"
                report += f"- Type: {damage.get('label', 'Unknown')}\n"
                report += f"- Extent: {damage.get('extent', 'Unknown')}\n"
            report += "---"
        else:
            # Fallback: Get text report from separate API call
            # Include damage hints if available for consistency
            text_prompt = SIMPLE_DAMAGE_PROMPT
            if damage_hints and len(damage_hints) > 0:
                hints_text = "\n\nIMPORTANT: The insurance document mentions these damaged areas:\n"
                for hint in damage_hints:
                    if isinstance(hint, dict):
                        part = hint.get('part', hint.get('description', str(hint)))
                        hints_text += f"- {part}\n"
                    else:
                        hints_text += f"- {hint}\n"
                hints_text += "\nFocus on identifying damage in these specific areas."
                text_prompt = text_prompt + hints_text
            
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": text_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}",
                                    "detail": IMAGE_DETAIL
                                }
                            }
                        ]
                    }
                ],
                max_tokens=MAX_TOKENS_REPORT,
                temperature=TEMPERATURE,
                top_p=TOP_P
            )
            
            report = response.choices[0].message.content
        
        return report, annotated_path, damages_list
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        if "Invalid API key" in error_msg or "Incorrect API key" in error_msg:
            return "Error: Invalid API key. Please check your OPENAI_API_KEY environment variable.", None, []
        elif "Rate limit" in error_msg:
            return "Error: Rate limit exceeded. Please wait a moment and try again.", None, []
        elif "quota" in error_msg.lower():
            return "Error: Insufficient API quota. Please check your OpenAI account billing.", None, []
        elif "Connection" in error_msg or "connection" in error_msg or "APIConnectionError" in error_type:
            return f"""Error: Connection failed to OpenAI API.

POSSIBLE CAUSES:
1. No internet connection - Check your network
2. Firewall blocking - Allow Python/OpenAI through firewall
3. VPN/Proxy issues - Try disabling VPN or configure proxy
4. OpenAI service down - Check https://status.openai.com

Technical details: {error_type}: {error_msg}""", None, []
        elif "timeout" in error_msg.lower():
            return "Error: Connection timed out. Try again in a few moments.", None, []
        else:
            return f"Error analyzing image: {error_type}: {error_msg}", None, []


def open_file_picker():
    """Open a file picker dialog to select an image or video file."""
    if not FILE_PICKER_AVAILABLE:
        return None
    
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Select Vehicle Image or Video",
            filetypes=[
                ("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
                ("Video Files", "*.mp4;*.avi;*.mov;*.mkv;*.wmv"),
                ("All Files", "*.*")
            ]
        )
        root.destroy()
        return file_path
    except Exception as e:
        return None


def is_video_file(file_path):
    """Check if a file is a video based on its extension."""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    return Path(file_path).suffix.lower() in video_extensions


def generate_report_header():
    """Generate a simple report header."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"""
{'='*60}
  VEHICLE DAMAGE DETECTION
{'='*60}
  Time: {timestamp}
{'='*60}
"""
    return header


def save_report(content, output_path=None):
    """Save the assessment report to a file."""
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"damage_report_{timestamp}.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path


def main():
    """Main function for the Vehicle Damage Detection System."""
    parser = argparse.ArgumentParser(
        description='Vehicle Damage Detection System for Insurance Assessment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python openai_gpt_vision.py image.jpg
  python openai_gpt_vision.py video.mp4 --multi-frame
  python openai_gpt_vision.py --save-report image.jpg
        """
    )
    parser.add_argument('file', nargs='?', help='Path to image or video file')
    parser.add_argument('--multi-frame', action='store_true', 
                        help='Analyze multiple frames from video')
    parser.add_argument('--save-report', action='store_true',
                        help='Save the assessment report to a file')
    
    args = parser.parse_args()
    
    print(generate_report_header())
    
    # If file provided via command line
    if args.file:
        file_path = args.file
        is_video = is_video_file(file_path)
        
        print(f"  File: {file_path}")
        print(f"  Type: {'Video' if is_video else 'Image'}")
        print("="*60)
        print("\nAnalyzing vehicle for damage...\n")
        
        result, annotated_path, damages_list = analyze_vehicle_damage(file_path, is_video=is_video, 
                                        multi_frame=args.multi_frame)
        print(result)
        
        if annotated_path:
            print(f"\n** Annotated image with damage highlights: {annotated_path}")
        
        if args.save_report:
            full_report = generate_report_header() + f"\nFile: {file_path}\n\n" + result
            report_path = save_report(full_report)
            print(f"\n{'='*60}")
            print(f"Report saved to: {report_path}")
        
        print("="*60)
        return
    
    # Interactive mode
    print("  Mode: Interactive")
    print("="*70)
    
    while True:
        print("\n" + "-"*50)
        print("OPTIONS:")
        print("-"*50)
        print("  1. Enter file path manually")
        if FILE_PICKER_AVAILABLE:
            print("  2. Browse for file")
        print("  3. Exit")
        print("-"*50)
        
        try:
            choice = input("\nSelect option: ").strip()
            
            if choice == "3":
                print("\nThank you for using the Vehicle Damage Detection System.")
                break
            
            file_path = None
            
            if choice == "1":
                file_path = input("\nEnter file path: ").strip().strip('"').strip("'")
                if not file_path:
                    print("No file path entered.")
                    continue
                    
            elif choice == "2" and FILE_PICKER_AVAILABLE:
                print("\nOpening file browser...")
                file_path = open_file_picker()
                if not file_path:
                    print("No file selected.")
                    continue
                print(f"Selected: {file_path}")
            else:
                print("Invalid option.")
                continue
            
            is_video = is_video_file(file_path)
            multi_frame = False
            
            if is_video and VIDEO_SUPPORT:
                mf_choice = input("\nAnalyze multiple frames? (y/n, default: n): ").strip().lower()
                multi_frame = mf_choice == 'y'
            
            print("\n" + "="*60)
            print("ANALYZING VEHICLE...")
            print("="*60 + "\n")
            
            result, annotated_path, damages_list = analyze_vehicle_damage(file_path, is_video=is_video, 
                                           multi_frame=multi_frame)
            print(result)
            
            if annotated_path:
                print(f"\n** Annotated image with damage highlights saved to:")
                print(f"   {annotated_path}")
            
            # Option to save report
            save_choice = input("\n\nSave report to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                full_report = generate_report_header() + f"\nFile: {file_path}\n\n" + result
                if annotated_path:
                    full_report += f"\n\nAnnotated image: {annotated_path}"
                report_path = save_report(full_report)
                print(f"Report saved to: {report_path}")
            
            print("="*60)
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
