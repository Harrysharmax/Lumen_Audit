# AI Inspector module for advanced image analysis using Google Gemini Vision

import base64
import json
import os
import google.generativeai as genai


def normalize_ai_output(analysis_dict: dict) -> dict:
    """
    Normalize AI output to ensure consistency and handle edge cases.
    
    Rules:
    - Lowercase all string values
    - Strip leading/trailing whitespace from strings
    - Convert None/empty/null values to "unclear" (except for 'error' and 'api_used' fields)
    - Preserve boolean and numeric values
    
    Args:
        analysis_dict (dict): Raw AI analysis output
        
    Returns:
        dict: Normalized analysis output
    """
    normalized = {}
    
    # Fields that should not be converted to "unclear"
    preserve_none_fields = {"error", "api_used"}
    
    for key, value in analysis_dict.items():
        # Handle None values
        if value is None:
            if key in preserve_none_fields:
                normalized[key] = None
            else:
                normalized[key] = "unclear"
            continue
        
        # Handle string values: lowercase and strip
        if isinstance(value, str):
            normalized_str = value.strip().lower()
            # Convert empty strings to "unclear"
            if not normalized_str:
                if key in preserve_none_fields:
                    normalized[key] = None
                else:
                    normalized[key] = "unclear"
            else:
                normalized[key] = normalized_str
        
        # Preserve boolean and numeric values as-is
        elif isinstance(value, (bool, int, float)):
            normalized[key] = value
        
        # Default: pass through
        else:
            normalized[key] = value
    
    return normalized


