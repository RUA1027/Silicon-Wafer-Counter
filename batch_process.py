import os
import argparse
import logging
from pathlib import Path
import cv2
import sys

# Ensure the module can be found if running from a different directory
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

try:
    from core.wafer_counter import WaferCounter
except ImportError:
    print("Error: Could not import 'core.wafer_counter'. Make sure you are running this script from the project root or the 'core' module is accessible.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def setup_argparse():
    parser = argparse.ArgumentParser(description="Batch process silicon wafer images for counting.")
    parser.add_argument("--input", "-i", type=str, default="input", help="Path to input directory containing images.")
    parser.add_argument("--output", "-o", type=str, default="output_results", help="Path to output directory for saving results.")
    parser.add_argument("--save-plot", action="store_true", help="Save the result images with detected lines.")
    return parser.parse_args()

def main():
    args = setup_argparse()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Error: Input directory '{input_path}' does not exist.")
        sys.exit(1)
        
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    image_files = [f for f in input_path.iterdir() if f.suffix.lower() in image_extensions]
    
    if not image_files:
        logger.warning(f"No image files found in '{input_path}'.")
        return
        
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Found {len(image_files)} images. Starting batch processing...")
    logger.info("-" * 60)
    logger.info(f"{'Image Name':<30} | {'Count':<10} | {'Status':<10}")
    logger.info("-" * 60)
    
    counter = WaferCounter()
    success_count = 0
    fail_count = 0
    
    for img_file in image_files:
        try:
            count, result_img, _ = counter.process(str(img_file))
            
            logger.info(f"{img_file.name:<30} | {count:<10} | Success")
            
        
            # Save using imencode + tofile for unicode path support
            save_file = output_path / f"result_{img_file.name}"
            success, encoded_img = cv2.imencode(save_file.suffix, result_img)
            if success:
                encoded_img.tofile(str(save_file))
            else:
                logger.error(f"Failed to encode image: {save_file}")
            
            success_count += 1
            
        except Exception as e:
            # Print error in red if possible, or just standard log
            # Using ANSI codes for red color
            error_msg = f"\033[91mError: {str(e)}\033[0m" 
            logger.error(f"{img_file.name:<30} | {'N/A':<10} | {error_msg}")
            fail_count += 1
            
    logger.info("-" * 60)
    total = success_count + fail_count
    success_rate = (success_count / total * 100) if total > 0 else 0
    logger.info(f"Processing complete.")
    logger.info(f"Total: {total}, Success: {success_count}, Failed: {fail_count}")
    logger.info(f"Success Rate: {success_rate:.2f}%")
    logger.info(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()
