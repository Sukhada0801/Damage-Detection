# dummy_database.py
"""
Vehicle Repair Cost Database
Loads repair cost estimates from JSON file for easy maintenance and updates.
"""

import json
import os
from pathlib import Path

# Path to the JSON database file
_DB_FILE = Path(__file__).parent / "dummy_indian_vehicle_repair_estimates.json"

def _load_database():
    """Load the database from JSON file."""
    try:
        if _DB_FILE.exists():
            with open(_DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # New file is a flat list, return as-is
                return data if isinstance(data, list) else []
        else:
            # Return empty list if file doesn't exist yet
            print(f"Warning: Database file not found at {_DB_FILE}. Using empty database.")
            return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in database file: {e}")
        return []
    except Exception as e:
        print(f"Error loading database: {e}")
        return []

# Load the database
data = _load_database()

# Export for backward compatibility
dummy_data = data
dummy_db = data


def get_repair_cost(make, model, year, damage_type, severity=None, variant=None):
    """
    Get repair cost estimate from JSON database.
    
    Args:
        make: Vehicle make/brand (e.g., "Toyota")
        model: Vehicle model (e.g., "Innova Crysta")
        year: Vehicle year (e.g., 2020)
        damage_type: Type of damage (e.g., "scratch", "dent", "broken_headlight")
        severity: Severity level (optional - new database doesn't use severity, kept for compatibility)
        variant: Vehicle variant (optional - will try to match if provided)
    
    Returns:
        Estimated cost in INR if match found, None otherwise
    """
    if not data or not isinstance(data, list):
        print("DEBUG: Database not loaded or empty")
        return None
    
    # Normalize damage_type to match JSON format
    normalized_damage = _normalize_damage_type_for_lookup(damage_type)
    
    if not normalized_damage:
        print(f"DEBUG: Could not normalize damage type: {damage_type}")
        return None
    
    print(f"DEBUG: Searching for {make} {model} {year} (variant: {variant}) - {normalized_damage}")
    
    # Try exact match first (with variant if provided)
    for entry in data:
        brand_match = entry.get("Brand", "").lower() == make.lower()
        model_match = entry.get("Model", "").lower() == model.lower()
        year_match = entry.get("Year") == year
        damage_match = entry.get("DamageType", "").lower() == normalized_damage.lower()
        variant_match = True  # Default to True if variant not provided
        
        if variant:
            variant_match = entry.get("Variant", "").lower() == variant.lower()
        
        if brand_match and model_match and year_match and damage_match and variant_match:
            cost = entry.get("EstimatedRepairCost")
            if cost is not None:
                print(f"DEBUG: Found cost ₹{cost} for {make} {model} {year} - {normalized_damage}")
                return cost
    
    # If variant was provided but no match, try without variant
    if variant:
        print(f"DEBUG: No match with variant '{variant}', trying without variant...")
        for entry in data:
            if (
                entry.get("Brand", "").lower() == make.lower() and
                entry.get("Model", "").lower() == model.lower() and
                entry.get("Year") == year and
                entry.get("DamageType", "").lower() == normalized_damage.lower()
            ):
                cost = entry.get("EstimatedRepairCost")
                if cost is not None:
                    print(f"DEBUG: Found cost ₹{cost} for {make} {model} {year} - {normalized_damage} (any variant)")
                    return cost
    
    print(f"DEBUG: No cost found for {make} {model} {year} - {normalized_damage}")
    return None


def _normalize_damage_type_for_lookup(damage_type):
    """
    Normalize damage type to match the format in dummy_indian_vehicle_repair_estimates.json.
    The JSON uses formats like: "Scratch", "Dent", "Broken windshield", "Headlight damage", etc.
    """
    if not damage_type:
        return None
    
    damage_lower = damage_type.lower().strip()
    
    # Direct mappings to JSON format
    format_mappings = {
        "scratch": "Scratch",
        "scratches": "Scratch",
        "scraches": "Scratch",  # Handle typo
        "paint chips": "Scratch",
        "paint_chips": "Scratch",
        "paint chip": "Scratch",
        "paint_chip": "Scratch",
        "paint damage": "Scratch",
        "paint_damage": "Scratch",
        "dent": "Dent",
        "dents": "Dent",
        "broken_headlight": "Headlight damage",
        "broken headlight": "Headlight damage",
        "headlight damage": "Headlight damage",
        "headlight": "Headlight damage",
        "headlights": "Headlight damage",
        "broken_windshield": "Broken windshield",
        "broken windshield": "Broken windshield",
        "windshield": "Broken windshield",
        "windshield crack": "Broken windshield",
        "windshield_crack": "Broken windshield",
        "bumper_damage": "Bumper crack",
        "bumper damage": "Bumper crack",
        "bumper crack": "Bumper crack",
        "bumper": "Bumper crack",
        "door_damage": "Door damage",
        "door damage": "Door damage",
        "door": "Door damage",
        "broken_side_mirror": "Broken side mirror",
        "broken side mirror": "Broken side mirror",
        "side mirror": "Broken side mirror",
        "mirror": "Broken side mirror"
    }
    
    # Try exact match first
    if damage_lower in format_mappings:
        return format_mappings[damage_lower]
    
    # Try partial matching
    if "headlight" in damage_lower:
        return "Headlight damage"
    elif "windshield" in damage_lower or "wind_screen" in damage_lower or "wind screen" in damage_lower:
        return "Broken windshield"
    elif "bumper" in damage_lower:
        return "Bumper crack"
    elif "door" in damage_lower:
        return "Door damage"
    elif "mirror" in damage_lower or "side_mirror" in damage_lower or "side mirror" in damage_lower:
        return "Broken side mirror"
    elif "scratch" in damage_lower or "paint" in damage_lower:
        return "Scratch"
    elif "dent" in damage_lower:
        return "Dent"
    
    # Return title case version as fallback
    return damage_type.title()


def _normalize_damage_type(damage_type):
    """Normalize damage type to match JSON keys (lowercase with underscores)."""
    if not damage_type:
        return None
    # Convert to lowercase and replace spaces/hyphens with underscores
    normalized = damage_type.lower().strip().replace(" ", "_").replace("-", "_")
    
    # Handle common variations and typos - check both exact matches and contains
    mappings = {
        "scratch": "scratch",
        "scratches": "scratch",
        "scraches": "scratch",  # Handle typo "Scraches"
        "scrach": "scratch",  # Handle typo
        "scrachs": "scratch",  # Handle typo
        "paint_chips": "scratch",  # Paint chips are similar to scratches
        "paint_chip": "scratch",
        "paint chips": "scratch",
        "paint chip": "scratch",
        "paint_damage": "scratch",  # General paint damage
        "paint_damages": "scratch",
        "paint": "scratch",  # General paint issues
        "dent": "dent",
        "dents": "dent",
        "broken_headlight": "broken_headlight",
        "broken_headlights": "broken_headlight",
        "broken headlight": "broken_headlight",
        "headlight": "broken_headlight",
        "headlights": "broken_headlight",
        "broken_windshield": "broken_windshield",
        "broken windshield": "broken_windshield",
        "windshield": "broken_windshield",
        "windshield_crack": "broken_windshield",
        "windshield_cracks": "broken_windshield",
        "crack": "broken_windshield",  # If just "crack", assume windshield
        "bumper_damage": "bumper_damage",
        "bumper": "bumper_damage",
        "bumpers": "bumper_damage",
        "door_damage": "door_damage",
        "door": "door_damage",
        "doors": "door_damage"
    }
    
    # First try exact match
    if normalized in mappings:
        return mappings[normalized]
    
    # Then try fuzzy matching - check if normalized contains any key or vice versa
    for key, value in mappings.items():
        if key in normalized or normalized in key:
            return value
    
    # Try matching by checking if it starts with common damage type prefixes or contains keywords
    if normalized.startswith("scrat") or "paint" in normalized:
        return "scratch"  # Paint chips and paint damage map to scratch
    elif normalized.startswith("dent"):
        return "dent"
    elif "headlight" in normalized or "head_light" in normalized:
        return "broken_headlight"
    elif "windshield" in normalized or "wind_screen" in normalized:
        return "broken_windshield"
    elif "bumper" in normalized:
        return "bumper_damage"
    elif "door" in normalized:
        return "door_damage"
    
    # Return normalized version if no match found
    return normalized


def _normalize_severity(severity):
    """Normalize severity to match JSON keys (minor, moderate, major)."""
    if not severity:
        return None
    severity_lower = severity.lower()
    # Map common variations
    mappings = {
        "minor": "minor",
        "moderate": "moderate",
        "severe": "major",  # Map "severe" to "major"
        "major": "major"
    }
    return mappings.get(severity_lower, severity_lower)


def get_estimate(make, year, variant, defect_type, severity=None):
    """
    Get repair cost estimate based on vehicle make, year, variant, defect type, and severity.
    This function provides backward compatibility with the old interface.
    
    Args:
        make: Vehicle make/brand (e.g., "Toyota")
        year: Vehicle year (e.g., 2020)
        variant: Vehicle model name (e.g., "Innova Crysta") - this maps to "Model" in the new JSON
        defect_type: Type of damage (e.g., "Scratch", "Dent", "Broken Headlight", "Paint chips")
        severity: Severity level (optional - new database doesn't use severity, kept for compatibility)
    
    Returns:
        Estimated cost in INR if match found, None otherwise
    """
    print(f"DEBUG: get_estimate called with: make='{make}', year={year}, variant='{variant}', defect_type='{defect_type}', severity='{severity}'")
    
    # Note: In the new JSON structure:
    # - Brand = make
    # - Model = variant (from frontend, which is actually the model name)
    # - Year = year
    # - Variant in JSON = variant trim level (Base, Mid, etc.) - we don't have this from frontend, so we'll match without it
    
    return get_repair_cost(make, variant, year, defect_type, severity=severity, variant=None)


def get_repair_estimate(make, defect_type, severity):
    """
    Legacy function for backward compatibility.
    Note: This function doesn't use year/model, so it may return incorrect results.
    Consider using get_estimate() or get_repair_cost() instead.
    """
    # Try to find a match (will use first car found with matching make)
    normalized_damage_type = _normalize_damage_type(defect_type)
    normalized_severity = _normalize_severity(severity)
    
    if not normalized_damage_type or not normalized_severity:
        # default estimation logic
        default_costs = {
            "minor": 1000,
            "moderate": 3000,
            "major": 8000,
            "severe": 8000
        }
        return default_costs.get(normalized_severity or severity.lower(), "No Estimate Found")
    
    # Try to find any car with matching make
    for car in data["cars"]:
        if car["make"].lower() == make.lower():
            try:
                return car["damage"][normalized_damage_type][normalized_severity]
            except KeyError:
                continue
    
    # default estimation logic
    default_costs = {
        "minor": 1000,
        "moderate": 3000,
        "major": 8000,
        "severe": 8000
    }
    return default_costs.get(normalized_severity, "No Estimate Found")
