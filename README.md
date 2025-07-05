# Image borders and watermark

A versatile Python script to batch-process images in a folder. This tool can add borders to make images square, apply a watermark, and preserve all original metadata, ensuring no loss of quality.

## Features

- **Square Images with Borders**: Automatically calculates and adds horizontal or vertical borders to make any image a 1x1 aspect ratio without cropping or stretching.
- **Full Metadata Preservation**: Copies all original metadata (EXIF, DPI, ICC color profiles, etc.) to the new image.
- **High-Quality Output**: Saves JPEG files at a high-quality setting (defaulting to 95/100) to prevent quality loss during re-compression.
- **Optional Watermarking**: Apply a custom image watermark to the bottom-right corner of processed images.
- **Optional Deletion of Originals**: Includes a safe-guard option to delete the original files after they have been successfully processed.
- **Cross-Platform Path Handling**: Automatically handles Windows-style paths even when run from a Linux-like terminal (e.g., WSL, Git Bash).

---

## Requirements

- Python 3.x
- Pillow (Python Imaging Library)

---

## Installation

1.  **Clone or download the script** and save it as `process_images.py` (or any name you prefer).

2.  **Install the Pillow library** using pip:
    ```bash
    pip install Pillow
    ```

---

## Usage

The script is run from the command line. The basic structure is:

```bash
python process_images.py "/path/to/image/folder" ["/path/to/watermark.png"] [--delete-originals]
Important: Always enclose file paths in double quotes (") if they contain spaces.Examples1. Add Borders OnlyThis is the simplest use case. It will create new _1x1.jpg files in the same folder.python process_images.py "C:\Users\YourUser\Pictures\Vacation Photos"
2. Add Borders and a WatermarkProvide the path to your watermark image as the second argument.python process_images.py "C:\Users\YourUser\Pictures\Vacation Photos" "C:\Users\YourUser\Documents\my_logo.png"
3. Add Borders and Delete OriginalsUse the --delete-originals flag to remove the source files after processing. Use this with caution!python process_images.py "C:\Users\YourUser\Pictures\Vacation Photos" --delete-originals
4. Add Borders, Watermark, and Delete OriginalsCombine the watermark path and the delete flag. The order of the flag does not matter.python process_images.py "C:\Users\YourUser\Pictures\Vacation Photos" "C:\Users\YourUser\Documents\my_logo.png" --delete-originals
orpython process_images.py --delete-originals "C:\Users\YourUser\Pictures\Vacation Photos" "C:\Users\YourUser\Documents\my_logo.png"
CustomizationYou can easily change the script's behavior by editing the variables in the # --- ADJUSTABLE SETTINGS --- section at the bottom of the script file.size_ratio: A float that determines the watermark's width relative to the image's width. 0.15 means 15%.opacity: A float from 0.0 (fully transparent) to 1.0 (fully opaque) for the watermark.color_for_borders: The color of the added borders. Can be a name ('white') or hex code ('#FFFFFF').jpeg_quality: An integer from 1 to 100 that controls the quality of saved JPEGs. 95 is recommended for high quality.# --- ADJUSTABLE SETTINGS ---
size_ratio = 0.15
opacity = 0.6
color_for_borders = 'white'
jpeg_quality = 95
