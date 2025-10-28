#!/usr/bin/env python3
"""
dir_size.py - calculate total size of a directory (recursively).
Usage:
    python dir_size.py [directory_path]

If no directory is provided, the current working directory is used.
"""

import os
import sys

def get_dir_size(path: str) -> int:
    """Return total size (in bytes) of all files in the directory tree."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
            except OSError:
                # Skip files that can't be accessed
                pass
    return total

if __name__ == "__main__":
    # Use current directory if no argument is given
    if len(sys.argv) > 2:
        print("Usage: python dir_size.py [directory_path]")
        sys.exit(1)

    directory = sys.argv[1] if len(sys.argv) == 2 else os.getcwd()

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        sys.exit(1)

    size_bytes = get_dir_size(directory)
    size_mb = size_bytes / (1024 * 1024)

    print(f"Directory: {directory}")
    print(f"Size: {size_bytes:,} bytes ({size_mb:.2f} MB)")