class AIInspector:
    """
    Performs advanced AI-powered analysis of signage images using Google Gemini Vision.
    Evaluates illumination compliance and image correctness.
    """
    
    # Google Gemini API endpoint
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    MODEL = "gemini-2.5-flash"
    MAX_TOKENS = 500
    
    # Structured prompt for consistent AI analysis - Lenskart Signage Quality Auditor
    ANALYSIS_PROMPT = """You are analyzing a Lenskart store signage image for quality audit.

CRITICAL: Look for Lenskart branding, logos, or store signage. If this is NOT a Lenskart store signage, respond with is_lenskart_board: false.

Analyze and respond with ONLY valid JSON (no markdown, no extra text):

{
  "is_lenskart_board": boolean - Is this clearly a Lenskart store signage board?,
  "signage_visible": boolean - Is the entire signage clearly visible in the frame?,
  "light_status": string - "ON" (lights bright/illuminated), "OFF" (dark/no light), or "UNCLEAR",
  "partial_letter_illumination": boolean - Are some individual letters dim or poorly lit while others are bright?,
  "image_quality": boolean - Is image clear enough to analyze? (Account for night photography, slight blur, low-light OK),
  "is_blurry": boolean - Is image significantly blurry or out of focus?,
  "confidence_score": number - Your confidence 0.0 to 1.0 (lower for blurry/low-light),
  "detailed_explanation": string - Brief explanation of findings
}

CRITICAL RULES:
- Respond ONLY with valid JSON object - no markdown wrapping, no extra text
- For Lenskart detection: Look for "Lenskart" text, eyewear branding, or store logos
- For partial letters: This means SOME letters are dim/unlit while OTHERS are bright (not all lights off)
- For confidence: Reduce score for blurry/low-light conditions (0.70-0.85 acceptable for poor quality)
- If uncertain about anything, set lower confidence and explain in detailed_explanation"""
    
    def __init__(self, api_key=None):
        """
        Initialize the AI Inspector.
        
        Args:
            api_key (str): Google Gemini API key. If None, mock mode will be used.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.use_mock = self.api_key is None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = None
        else:
            self.client = None
    
    def analyze_signage(self, image_path):
        """
        Analyze store signage image using GPT-4 Vision for illumination compliance.
        
        Evaluates:
        - Whether signage is visible in the image
        - Light status (ON/OFF/UNCLEAR)
        - Presence of partial letter illumination
        - Image correctness and relevance
        
        Args:
            image_path (str): Absolute path to the image file
            
        Returns:
            dict: Structured JSON response with analysis results and metadata:
                - is_lenskart_board (bool): Is this a Lenskart signage board?
                - signage_visible (bool): Is the entire signage visible in frame?
                - light_status (str): "ON", "OFF", or "UNCLEAR"
                - partial_letter_illumination (bool): Are individual letters poorly lit?
                - image_quality (bool): Sufficient quality for analysis?
                - is_blurry (bool): Is image significantly blurred?
                - confidence_score (float): Model confidence (0.0-1.0)
                - detailed_explanation (str): AI explanation
                - api_used (str): "gemini-vision" or "mock"
                - error (str): Error message if any, else None
        """
        # Use mock if API key not available
        if self.use_mock:
            return self._mock_analyze_signage(image_path)
        
        try:
            # Step 1: Load and encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Step 2: Create request with image and prompt
            model = genai.GenerativeModel(self.MODEL)
            response = model.generate_content(
                [
                    self.ANALYSIS_PROMPT,
                    {
                        "mime_type": "image/jpeg",
                        "data": base64_image
                    }
                ]
            )
            
            # Step 3: Extract and parse JSON response from API
            analysis_text = response.text
            
            # IMPORTANT: Gemini often wraps JSON in markdown code blocks ```json ... ```
            # Remove markdown wrapping if present
            if analysis_text.startswith('```'):
                # Extract JSON from markdown code blocks
                lines = analysis_text.split('\n')
                # Find start and end of JSON
                start_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('```'):
                        start_idx = i + 1
                        break
                end_idx = len(lines)
                for i in range(start_idx, len(lines)):
                    if lines[i].startswith('```'):
                        end_idx = i
                        break
                analysis_text = '\n'.join(lines[start_idx:end_idx]).strip()
            
            # Parse JSON response from AI model
            analysis_json = json.loads(analysis_text)
            
            # Normalize output for consistency
            analysis_json = normalize_ai_output(analysis_json)
            
            # Ensure all expected fields are present
            expected_fields = {
                'is_lenskart_board': None,
                'signage_visible': None,
                'light_status': 'unclear',
                'partial_letter_illumination': None,
                'image_quality': None,
                'is_blurry': None,
                'confidence_score': 0.0,
                'detailed_explanation': None
            }
            for field, default_value in expected_fields.items():
                if field not in analysis_json:
                    analysis_json[field] = default_value
            
            # Add metadata
            analysis_json['api_used'] = 'gemini-vision'
            analysis_json['error'] = None
            
            return analysis_json
        
        except json.JSONDecodeError as e:
            # If API response is not valid JSON, return error
            return {
                'is_lenskart_board': None,
                'signage_visible': None,
                'light_status': 'unclear',
                'partial_letter_illumination': None,
                'image_quality': None,
                'is_blurry': None,
                'confidence_score': 0.0,
                'detailed_explanation': None,
                'api_used': 'gemini-vision',
                'error': f'Invalid JSON response from API: {str(e)}'
            }
        
        except Exception as e:
            # Network or API error
            return {
                'is_lenskart_board': None,
                'signage_visible': None,
                'light_status': 'unclear',
                'partial_letter_illumination': None,
                'image_quality': None,
                'is_blurry': None,
                'confidence_score': 0.0,
                'detailed_explanation': None,
                'api_used': 'gemini-vision',
                'error': f'API request failed: {str(e)}'
            }
    
    def _mock_analyze_signage(self, image_path):
        """
        Mock analysis function for testing without API key.
        Returns realistic test data without making actual API calls.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Mock analysis results in same format as real API
        """
        import random
        
        # Generate mock results with varied scenarios
        scenarios = [
            {
                'is_lenskart_board': True,
                'signage_visible': True,
                'light_status': 'ON',
                'partial_letter_illumination': False,
                'image_quality': True,
                'is_blurry': False,
                'confidence_score': 0.95,
                'detailed_explanation': 'Lenskart signage is clearly visible with lights fully illuminated. All letters are bright and readable.'
            },
            {
                'is_lenskart_board': True,
                'signage_visible': True,
                'light_status': 'OFF',
                'partial_letter_illumination': False,
                'image_quality': True,
                'is_blurry': False,
                'confidence_score': 0.92,
                'detailed_explanation': 'Lenskart signage is visible but lights are completely OFF. No illumination detected on signage.'
            },
            {
                'is_lenskart_board': True,
                'signage_visible': True,
                'light_status': 'ON',
                'partial_letter_illumination': True,
                'image_quality': True,
                'is_blurry': False,
                'confidence_score': 0.88,
                'detailed_explanation': 'Lenskart signage lights are ON but several specific letters show dim or partial illumination.'
            },
            {
                'is_lenskart_board': False,
                'signage_visible': False,
                'light_status': 'UNCLEAR',
                'partial_letter_illumination': None,
                'image_quality': False,
                'is_blurry': True,
                'confidence_score': 0.3,
                'detailed_explanation': 'Image does not show Lenskart signage or is too blurry/unclear for proper analysis.'
            }
        ]
        
        # Select random scenario for variety in testing
        result = random.choice(scenarios)
        
        # Normalize output for consistency
        result = normalize_ai_output(result)
        
        result['api_used'] = 'mock'
        result['error'] = None
        
        return result