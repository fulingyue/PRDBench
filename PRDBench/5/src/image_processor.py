"""Image Resource Processing Module - handles validation, preprocessing, and metadata cleaning."""

import os
import struct
from PIL import Image


# File header magic bytes for image format validation
IMAGE_SIGNATURES = {
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'webp': [b'RIFF'],
}


def validate_image_path(path):
    """Validate that the image path exists."""
    return os.path.exists(path)


def get_actual_image_type(file_path):
    """Detect actual image type by reading file header bytes."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)
    except (IOError, OSError):
        return None

    # Check JPEG
    if header[:3] == b'\xff\xd8\xff':
        return 'jpeg'

    # Check PNG
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'

    # Check WebP (RIFF....WEBP)
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'webp'

    return None


def validate_image_format(file_path, allowed_formats):
    """Validate image format by reading file header bytes.

    Args:
        file_path: Path to the image file
        allowed_formats: List of allowed format strings (e.g., ['jpg', 'jpeg', 'png', 'webp'])

    Returns:
        tuple: (is_valid, actual_type)
    """
    actual_type = get_actual_image_type(file_path)
    if actual_type is None:
        return False, None

    # Normalize format names for comparison
    normalized_allowed = set()
    for fmt in allowed_formats:
        fmt_lower = fmt.lower()
        normalized_allowed.add(fmt_lower)
        if fmt_lower == 'jpg':
            normalized_allowed.add('jpeg')
        elif fmt_lower == 'jpeg':
            normalized_allowed.add('jpg')

    is_valid = actual_type.lower() in normalized_allowed
    return is_valid, actual_type


def preprocess_image(image_path, target_format='jpeg'):
    """Preprocess image: format conversion and metadata cleaning.

    Args:
        image_path: Path to the source image
        target_format: Target format to convert to

    Returns:
        str: Path to the processed image
    """
    # Ensure output directory exists
    src_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(src_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    # Open and process image
    with Image.open(image_path) as img:
        # Convert to RGB if necessary (removes alpha channel, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Create a clean copy without EXIF data
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(list(img.getdata()))

        # Determine output filename
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        fmt_lower = target_format.lower()
        if fmt_lower in ('jpg', 'jpeg'):
            ext = '.jpg'
            save_format = 'JPEG'
        elif fmt_lower == 'png':
            ext = '.png'
            save_format = 'PNG'
        elif fmt_lower == 'webp':
            ext = '.webp'
            save_format = 'WEBP'
        else:
            ext = '.jpg'
            save_format = 'JPEG'

        output_path = os.path.join(images_dir, f"{base_name}_processed{ext}")
        clean_img.save(output_path, format=save_format)

    return output_path
