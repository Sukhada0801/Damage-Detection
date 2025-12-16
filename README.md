# Vehicle Damage Detection System for Insurance Assessment

A Python-based AI application that analyzes vehicle images and videos to automatically detect and assess damage for insurance claim processing. Uses OpenAI's GPT-4 Vision to provide comprehensive damage reports.

## Features

### Damage Detection Categories

#### Geometric (Structural) Damage
- **Side Mirror Damage** - Broken, cracked, missing, or misaligned mirrors
- **Glass Damage** - Shattered, cracked, or chipped windshield/windows
- **Headlight/Taillight Damage** - Broken or cracked lights
- **Dents** - Body panel, door, hood, trunk, roof dents
- **Bumper Damage** - Front/rear bumper cracks, dents, detachment
- **Frame/Body Damage** - Bent panels, structural deformation
- **Wheel/Tire Damage** - Bent rims, wheel well damage

#### Cosmetic Damage
- **Scratches** - Paint scratches, clear coat damage, deep scratches
- **Paint Damage** - Chips, peeling, fading, discoloration
- **Surface Rust** - Visible rust spots or corrosion
- **Minor Abrasions** - Scuffs, surface marks

### Key Capabilities

- **Image Analysis** - Analyze photos of vehicle damage
- **Video Analysis** - Extract and analyze frames from damage videos
- **Multi-Frame Analysis** - Analyze multiple video frames for comprehensive assessment
- **Professional Reports** - Generate detailed insurance assessment reports
- **Report Export** - Save reports to files for documentation
- **Severity Assessment** - Categorize damage as Critical, Major, Minor, or Negligible
- **Repair Priority** - Identify which repairs are most urgent

## Installation

1. Install Python 3.8 or higher

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Setup

1. Get your OpenAI API key from https://platform.openai.com/api-keys

2. Set your API key as an environment variable:

   **Windows (PowerShell):**
   ```powershell
   $env:OPENAI_API_KEY="your-api-key-here"
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   set OPENAI_API_KEY=your-api-key-here
   ```
   
   **Linux/Mac:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Usage

### Command-Line Interface

```bash
# Analyze a single image
python openai_gpt_vision.py "vehicle_damage.jpg"

# Analyze a video (single frame)
python openai_gpt_vision.py "damage_video.mp4"

# Analyze video with multiple frames for thorough assessment
python openai_gpt_vision.py "damage_video.mp4" --multi-frame

# Analyze and save report to file
python openai_gpt_vision.py "vehicle_damage.jpg" --save-report
```

### Interactive Mode

Run without arguments to enter interactive mode:
```bash
python openai_gpt_vision.py
```

Options:
1. Enter file path manually
2. Browse for file (file picker dialog)
3. Exit

## Sample Output

*Example of what the generated report looks like:*

```
======================================================================
         VEHICLE DAMAGE ASSESSMENT REPORT
         Insurance Claim Processing System
======================================================================
  Report Generated: [Current Date & Time]
======================================================================

### DAMAGE ASSESSMENT REPORT

**Overall Condition:** MODERATE

**Damage Summary:**
Vehicle exhibits moderate damage with a significant dent on the rear 
passenger door and multiple scratches along the driver's side panels.

---

**GEOMETRIC (STRUCTURAL) DAMAGE:**

| Component | Damage Type | Severity | Location | Description |
|-----------|-------------|----------|----------|-------------|
| Rear Door | Dent | Major | Right rear passenger door | 15cm diameter dent with paint cracking |
| Side Mirror | Crack | Minor | Left side mirror | Hairline crack on mirror housing |

**COSMETIC DAMAGE:**

| Component | Damage Type | Severity | Location | Description |
|-----------|-------------|----------|----------|-------------|
| Body Panel | Scratches | Minor | Driver's side | Multiple shallow scratches, 30cm length |
| Bumper | Paint Chip | Negligible | Front bumper | Small paint chips near license plate |

---

**REPAIR PRIORITY:**
1. Rear door dent repair (structural integrity concern)
2. Side mirror replacement
3. Paint touch-up for scratches

**ESTIMATED REPAIR COMPLEXITY:**
- Geometric Repairs: Moderate
- Cosmetic Repairs: Simple

**SAFETY CONCERNS:**
None identified - damage is cosmetic and does not affect vehicle operation.
```

## Supported File Formats

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- WebP (.webp)
- GIF (.gif)

### Videos
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WMV (.wmv)
- WebM (.webm)

## For Insurance Companies

This system is designed to:

1. **Streamline Claims Processing** - Automated damage detection reduces manual inspection time
2. **Consistent Assessments** - AI provides standardized damage categorization
3. **Documentation** - Generate professional reports for claim files
4. **Multi-Angle Analysis** - Video support allows comprehensive vehicle inspection
5. **Severity Classification** - Clear damage severity levels for repair estimation

## Requirements

- Python 3.8+
- OpenAI API key with GPT-4 Vision access
- opencv-python (for video support)
- tkinter (for file picker, usually included with Python)

## Troubleshooting

- **API Key Error**: Ensure `OPENAI_API_KEY` environment variable is set correctly
- **Video Support Disabled**: Install opencv-python with `pip install opencv-python`
- **Model Access Error**: Verify your OpenAI account has access to GPT-4o model
- **Rate Limit Error**: Wait a moment and try again, or check your API usage limits

## Security

- API keys should only be stored in environment variables
- Never commit API keys to version control
- The `.gitignore` file is configured to exclude sensitive files

## License

For internal insurance company use.
