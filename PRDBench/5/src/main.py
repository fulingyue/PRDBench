"""Product Requirements Template and Automated Generation Tool - Main Entry Point."""

import os
import sys

from template_manager import (
    COLOR_EMOTION_OPTIONS,
    validate_template,
    save_template,
    load_template,
    list_templates,
    ensure_templates_dir,
)
from image_processor import validate_image_path, validate_image_format, preprocess_image
from feature_extractor import (
    analyze_image_features,
    validate_api_key,
    generate_style_description,
)
from prd_generator import generate_prd


def display_menu():
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("  Product Requirements Template and Auto-Generation Tool")
    print("=" * 50)
    print("  1. Create/Edit Requirement Template")
    print("  2. Generate Product PRD Based on Template")
    print("  3. Exit Tool")
    print("=" * 50)


def get_input(prompt):
    """Get user input with prompt."""
    try:
        return input(prompt)
    except EOFError:
        print("\nEnd of input reached. Exiting.")
        sys.exit(0)


def create_template():
    """Interactive template creation workflow."""
    print("\n--- Create/Edit Requirement Template ---\n")

    # Basic Information
    product_name = get_input("Please enter product name: ").strip()
    if not product_name:
        print("Error: Product name cannot be empty")
        return

    target_users = get_input("Please enter target users: ").strip()
    if not target_users:
        print("Error: Target users cannot be empty")
        return

    # Style Keywords
    keywords_input = get_input("Please enter style keywords (separate multiple with commas): ").strip()
    if not keywords_input:
        print("Error: Style keywords cannot be empty")
        return
    style_keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
    if not style_keywords:
        print("Error: Style keywords cannot be empty")
        return
    print(f"Parsed style keywords: {style_keywords}")

    # Color Emotion Tendency
    print("\nColor Emotion Tendency Options:")
    for key, value in COLOR_EMOTION_OPTIONS.items():
        print(f"  {key}. {value}")
    emotion_choice = get_input("Please select color emotion tendency (1-5): ").strip()
    if emotion_choice not in COLOR_EMOTION_OPTIONS:
        print("Error: Invalid color emotion tendency selection")
        return
    color_emotion = COLOR_EMOTION_OPTIONS[emotion_choice]
    print(f"Selected color emotion tendency: {color_emotion}")

    # Build template data
    template_data = {
        "basic_info": {
            "product_name": product_name,
            "target_users": target_users
        },
        "image_spec": {
            "source_type": "local_path",
            "allowed_formats": ["jpg", "jpeg", "png", "webp"]
        },
        "feature_requirements": {
            "style_keywords": style_keywords,
            "color_emotion": color_emotion
        }
    }

    # Validate template
    is_valid, errors = validate_template(template_data)
    if not is_valid:
        print("Template validation failed:")
        for err in errors:
            print(f"  - {err}")
        return

    # Save template
    template_name = get_input("Please enter template name: ").strip()
    if not template_name:
        print("Error: Template name cannot be empty")
        return

    # Check if template exists
    existing_templates = list_templates()
    overwrite = False
    if template_name in existing_templates:
        confirm = get_input(f"Template '{template_name}' already exists. Overwrite? (y/n): ").strip().lower()
        if confirm == 'y':
            overwrite = True
        else:
            print("Template save cancelled.")
            return

    success, message = save_template(template_data, template_name, overwrite=True)
    if success:
        print(f"Template saved successfully: {template_name}")
    else:
        print(f"Error: {message}")


def generate_prd_workflow():
    """Interactive PRD generation workflow."""
    print("\n--- Generate Product PRD Based on Template ---\n")

    # List and select template
    templates = list_templates()
    if not templates:
        print("Error: No templates found. Please create a template first.")
        return

    print("Available templates:")
    for i, name in enumerate(templates, 1):
        print(f"  {i}. {name}")

    selection = get_input("Please select a template (enter number): ").strip()
    try:
        idx = int(selection) - 1
        if idx < 0 or idx >= len(templates):
            print(f"Error: Template does not exist. Please enter a number between 1 and {len(templates)}.")
            return
    except ValueError:
        print("Error: Please enter a valid number.")
        return

    template_name = templates[idx]
    template_data, error = load_template(template_name)
    if error:
        print(f"Error: {error}")
        return

    print(f"Loaded template: {template_name}")

    # Get image path
    allowed_formats = template_data.get('image_spec', {}).get('allowed_formats', ['jpg', 'jpeg', 'png', 'webp'])
    image_paths = []

    while not image_paths:
        path = get_input("Please enter image path: ").strip()
        if not path:
            print("Error: Image path cannot be empty.")
            continue

        if not validate_image_path(path):
            print(f"Error: Unable to find image in this local path: {path}")
            continue

        is_valid, actual_type = validate_image_format(path, allowed_formats)
        if not is_valid:
            print(f"Error: File type does not meet requirements. Allowed types: {', '.join(allowed_formats)}")
            continue

        image_paths.append(path)
        print(f"Image added: {path} (type: {actual_type})")

    # API Key for style description
    style_keywords = template_data.get('feature_requirements', {}).get('style_keywords', [])
    api_key = get_input("Please enter OpenAI API Key (or 'skip' to skip style description): ").strip()

    if api_key.lower() != 'skip':
        if not validate_api_key(api_key):
            print("Error: API key format incorrect. Must match pattern: sk-[48 alphanumeric characters]")
            # Allow re-entry
            api_key = get_input("Please re-enter API Key (or 'skip' to skip): ").strip()
            if api_key.lower() != 'skip' and not validate_api_key(api_key):
                print("Error: API key format incorrect. Skipping style description.")
                api_key = 'skip'

    # Process images and extract features
    print("\nProcessing images...")
    processed_paths = []
    features_list = []

    for path in image_paths:
        print(f"  Processing: {path}")
        processed_path = preprocess_image(path, 'jpeg')
        processed_paths.append(processed_path)

        features = analyze_image_features(processed_path)
        features_list.append(features)
        print(f"    Dominant colors: {features['dominant_colors']}")
        print(f"    Texture: {features['texture']}")

    # Generate style description
    if features_list:
        style_desc = generate_style_description(
            style_keywords,
            features_list[0]['dominant_colors'],
            features_list[0]['texture'],
            api_key
        )
    else:
        style_desc = "No images processed."

    # Output name
    output_name = get_input("Please enter document name (or press Enter for auto-generated name): ").strip()
    if not output_name:
        output_name = None

    # Generate PRD
    output_path = generate_prd(template_data, features_list, processed_paths, style_desc, output_name)
    print(f"\nDocument generation completed, path: {output_path}")


def main():
    """Main entry point."""
    ensure_templates_dir()

    while True:
        display_menu()
        choice = get_input("Please select an option (1-3): ").strip()

        if choice == '1':
            create_template()
        elif choice == '2':
            generate_prd_workflow()
        elif choice == '3':
            print("Thank you for using the tool. Goodbye!")
            break
        else:
            print("Error: Invalid menu option. Please enter a number between 1 and 3.")


if __name__ == '__main__':
    main()
