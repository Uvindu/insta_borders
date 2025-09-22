
import os
import sys
from PIL import Image, ImageOps
import re

def convert_windows_to_linux_path(path_input: str) -> str:
    """
    Converts a Windows-style file path to a Linux-compatible format.
    """
    if path_input.startswith('/'):
        return path_input
    linux_path = path_input.replace('\\', '/')
    drive_letter_pattern = re.compile(r'^([a-zA-Z]):/')
    linux_path = drive_letter_pattern.sub(
        lambda match: f'/mnt/{match.group(1).lower()}/', 
        linux_path
    )
    return linux_path

def process_images(input_folder, watermark_path=None, delete_originals=False, watermark_size_ratio=0.15, watermark_opacity=0.6, border_color='white', jpeg_quality=95):

    """
    Processes images in a folder to make them square by adding borders, optionally applies watermark and/or deletes originals.
    """
    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')


    watermark_base = None
    if watermark_path:
        try:
            watermark_base = Image.open(watermark_path).convert("RGBA")
            print(f"Using watermark: {watermark_path}")
        except FileNotFoundError:
            print(f"Error: Watermark image not found at '{watermark_path}'")
            sys.exit(1)


    if not os.path.isdir(input_folder):
        print(f"Error: Folder not found at '{input_folder}'")
        return
    print(f"Scanning folder: {input_folder}")
    if delete_originals:
        print("WARNING: Original files will be deleted after processing.")


    for filename in os.listdir(input_folder):
        if filename.lower().endswith(supported_extensions) and "_1x1" not in filename:
            try:
                image_path = os.path.join(input_folder, filename)
                with Image.open(image_path) as img:
                    metadata = img.info.copy()
                    original_mode = img.mode
                    max_dimension = max(img.size)
                    squared_image = ImageOps.pad(img, (max_dimension, max_dimension), color=border_color, centering=(0.5, 0.5))
                    final_image = squared_image
                    if watermark_base:
                        image_for_watermarking = squared_image
                        if image_for_watermarking.mode != 'RGBA':
                            image_for_watermarking = image_for_watermarking.convert('RGBA')
                        watermark = watermark_base.copy()
                        wm_target_width = int(image_for_watermarking.width * watermark_size_ratio)
                        watermark.thumbnail((wm_target_width, wm_target_width), Image.LANCZOS)
                        if watermark_opacity < 1.0:
                            alpha = watermark.getchannel('A')
                            new_alpha = alpha.point(lambda p: int(p * watermark_opacity) if p > 0 else 0)
                            watermark.putalpha(new_alpha)
                        margin = int(image_for_watermarking.width * 0.02)
                        position = (image_for_watermarking.width - watermark.width - margin,
                                    image_for_watermarking.height - watermark.height - margin)
                        image_for_watermarking.paste(watermark, position, watermark)
                        final_image = image_for_watermarking
                    if final_image.mode != original_mode:
                        final_image = final_image.convert(original_mode)
                    name, ext = os.path.splitext(filename)
                    new_filename = f"{name}_1x1{ext}"
                    output_path = os.path.join(input_folder, new_filename)
                    if ext.lower() in ['.jpg', '.jpeg']:
                        metadata['quality'] = jpeg_quality
                    final_image.save(output_path, **metadata)
                    action = "Bordered & Watermarked" if watermark_base else "Bordered"
                    print(f"Processed '{filename}' -> Saved as '{new_filename}' ({action})")
                    if delete_originals:
                        try:
                            os.remove(image_path)
                            print(f"  -> Removed original: '{filename}'")
                        except OSError as e:
                            print(f"  -> ERROR: Could not remove original '{filename}'. Reason: {e}")
            except Exception as e:
                print(f"Could not process file '{filename}'. Reason: {e}")
    print("\nProcessing complete.")

if __name__ == "__main__":
    args = sys.argv[1:]
    delete_originals_flag = "--delete-originals" in args
    if delete_originals_flag:
        args.remove("--delete-originals")
    if len(args) < 1 or len(args) > 2:
        print("Usage: python script.py \"/path/to/folder\" [\"/path/to/watermark.png\"] [--delete-originals]")
        sys.exit(1)
    folder_to_process = args[0]
    watermark_file_path = None
    if len(args) == 2:
        watermark_file_path = args[1]
    if sys.platform != "win32":
        print("Non-Windows OS detected. Converting paths...")
        folder_to_process = convert_windows_to_linux_path(folder_to_process)
        if watermark_file_path:
            watermark_file_path = convert_windows_to_linux_path(watermark_file_path)
    size_ratio = 0.15
    opacity = 0.6
    color_for_borders = 'white'
    jpeg_quality = 95
    process_images(
        input_folder=folder_to_process,
        watermark_path=watermark_file_path,
        delete_originals=delete_originals_flag,
        watermark_size_ratio=size_ratio,
        watermark_opacity=opacity,
        border_color=color_for_borders,
        jpeg_quality=jpeg_quality
    )
