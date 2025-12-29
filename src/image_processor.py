# Image processing module using OpenCV for basic validations

import cv2
import os

class ImageProcessor:
    def __init__(self):
        pass
    
    def validate_image(self, image_path):
        """
        Perform basic image validations using OpenCV.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary containing validation results
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'is_valid_image': False,
                    'is_cropped': None,
                    'is_low_quality': None,
                    'error': 'Unable to load image'
                }
            
            # Check if image is cropped (simple heuristic: aspect ratio check)
            height, width = image.shape[:2]
            aspect_ratio = width / height
            is_cropped = aspect_ratio < 1.0 or aspect_ratio > 3.0  # Assuming signage is landscape
            
            # Check image quality (blur detection using Laplacian variance)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            is_low_quality = variance < 100  # Threshold for blur
            
            return {
                'is_valid_image': True,
                'is_cropped': is_cropped,
                'is_low_quality': is_low_quality,
                'error': None
            }
        except Exception as e:
            return {
                'is_valid_image': False,
                'is_cropped': None,
                'is_low_quality': None,
                'error': str(e)
            }