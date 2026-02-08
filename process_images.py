import argparse
import logging
import os
import shutil
import sys
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageOps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

def convert_windows_to_linux_path(path_input: str) -> Path:
    """
    Converts a Windows-style file path to a Linux-compatible pathlib.Path object.
    Useful for WSL environments.
    """
    path_str = str(path_input)
    if path_str.startswith('/'):
        return Path(path_str)
    
    # Replace backslashes
    linux_path_str = path_str.replace('\\', '/')
    
    # Handle drive letters (e.g., C:/ -> /mnt/c/)
    drive_letter_pattern = re.compile(r'^([a-zA-Z]):/')
    linux_path_str = drive_letter_pattern.sub(
        lambda match: f'/mnt/{match.group(1).lower()}/', 
        linux_path_str
    )
    return Path(linux_path_str)

def get_path(path_str: str) -> Path:
    """Resolves path, handling potential Windows paths on Linux (WSL)."""
    if sys.platform != "win32" and (':' in path_str or '\\' in path_str):
         return convert_windows_to_linux_path(path_str)
    return Path(path_str)

def process_file(
    file_path: Path,
    output_dir: Path,
    watermark_path: Optional[Path],
    watermark_config: dict,
    border_color: str,
    jpeg_quality: int,
    delete_original: bool
) -> str:
    """
    Worker function to process a single image.
    """
    try:
        # Skip if it looks like a processed file (simple check to avoid recursion if output is same dir)
        if "_1x1" in file_path.stem:
            return f"Skipped (already processed): {file_path.name}"

        with Image.open(file_path) as img:
            # Preserve metadata
            metadata = img.info.copy()
            original_mode = img.mode
            
            # 1. Square the image with borders
            max_dimension = max(img.size)
            squared_image = ImageOps.pad(
                img, 
                (max_dimension, max_dimension), 
                color=border_color, 
                centering=(0.5, 0.5)
            )
            
            final_image = squared_image

            # 2. Add Watermark
            if watermark_path:
                try:
                    # We load watermark inside worker to be safe with pickling, 
                    # though passing a pre-loaded image is faster if shared correctly.
                    # For simplicity and robustness in MP, we assume I/O overhead is acceptable 
                    # or OS caches file read. 
                    # Optimization: In a real heavy loop, we might preload or pass bytes.
                    # Given the task, reopening the small watermark file is negligible compared to JPEG encoding.
                    with Image.open(watermark_path) as wm_base:
                        wm_base = wm_base.convert("RGBA")
                        
                        target_layer = squared_image.convert("RGBA")
                        
                        # Calculate size
                        wm_target_width = int(target_layer.width * watermark_config['ratio'])
                        
                        # Resize watermark
                        wm_resized = wm_base.copy()
                        wm_resized.thumbnail((wm_target_width, wm_target_width), Image.Resampling.LANCZOS)
                        
                        # Apply Opacity
                        opacity = watermark_config['opacity']
                        if opacity < 1.0:
                            alpha = wm_resized.getchannel('A')
                            new_alpha = alpha.point(lambda p: int(p * opacity) if p > 0 else 0)
                            wm_resized.putalpha(new_alpha)
                        
                        # Position (Bottom-Right)
                        margin = int(target_layer.width * 0.02)
                        position = (
                            target_layer.width - wm_resized.width - margin,
                            target_layer.height - wm_resized.height - margin
                        )
                        
                        target_layer.paste(wm_resized, position, wm_resized)
                        final_image = target_layer

                except Exception as wm_err:
                    logger.error(f"Failed to load watermark for {file_path.name}: {wm_err}")
                    # Continue without watermark if it fails

            # 3. Save
            if final_image.mode != original_mode and original_mode != 'RGBA':
                 # Convert back if original wasn't RGBA (unless we added alpha via watermark)
                 # However, JPEGs don't support RGBA.
                 if file_path.suffix.lower() in ['.jpg', '.jpeg']:
                     final_image = final_image.convert("RGB")
                 else:
                     final_image = final_image.convert(original_mode)

            new_filename = f"{file_path.stem}_1x1{file_path.suffix}"
            output_path = output_dir / new_filename

            save_kwargs = metadata
            if file_path.suffix.lower() in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = jpeg_quality
            
            # Filter incompatible args for save if necessary (usually metadata is fine)
            try:
                final_image.save(output_path, **save_kwargs)
            except TypeError:
                # Fallback if metadata contains unserializable data or bad args
                final_image.save(output_path, quality=jpeg_quality)

            msg = f"Processed: {file_path.name} -> {output_path.name}"

    except Exception as e:
        return f"Error processing {file_path.name}: {str(e)}"

    # 4. Delete Original
    if delete_original:
        try:
            file_path.unlink()
            msg += " (Original deleted)"
        except OSError as e:
            msg += f" (Failed to delete original: {e})"
    
    return msg

def main():
    parser = argparse.ArgumentParser(
        description="Batch process images: Add borders to make square (1x1), optionally watermark, and preserve metadata."
    )
    
    # Path Arguments
    parser.add_argument("input_dir", help="Directory containing images to process")
    parser.add_argument("-w", "--watermark", help="Path to watermark image", default=None)
    parser.add_argument("-o", "--output", help="Output directory (default: same as input)", default=None)
    
    # Flags
    parser.add_argument("--delete-originals", action="store_true", help="Delete original files after processing")
    
    # Configuration
    parser.add_argument("--color", default="white", help="Border color (name or hex, default: white)")
    parser.add_argument("--opacity", type=float, default=0.6, help="Watermark opacity (0.0 - 1.0, default: 0.6)")
    parser.add_argument("--ratio", type=float, default=0.15, help="Watermark size ratio relative to image width (default: 0.15)")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality (1-100, default: 95)")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel workers (default: CPU count)")

    args = parser.parse_args()

    # Setup Paths
    input_path = get_path(args.input_dir)
    if not input_path.is_dir():
        logger.error(f"Error: Input directory '{input_path}' does not exist.")
        sys.exit(1)

    if args.output:
        output_path = get_path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path

    watermark_path = get_path(args.watermark) if args.watermark else None
    if watermark_path and not watermark_path.exists():
        logger.error(f"Error: Watermark file '{watermark_path}' not found.")
        sys.exit(1)

    # Collect Files
    files_to_process = [
        p for p in input_path.iterdir() 
        if p.suffix.lower() in SUPPORTED_EXTENSIONS and "_1x1" not in p.stem
    ]

    if not files_to_process:
        logger.info(f"No valid images found in {input_path}")
        sys.exit(0)

    logger.info(f"Found {len(files_to_process)} images in {input_path}")
    if args.delete_originals:
        logger.warning("WARNING: Original files will be deleted after processing.")

    watermark_config = {
        'ratio': args.ratio,
        'opacity': args.opacity
    }

    # Parallel Processing
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_file, 
                p, 
                output_path, 
                watermark_path, 
                watermark_config, 
                args.color, 
                args.quality, 
                args.delete_originals
            ): p for p in files_to_process
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            logger.info(result)

    logger.info("\nBatch processing complete.")

if __name__ == "__main__":
    main()