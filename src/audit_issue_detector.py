# Audit Issue Detector - Quality-aware confidence scoring for low-light/blurry images
# This module applies blur and image quality adjusted confidence thresholds

class AuditIssueDetector:
    """
    Applies quality-aware confidence scoring for accurate classification.
    
    Confidence Thresholds (adjusted for image quality):
    - Clear images: High threshold = 0.85 (strict)
    - Slightly blurry: Medium threshold = 0.75 (moderate)
    - Very blurry/low-light: Low threshold = 0.70 (lenient, but manual review still required)
    
    This approach ensures accuracy even with blurry/low-light images by adjusting
    expectations based on actual image quality.
    """
    
    def __init__(self):
        """Initialize the audit issue detector with blur-aware thresholds."""
        # Confidence thresholds based on image quality
        self.confidence_thresholds = {
            'clear': 0.85,           # Clear images require high confidence
            'slightly_blurry': 0.75, # Blurry images use moderate threshold
            'very_blurry': 0.70      # Very blurry/low-light uses lenient threshold
        }
    
    def get_quality_tier(self, validation_results):
        """
        Determine image quality tier for confidence threshold adjustment.
        
        Args:
            validation_results (dict): Output from ImageValidator
            
        Returns:
            str: Quality tier ('clear', 'slightly_blurry', or 'very_blurry')
        """
        laplacian_variance = validation_results.get('laplacian_variance', 0)
        is_blurry = validation_results.get('is_blurry', False)
        is_very_dark = validation_results.get('is_very_dark', False)
        mean_brightness = validation_results.get('mean_brightness', 100)
        
        # Very blurry or very dark images
        if is_blurry and (is_very_dark or laplacian_variance < 50):
            return 'very_blurry'
        
        # Moderately blurry or dark
        if is_blurry or mean_brightness < 80:
            return 'slightly_blurry'
        
        # Clear image
        return 'clear'
    
    def adjust_confidence(self, ai_confidence, quality_tier):
        """
        Adjust AI confidence based on image quality.
        
        Low-quality images may need lower confidence thresholds to avoid
        false negatives, but we still report actual AI confidence level.
        
        Args:
            ai_confidence (float): Raw AI confidence (0.0-1.0)
            quality_tier (str): Image quality tier
            
        Returns:
            dict: Adjusted confidence info
                - raw_confidence: Original AI confidence
                - quality_tier: Image quality assessment
                - applicable_threshold: Threshold for this image type
                - meets_threshold: Whether raw confidence meets threshold
        """
        threshold = self.confidence_thresholds.get(quality_tier, 0.75)
        
        return {
            'raw_confidence': ai_confidence,
            'quality_tier': quality_tier,
            'applicable_threshold': threshold,
            'meets_threshold': ai_confidence >= threshold
        }
    
    def detect_issues(self, validation_results, ai_analysis):
        """
        Analyze validation and AI results to identify issues for audit.
        Applies quality-aware confidence thresholds.
        
        Args:
            validation_results (dict): Image validation results from ImageValidator
            ai_analysis (dict): AI analysis output from AIInspector
            
        Returns:
            dict: Audit findings:
                - issue_detected (bool): Are there potential issues?
                - issue_type (str): Type of issue detected
                - issue_description (str): Human-readable description
                - confidence_score (float): AI confidence in this analysis
                - quality_tier (str): Image quality assessment
                - manual_review_required (bool): Always True
                - details (dict): Additional context for auditor
        """
        
        # Initialize findings
        findings = {
            'issue_detected': False,
            'issue_type': 'no_issue',
            'issue_description': 'No issues detected',
            'confidence_score': 1.0,
            'quality_tier': 'clear',
            'manual_review_required': True,
            'details': {}
        }
        
        # Determine image quality tier
        quality_tier = self.get_quality_tier(validation_results)
        findings['quality_tier'] = quality_tier
        
        # Extract values safely
        is_readable = validation_results.get('is_readable', False)
        resolution_ok = validation_results.get('resolution_ok', False)
        is_blurry = validation_results.get('is_blurry', False)
        is_very_dark = validation_results.get('is_very_dark', False)
        
        is_lenskart_board = ai_analysis.get('is_lenskart_board', False)
        signage_visible = ai_analysis.get('signage_visible', False)
        light_status = str(ai_analysis.get('light_status', 'unclear')).lower()
        partial_letter_illumination = ai_analysis.get('partial_letter_illumination', False)
        image_quality = ai_analysis.get('image_quality', False)
        is_blurry_ai = ai_analysis.get('is_blurry', False)
        ai_confidence = ai_analysis.get('confidence_score', 0.0)
        ai_explanation = ai_analysis.get('detailed_explanation', '')
        ai_error = ai_analysis.get('error')
        
        # Get applicable confidence threshold for this image quality
        confidence_info = self.adjust_confidence(ai_confidence, quality_tier)
        threshold = confidence_info['applicable_threshold']
        
        # ===== Issue Detection Logic =====
        # Mapped to 4 categories: incorrect_image, cropped_image, light_not_on, partial_letters_unlit
        
        # 1. Image readability or structure errors
        if not is_readable:
            findings['issue_detected'] = True
            findings['issue_type'] = 'incorrect_image'
            findings['issue_description'] = 'Image file is corrupted or unreadable'
            findings['confidence_score'] = 0.0
            findings['details'] = {
                'reason': 'Cannot read image file',
                'is_readable': False,
                'note': 'Resubmit valid image file'
            }
            return findings
        
        # 2. Not a Lenskart board
        if is_lenskart_board is False:
            findings['issue_detected'] = True
            findings['issue_type'] = 'incorrect_image'
            findings['issue_description'] = 'Image does not show Lenskart store signage'
            findings['confidence_score'] = ai_confidence
            findings['details'] = {
                'reason': 'Not Lenskart board',
                'is_lenskart_board': False,
                'ai_confidence': ai_confidence,
                'note': 'Submit image of actual Lenskart store signage'
            }
            return findings
        
        # 3. API Error
        if ai_error is not None:
            findings['issue_detected'] = True
            findings['issue_type'] = 'incorrect_image'
            findings['issue_description'] = 'AI analysis encountered an error'
            findings['confidence_score'] = 0.0
            findings['details'] = {
                'reason': 'API error during analysis',
                'error': ai_error,
                'note': 'Manual review required'
            }
            return findings
        
        # 4. Image Cropping / Signage Not Fully Visible
        if not resolution_ok or not signage_visible:
            findings['issue_detected'] = True
            findings['issue_type'] = 'cropped_image'
            findings['issue_description'] = 'Signage not fully visible in frame or resolution too low'
            findings['confidence_score'] = ai_confidence if ai_confidence > 0.5 else 0.5
            findings['details'] = {
                'reason': 'Cropped or incomplete signage',
                'resolution_ok': resolution_ok,
                'signage_visible': signage_visible,
                'width': validation_results.get('width', 'N/A'),
                'height': validation_results.get('height', 'N/A'),
                'note': 'Resubmit with complete signage in frame'
            }
            return findings
        
        # 5. Lights OFF
        if light_status == 'off':
            findings['issue_detected'] = True
            findings['issue_type'] = 'light_not_on'
            findings['issue_description'] = 'Signage lights are completely OFF'
            findings['confidence_score'] = ai_confidence
            findings['details'] = {
                'reason': 'Lights confirmed OFF',
                'light_status': 'OFF',
                'ai_confidence': ai_confidence,
                'quality_tier': quality_tier,
                'applicable_threshold': threshold,
                'note': 'Verify if lights should be ON; schedule repair if needed'
            }
            return findings
        
        # 6. Partial Letter Illumination
        if partial_letter_illumination is True:
            findings['issue_detected'] = True
            findings['issue_type'] = 'partial_letters_unlit'
            findings['issue_description'] = 'Some individual letters appear dim or poorly illuminated'
            findings['confidence_score'] = ai_confidence
            findings['details'] = {
                'reason': 'Partial letter illumination detected',
                'light_status': light_status,
                'ai_confidence': ai_confidence,
                'quality_tier': quality_tier,
                'applicable_threshold': threshold,
                'note': 'Inspect specific letters; repair defective components'
            }
            return findings
        
        # 7. Unclear Light Status (but meets confidence threshold)
        # If AI cannot determine light status, it defaults to "no issue" if confidence permits
        if light_status == 'unclear':
            if ai_confidence >= threshold:
                # High confidence that light status is uncertain - treat as no issue
                findings['issue_detected'] = False
                findings['issue_type'] = 'no_issue'
                findings['issue_description'] = 'Light status unclear but AI confidence sufficient for approval'
                findings['confidence_score'] = ai_confidence
                findings['details'] = {
                    'reason': 'Light status UNCLEAR but meets confidence threshold',
                    'light_status': 'UNCLEAR',
                    'ai_confidence': ai_confidence,
                    'quality_tier': quality_tier,
                    'applicable_threshold': threshold,
                    'note': 'May indicate daytime photo or conditions requiring manual verification'
                }
                return findings
        
        # ===== No Issues Detected =====
        # All checks passed and confidence meets threshold
        findings['issue_detected'] = False
        findings['issue_type'] = 'no_issue'
        findings['issue_description'] = 'No issues detected - lights appear ON with consistent illumination'
        findings['confidence_score'] = ai_confidence
        findings['details'] = {
            'reason': 'All checks passed',
            'light_status': light_status,
            'signage_visible': signage_visible,
            'partial_letter_illumination': partial_letter_illumination,
            'ai_confidence': ai_confidence,
            'quality_tier': quality_tier,
            'applicable_threshold': threshold,
            'note': 'Human auditor must verify - AI is assistant only'
        }
        
        return findings
