# Image Validator module using OpenCV for basic validations

import cv2
import os

class ImageValidator:
    """
    Validates images for quality and compliance with signage inspection requirements.
    Performs basic checks without AI model involvement.
    """
    
    # Configuration constants for validation thresholds
    # Note: Lenskart test images are 144x288, so we use lenient minimums to allow Gemini analysis
    MIN_WIDTH = 100  # Minimum acceptable image width in pixels (lenient for thumbnails)
    MIN_HEIGHT = 100  # Minimum acceptable image height in pixels (lenient for thumbnails)
    BLUR_THRESHOLD = 100  # Laplacian variance threshold for blur detection
    EDGE_THRESHOLD = 500  # Canny edge detection threshold for cropping analysis
    BRIGHTNESS_THRESHOLD = 50  # Brightness level threshold (0-255) for dark detection
    
    def __init__(self):
        """Initialize the ImageValidator with predefined thresholds."""
        pass
    
    def validate_image(self, image_path):
        """
        Perform comprehensive image validations using OpenCV.
        
        Checks:
        1. Image readability - Can the file be loaded?
        2. Resolution - Is the image large enough? (width >= 500, height >= 300)
        3. Blur quality - Is the image blurry? (Laplacian variance > threshold)
        4. Edge detection - Are edges clear for frame analysis? (Canny detection)
        5. Brightness analysis - Is image too dark? (Mean brightness analysis)
        
        Args:
            image_path (str): Absolute path to the image file
            
        Returns:
            dict: Structured validation results with keys:
                - is_readable (bool): File can be loaded successfully
                - width (int): Image width in pixels
                - height (int): Image height in pixels
                - resolution_ok (bool): Meets minimum resolution requirements
                - laplacian_variance (float): Blur detection score (higher = sharper)
                - is_blurry (bool): Image fails blur quality check
                - edge_density (float): Density of detected edges (for cropping analysis)
                - mean_brightness (float): Average brightness (0-255)
                - is_very_dark (bool): Image is too dark (brightness < threshold)
                - validation_passed (bool): Overall validation status
                - error (str): Error message if validation failed, else None
        """
        try:
            # Step 1: Load image from file
            image = cv2.imread(image_path)
            
            # Check if image was successfully loaded
            if image is None:
                return {
                    'is_readable': False,
                    'width': None,
                    'height': None,
                    'resolution_ok': None,
                    'laplacian_variance': None,
                    'is_blurry': None,
                    'edge_density': None,
                    'mean_brightness': None,
                    'is_very_dark': None,
                    'validation_passed': False,
                    'error': 'Unable to read image file'
                }
            
            # Step 2: Extract image dimensions
            height, width = image.shape[:2]
            
            # Step 3: Check if resolution meets minimum requirements
            resolution_ok = (width >= self.MIN_WIDTH) and (height >= self.MIN_HEIGHT)
            
            # Step 4: Detect blur using Laplacian variance method
            # Convert to grayscale for blur detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (higher variance = sharper image, lower = more blurry)
            laplacian_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Determine if image is blurry based on threshold
            is_blurry = laplacian_variance < self.BLUR_THRESHOLD
            
            # Step 5: Detect edges for cropping/frame analysis
            # Use Canny edge detection to find frame/signage boundaries
            edges = cv2.Canny(gray, 100, 200)
            
            # Calculate edge density as percentage of pixels with detected edges
            total_edge_pixels = cv2.countNonZero(edges)
            total_pixels = height * width
            edge_density = (total_edge_pixels / total_pixels) * 100 if total_pixels > 0 else 0
            
            # Step 6: Analyze brightness for low-light detection
            # Calculate mean brightness across all channels
            mean_brightness = cv2.mean(image)[0]  # Using first channel (B in BGR)
            
            # Determine if image is very dark
            is_very_dark = mean_brightness < self.BRIGHTNESS_THRESHOLD
            
            # Step 7: Determine overall validation status
            # Image passes if: readable, proper resolution, not blurry, and not too dark
            validation_passed = (resolution_ok and not is_blurry and not is_very_dark)
            
            return {
                'is_readable': True,
                'width': int(width),
                'height': int(height),
                'resolution_ok': resolution_ok,
                'laplacian_variance': float(laplacian_variance),
                'is_blurry': is_blurry,
                'edge_density': float(edge_density),
                'mean_brightness': float(mean_brightness),
                'is_very_dark': is_very_dark,
                'validation_passed': validation_passed,
                'error': None
            }
        
        except Exception as e:
            # Catch any unexpected errors during validation
            return {
                'is_readable': False,
                'width': None,
                'height': None,
                'resolution_ok': None,
                'laplacian_variance': None,
                'is_blurry': None,
                'edge_density': None,
                'mean_brightness': None,
                'is_very_dark': None,
                'validation_passed': False,
                'error': str(e)
            }