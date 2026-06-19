# Product Requirements Template and Auto-Generation Tool

## Introduction

This tool is a command-line application designed to help product teams quickly generate standardized Product Requirements Documents (PRD) through structured templates and automated processing workflows. The tool integrates image processing, feature extraction, and document generation capabilities, significantly improving the efficiency and quality of product documentation.

## Environment Setup

### System Requirements

- Python 3.7 or higher
- Windows, macOS, or Linux operating system

### Installing Dependencies

1. Clone or download the project to a local directory
2. Open a terminal or command prompt and navigate to the project root directory
3. Run the following command to install dependencies:

```bash
pip install -r src/requirements.txt
```

### Dependency Description

- `opencv-python`: For image processing and computer vision features
- `Pillow`: For image processing and metadata cleaning
- `scikit-learn`: For K-means clustering in dominant color extraction
- `numpy`: For numerical computations
- `requests`: For network requests (calling large language model APIs)

## Startup Commands

Run the following command in the project root directory to start the tool:

```bash
python src/main.py
```

## Main Features

After starting, the tool displays a main menu with the following options:

1. **Create/Edit Requirement Template** - Define product templates with basic info, image specs, and style requirements
2. **Generate Product PRD Based on Template** - Process images, extract features, and generate PRD documents
3. **Exit Tool** - Safely exit the program

## Output Files

- Generated PRD documents: `src/output/` directory (Markdown format)
- Processed images: `src/images/` directory
- Template files: `src/templates/` directory (JSON format)
