#!/usr/bin/env python3
import os
import argparse
import sys

def delete_specific_json_files(directory):
    """
    Delete all files named query_response.json and session_response.json in the specified directory and its subdirectories

    Args:
        directory: Directory path to search

    Returns:
        deleted_count: Number of files deleted
    """
    target_files = ["query_response.json", "session_response.json"]
    deleted_count = 0

    # Check if directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        return 0

    # Traverse directory and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file in target_files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting file '{file_path}': {e}")

    return deleted_count

def main():
    parser = argparse.ArgumentParser(description='Delete all files named query_response.json and session_response.json in the specified directory')
    parser.add_argument('directory', nargs='?', default=os.getcwd(),
                        help='Directory path to search (defaults to current directory)')

    args = parser.parse_args()

    print(f"Starting to search and delete specified JSON files in '{args.directory}'...")
    deleted_count = delete_specific_json_files(args.directory)

    print(f"\nOperation completed! Total deleted {deleted_count} files")

if __name__ == "__main__":
    main()
