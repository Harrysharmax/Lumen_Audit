# Configuration settings for the AI agent

import os

class Config:
    def __init__(self):
        # Get base directory (parent of src/)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Use absolute paths for all directories
        self.image_folder = os.path.join(base_dir, 'data', 'images')
        self.output_folder = os.path.join(base_dir, 'output')
        self.output_file = os.path.join(self.output_folder, 'signage_report.xlsx')
        
        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)
        
        self.api_key = os.getenv('GEMINI_API_KEY') or 'Mainly add api key here '  # For Google Gemini API