"""Template Management Module - creation, validation, and saving of product requirement templates."""

import os
import json


TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

COLOR_EMOTION_OPTIONS = {
    '1': 'Cool Tone-Professional',
    '2': 'Warm Tone-Friendly',
    '3': 'Neutral Tone-Balanced',
    '4': 'Bright Tone-Energetic',
    '5': 'Dark Tone-Luxury'
}


def ensure_templates_dir():
    """Ensure the templates directory exists."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def validate_template(template_data):
    """Validate template data for required fields.

    Returns:
        tuple: (is_valid, list of error messages)
    """
    errors = []

    basic_info = template_data.get('basic_info', {})
    if not basic_info.get('product_name', '').strip():
        errors.append("Product name cannot be empty")
    if not basic_info.get('target_users', '').strip():
        errors.append("Target users cannot be empty")

    feature_req = template_data.get('feature_requirements', {})
    style_keywords = feature_req.get('style_keywords', [])
    if not style_keywords or (len(style_keywords) == 1 and not style_keywords[0].strip()):
        errors.append("Style keywords cannot be empty")

    if not feature_req.get('color_emotion', '').strip():
        errors.append("Color emotion tendency cannot be empty")

    return len(errors) == 0, errors


def save_template(template_data, template_name, overwrite=False):
    """Save template to JSON file.

    Args:
        template_data: Dictionary with template data
        template_name: Name for the template file
        overwrite: Whether to overwrite existing template

    Returns:
        tuple: (success, message)
    """
    ensure_templates_dir()

    file_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if os.path.exists(file_path) and not overwrite:
        return False, f"Template '{template_name}' already exists. Use overwrite option."

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, indent=2, ensure_ascii=False)

    return True, f"Template saved successfully: {file_path}"


def load_template(template_name):
    """Load a template from file.

    Returns:
        tuple: (template_data or None, error_message or None)
    """
    ensure_templates_dir()
    file_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if not os.path.exists(file_path):
        return None, f"Template '{template_name}' does not exist"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError:
        return None, f"Template file '{template_name}' has invalid JSON format"


def list_templates():
    """List all available templates.

    Returns:
        list: List of template names (without .json extension)
    """
    ensure_templates_dir()
    templates = []
    for f in os.listdir(TEMPLATES_DIR):
        if f.endswith('.json'):
            templates.append(f[:-5])
    return sorted(templates)
