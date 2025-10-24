#!/usr/bin/env python3
import os
import shutil
import argparse
import sys

def delete_reports_folders(base_dir, folder_ids=None):
    """
    Delete reports folders in subfolders with specified IDs

    Args:
        base_dir: Base directory path
        folder_ids: List of folder IDs to process, if None then process all IDs

    Returns:
        deleted_count: Number of folders deleted
    """
    # Check if base directory exists
    if not os.path.exists(base_dir):
        print(f"Error: Base directory '{base_dir}' does not exist")
        return 0

    # Counter
    deleted_count = 0

    print(f"Starting to find and delete reports folders in '{base_dir}'...")

    # If no IDs specified, get all numerically named subfolders
    if folder_ids is None:
        folder_ids = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and item.isdigit():
                folder_ids.append(item)

    # Process each specified folder ID
    for folder_id in folder_ids:
        folder_path = os.path.join(base_dir, str(folder_id))

        # Check if folder exists
        if not os.path.exists(folder_path):
            print(f"Warning: Folder with ID {folder_id} does not exist, skipping")
            continue

        # Check if reports folder exists
        reports_path = os.path.join(folder_path, "reports")
        if os.path.exists(reports_path):
            try:
                # Delete reports folder
                shutil.rmtree(reports_path)
                print(f"Deleted: {reports_path}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting '{reports_path}': {e}")
        else:
            print(f"No reports folder found in folder ID {folder_id}, skipping")

    print(f"\nOperation completed! Total deleted {deleted_count} reports folders")
    return deleted_count

def parse_folder_ids(ids_str):
    """
    Parse folder ID string, supports range notation
    For example: "1,3-5,7,10-12" will be parsed as [1,3,4,5,7,10,11,12]

    Args:
        ids_str: ID string, such as "1,3-5,7,10-12"

    Returns:
        folder_ids: Parsed ID list
    """
    folder_ids = []

    # Split comma-separated parts
    parts = ids_str.split(',')

    for part in parts:
        part = part.strip()

        # Handle ranges (e.g. "3-5")
        if '-' in part:
            try:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                folder_ids.extend(range(start, end + 1))
            except ValueError:
                print(f"Warning: Cannot parse ID range '{part}', skipping")

        # Handle single ID
        else:
            try:
                folder_ids.append(int(part))
            except ValueError:
                print(f"Warning: Cannot parse ID '{part}', skipping")

    return sorted(folder_ids)

def main():
    parser = argparse.ArgumentParser(description='Delete reports folders in subfolders with specified IDs')
    parser.add_argument('-d', '--directory', required=True,
                        help='Base directory path')
    parser.add_argument('-i', '--ids',
                        help='Folder IDs to process, can be single ID, comma-separated ID list or range (e.g.: "1,3-5,7,10-12"), if not specified then process all IDs')

    args = parser.parse_args()

    # Parse folder IDs
    folder_ids = None
    if args.ids:
        folder_ids = [str(id) for id in parse_folder_ids(args.ids)]
        print(f"Will process folders with the following IDs: {folder_ids}")
    else:
        print("Will process all ID folders")

    delete_reports_folders(args.directory, folder_ids)

if __name__ == "__main__":
    main()
