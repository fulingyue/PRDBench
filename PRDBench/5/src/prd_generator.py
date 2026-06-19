"""PRD Document Generation Module - generates Markdown PRD documents."""

import os
import datetime


def generate_prd(template_data, image_features_list, processed_image_paths, style_description, output_name=None):
    """Generate a PRD document in Markdown format.

    Args:
        template_data: Template dictionary
        image_features_list: List of feature dictionaries per image
        processed_image_paths: List of processed image file paths
        style_description: Generated style description text
        output_name: Optional name for the output file

    Returns:
        str: Path to the generated PRD document
    """
    src_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(src_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    if output_name:
        filename = f"{output_name}.md"
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PRD_{timestamp}.md"

    output_path = os.path.join(output_dir, filename)

    basic_info = template_data.get('basic_info', {})
    image_spec = template_data.get('image_spec', {})
    feature_req = template_data.get('feature_requirements', {})

    lines = []
    lines.append("# Product Requirements Document (PRD)")
    lines.append("")

    # 1. Product Overview
    lines.append("## 1. Product Overview")
    lines.append(f"- **Product Name**: {basic_info.get('product_name', 'N/A')}")
    lines.append(f"- **Target Users**: {basic_info.get('target_users', 'N/A')}")
    lines.append("")

    # 2. Image Resource Specifications
    lines.append("## 2. Image Resource Specifications")
    lines.append(f"- **Source Type**: {image_spec.get('source_type', 'local_path')}")
    allowed = image_spec.get('allowed_formats', [])
    lines.append(f"- **Allowed File Types**: {', '.join(allowed)}")
    lines.append("- **Processed Image Paths**:")
    for path in processed_image_paths:
        lines.append(f"  - {path}")
    lines.append("")

    # 3. Core Feature Description
    lines.append("## 3. Core Feature Description")
    for i, features in enumerate(image_features_list, 1):
        lines.append(f"### Image {i} Features")
        lines.append("- **Dominant Colors**:")
        for color, pct in features.get('dominant_colors', []):
            lines.append(f"  - {color} ({pct:.2f}%)")
        lines.append(f"- **Texture Feature**: {features.get('texture', 'N/A')}")
        lines.append("")

    lines.append("### Visual Style Description")
    lines.append(style_description)
    lines.append("")

    # 4. Development Schedule Suggestions (CPM)
    lines.append("## 4. Development Schedule Suggestions")
    lines.append("- **Image Processing**: Format conversion, metadata cleanup (Estimated time: 5 minutes)")
    lines.append("- **Feature Extraction**: Dominant color analysis, texture feature extraction (Estimated time: 10 minutes)")
    lines.append("- **Document Generation**: Integrate information, generate PRD document (Estimated time: 3 minutes)")
    lines.append("")
    lines.append("- **Total Duration**: Estimated 18 minutes")

    content = "\n".join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_path
