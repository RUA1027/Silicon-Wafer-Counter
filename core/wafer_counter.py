import cv2 # type: ignore
import numpy as np
from scipy.signal import find_peaks

class WaferCounter:
    def __init__(self):
        pass

    def process(self, image_path):
        """
        Process the image to count wafers.
        Returns:
            count (int): Number of wafers detected.
            result_img (numpy.ndarray): Image with detected lines drawn.
            profile (numpy.ndarray): The 1D projection profile (for debugging/plotting).
        """
        # 1. Load Image
        # Use imdecode to support non-ASCII paths (e.g., Chinese characters) on Windows
        try:
            img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            img = None
            
        if img is None:
            raise ValueError(f"Could not load image at {image_path}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Preprocessing
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Gaussian Blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # 3. Background Masking
        # Calculate vertical projection of intensity to find dark background regions
        intensity_profile = np.mean(gray, axis=0)
        
        # Dynamic threshold: allow it to adapt, but keep a floor
        # If the image is generally dark, mean*0.5 might be too low, so keep 50 as floor
        # V3: Lowered to max(40, mean*0.4) to capture dark wafer regions
        bg_thresh = max(40, np.mean(intensity_profile) * 0.4)
        
        background_mask = (intensity_profile > bg_thresh).astype(np.uint8)
        
        # Remove small noise specs in background using opening
        # Reshape to (1, W) for OpenCV
        background_mask = background_mask.reshape(1, -1)
        kernel = np.ones((1, 5), np.uint8)
        background_mask = cv2.morphologyEx(background_mask, cv2.MORPH_OPEN, kernel)
        background_mask = background_mask.flatten()

        # 4. Edge Detection / Gradient
        # We look for vertical edges (X-gradient) for vertically stacked wafers (side-by-side gaps)
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobel_x = np.abs(sobel_x)
        
        # 5. Projection Profile
        # Sum across the height (axis 0) to get a horizontal profile
        h, w = abs_sobel_x.shape
        center_h = h // 2
        crop_height = h // 3
        # Take a central band to avoid top/bottom noise
        roi = abs_sobel_x[center_h - crop_height // 2 : center_h + crop_height // 2, :]
        
        profile = np.mean(roi, axis=0) # Result is (w,) array
        
        # Apply background mask to profile
        # Any peak in the background region is suppressed
        profile = profile * background_mask
        
        # Normalize profile
        if np.max(profile) - np.min(profile) > 0:
            profile = (profile - np.min(profile)) / (np.max(profile) - np.min(profile)) * 255
        profile = profile.astype(np.uint8)

        # 6. Peak Detection
        # Remove DC component for FFT
        profile_no_dc = profile - np.mean(profile)
        fft_res = np.fft.fft(profile_no_dc)
        freqs = np.fft.fftfreq(len(profile_no_dc))
        
        pos_mask = freqs > 0
        fft_mag = np.abs(fft_res)[pos_mask]
        pos_freqs = freqs[pos_mask]
        
        if len(fft_mag) > 0:
            valid_mask = pos_freqs > (10 / len(profile)) 
            if np.any(valid_mask):
                fft_mag = fft_mag[valid_mask]
                pos_freqs = pos_freqs[valid_mask]
                
                peak_freq_idx = np.argmax(fft_mag)
                peak_freq = pos_freqs[peak_freq_idx]
                estimated_period = 1 / peak_freq
            else:
                estimated_period = 20
        else:
            estimated_period = 20
            
        print(f"Estimated period: {estimated_period:.2f} pixels")
        
        min_distance = max(3, int(estimated_period * 0.6))
        min_distance = min(min_distance, 50)
        
        prominence = 10
        
        peaks, _ = find_peaks(profile, distance=min_distance, prominence=prominence)
        
        count = len(peaks)
        
        # 6. Visualization
        result_img = img.copy()
        for p in peaks:
            # Draw a vertical line at the peak column (p is the x-coordinate)
            cv2.line(result_img, (p, 0), (p, h), (0, 0, 255), 1)
            
        cv2.putText(result_img, f"Count: {count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return count, result_img, profile

if __name__ == "__main__":
    # Test with one image
    import os
    files = [f for f in os.listdir('.') if f.endswith('.jpg')]
    if files:
        wc = WaferCounter()
        c, res, prof = wc.process(files[0])
        print(f"Processed {files[0]}: {c} wafers")
        cv2.imwrite("test_result.jpg", res)
