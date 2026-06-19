"""Product Feature Extraction Module - dominant colors, texture, and style description."""

import os
import re
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def rgb_to_hex(r, g, b):
    """Convert RGB values to HEX format."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def extract_dominant_colors(image_path, k=5, top_n=3):
    """Extract dominant colors using K-means clustering.

    Args:
        image_path: Path to the image
        k: Number of clusters for K-means
        top_n: Number of top colors to return

    Returns:
        list: List of tuples (hex_color, percentage)
    """
    img = Image.open(image_path).convert('RGB')
    img_array = np.array(img)
    pixels = img_array.reshape(-1, 3).astype(np.float64)

    if HAS_SKLEARN:
        # Use sklearn KMeans
        kmeans = KMeans(n_clusters=min(k, len(np.unique(pixels, axis=0))), random_state=42, n_init=10)
        kmeans.fit(pixels)
        centers = kmeans.cluster_centers_
        labels = kmeans.labels_

        # Count pixels per cluster
        counts = np.bincount(labels, minlength=len(centers))
        total = len(labels)

        # Sort by count descending
        sorted_indices = np.argsort(-counts)
        results = []
        for i in sorted_indices[:top_n]:
            r, g, b = centers[i]
            hex_color = rgb_to_hex(r, g, b)
            percentage = (counts[i] / total) * 100
            results.append((hex_color, round(percentage, 2)))
        return results
    else:
        # Simplified: use histogram-based approach
        from collections import Counter
        # Quantize colors
        quantized = [(int(r)//32*32, int(g)//32*32, int(b)//32*32) for r, g, b in pixels[:10000]]
        counter = Counter(quantized)
        total = sum(counter.values())
        most_common = counter.most_common(top_n)
        results = []
        for (r, g, b), count in most_common:
            hex_color = rgb_to_hex(r, g, b)
            percentage = (count / total) * 100
            results.append((hex_color, round(percentage, 2)))
        return results


def extract_texture_features(image_path):
    """Extract texture features using LBP (Local Binary Pattern).

    Returns:
        str: 'smooth' or 'rough'
    """
    img = Image.open(image_path).convert('L')
    img_array = np.array(img, dtype=np.float64)

    if HAS_OPENCV:
        # Use Laplacian variance as texture measure
        laplacian = cv2.Laplacian(img_array.astype(np.uint8), cv2.CV_64F)
        variance = laplacian.var()
    else:
        # Simplified LBP-like approach: compute local variance
        # Calculate differences with neighbors
        h, w = img_array.shape
        if h < 3 or w < 3:
            return "smooth"

        # Use pixel differences to estimate texture
        dx = np.abs(np.diff(img_array, axis=1))
        dy = np.abs(np.diff(img_array, axis=0))
        variance = (dx.mean() + dy.mean()) / 2

    # Threshold to classify as smooth or rough
    threshold = 10.0
    if variance < threshold:
        return "smooth"
    else:
        return "rough"


def analyze_image_features(image_path):
    """Analyze all image features.

    Returns:
        dict: Dictionary with 'dominant_colors' and 'texture' keys
    """
    dominant_colors = extract_dominant_colors(image_path)
    texture = extract_texture_features(image_path)
    return {
        'dominant_colors': dominant_colors,
        'texture': texture
    }


def validate_api_key(api_key):
    """Validate OpenAI API key format."""
    pattern = r'^sk-[A-Za-z0-9]{48}$'
    return bool(re.match(pattern, api_key))


def generate_style_description(style_keywords, dominant_colors, texture, api_key):
    """Generate style description using LLM API.

    If api_key is 'skip', returns skip message.
    """
    if api_key.lower() == 'skip':
        return "User chose to skip style description generation."

    try:
        import requests
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        color_info = ", ".join([f"{c[0]} ({c[1]}%)" for c in dominant_colors])
        prompt = (
            f"Based on the following information, generate a product visual style description "
            f"conforming to the AIDA model (Attention-Interest-Desire-Action), limited to 200 words:\n"
            f"Style Keywords: {', '.join(style_keywords)}\n"
            f"Dominant Colors: {color_info}\n"
            f"Texture: {texture}\n"
        )

        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300
        }

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"API call failed (status: {response.status_code}). Style description not generated."
    except Exception as e:
        return f"API call failed: {str(e)}. Style description not generated."
