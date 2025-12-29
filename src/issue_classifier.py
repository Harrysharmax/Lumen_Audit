# Issue Classifier - Single Primary Issue Classification
# Classifies AI vision findings into one primary problem category per image

class IssueClassifier:
    """
    Classifies store signage issues into single primary category.
    Uses priority-based decision tree to ensure ONE issue per image.
    
    Categories (in priority order):
    1. incorrect_image - Image is unusable/wrong/invalid (not Lenskart board)
    2. cropped_image - Signage partially cut off or not fully visible
    3. light_not_on - Lights are completely OFF
    4. partial_letters_unlit - Some individual letters are poorly lit/dim
    5. no_issue_detected - All checks passed, lights appear ON
    """
    
    # Issue categories
    INCORRECT_IMAGE = 'incorrect_image'
    CROPPED_IMAGE = 'cropped_image'
    LIGHT_NOT_ON = 'light_not_on'
    PARTIAL_LETTERS_UNLIT = 'partial_letters_unlit'
    NO_ISSUE = 'no_issue_detected'
    
    # Priority order (higher = more severe, checked first)
    PRIORITY_ORDER = [
        INCORRECT_IMAGE,           # Priority 1: Image problems / Not Lenskart
        CROPPED_IMAGE,             # Priority 2: Composition problems
        LIGHT_NOT_ON,              # Priority 3: Confirmed OFF
        PARTIAL_LETTERS_UNLIT,     # Priority 4: Partial letter issues
        NO_ISSUE                   # Priority 5: All clear
    ]
    
    def __init__(self):
        """Initialize the issue classifier."""
        self.confidence_thresholds = {
            'high': 0.80,
            'medium': 0.60,
            'low': 0.40
        }
    
    def classify(self, validation_results, ai_analysis):
        """
        Classify image into single primary issue category.
        
        Args:
            validation_results (dict): Image validation output containing:
                - is_readable (bool): Image can be processed
                - resolution_ok (bool): Resolution meets minimum
                - is_blurry (bool): Image blur detected
                - width, height (int): Image dimensions
                - validation_passed (bool): Overall validation status
                - error (str): Error message if validation failed
            
            ai_analysis (dict): AI vision output containing:
                - is_lenskart_board (bool): Is this a Lenskart signage board?
                - signage_visible (bool): Signage visible in image
                - light_status (str): "ON", "OFF", or "UNCLEAR"
                - partial_letter_illumination (bool): Some letters poorly lit
                - image_quality (bool): Image quality adequate for analysis
                - is_blurry (bool): Image is blurry
                - confidence_score (float): AI confidence 0.0-1.0
                - detailed_explanation (str): Explanation of findings
                - error (str): API error if occurred
        
        Returns:
            dict: Classification result:
                - issue_type (str): Primary issue category
                - issue_detected (bool): Any issue found
                - confidence_score (float): Confidence in classification
                - reasoning (str): Why this category was chosen
                - manual_review_required (bool): Always True
                - details (dict): Additional classification details
        """
        
        # Initialize result structure
        result = {
            'issue_type': self.NO_ISSUE,
            'issue_detected': False,
            'confidence_score': 1.0,
            'reasoning': 'No issues detected',
            'manual_review_required': True,
            'details': {}
        }
        
        # Extract validation inputs
        is_readable = validation_results.get('is_readable', False)
        resolution_ok = validation_results.get('resolution_ok', False)
        is_blurry = validation_results.get('is_blurry', False)
        validation_passed = validation_results.get('validation_passed', False)
        validation_error = validation_results.get('error')
        width = validation_results.get('width')
        height = validation_results.get('height')
        
        # Extract AI analysis inputs
        is_lenskart_board = ai_analysis.get('is_lenskart_board', False)
        signage_visible = ai_analysis.get('signage_visible', False)
        light_status = str(ai_analysis.get('light_status', 'UNCLEAR')).upper()
        partial_letter_illumination = ai_analysis.get('partial_letter_illumination', False)
        image_quality = ai_analysis.get('image_quality', False)
        is_blurry = ai_analysis.get('is_blurry', False)
        ai_confidence = ai_analysis.get('confidence_score', 0.0)
        ai_error = ai_analysis.get('error')
        
        # ===== PRIORITY 1: INCORRECT_IMAGE =====
        # Image is fundamentally unusable or invalid (not Lenskart, corrupted, etc.)
        
        if validation_error is not None:
            # Validation error occurred
            return {
                'issue_type': self.INCORRECT_IMAGE,
                'issue_detected': True,
                'confidence_score': 1.0,
                'reasoning': f'Validation error: {validation_error}',
                'manual_review_required': True,
                'details': {
                    'category': 'validation_error',
                    'error': validation_error,
                    'action': 'Resubmit clearer image'
                }
            }
        
        if not is_readable:
            # Image cannot be read or processed
            return {
                'issue_type': self.INCORRECT_IMAGE,
                'issue_detected': True,
                'confidence_score': 1.0,
                'reasoning': 'Image is not readable or corrupted',
                'manual_review_required': True,
                'details': {
                    'category': 'unreadable_image',
                    'is_readable': False,
                    'action': 'Resubmit valid image file'
                }
            }
        
        if is_lenskart_board is False:
            # AI confirmed this is NOT a Lenskart board
            return {
                'issue_type': self.INCORRECT_IMAGE,
                'issue_detected': True,
                'confidence_score': ai_confidence,
                'reasoning': 'Image does not contain a Lenskart store signage board (wrong content)',
                'manual_review_required': True,
                'details': {
                    'category': 'not_lenskart_board',
                    'is_lenskart_board': False,
                    'ai_confidence': ai_confidence,
                    'action': 'Submit image of actual Lenskart store signage'
                }
            }
        
        if ai_error is not None:
            # AI analysis failed
            return {
                'issue_type': self.INCORRECT_IMAGE,
                'issue_detected': True,
                'confidence_score': 1.0,
                'reasoning': f'AI analysis failed: {ai_error}',
                'manual_review_required': True,
                'details': {
                    'category': 'ai_error',
                    'error': ai_error,
                    'action': 'Manual review required'
                }
            }
        
        # ===== PRIORITY 2: CROPPED_IMAGE =====
        # Signage is partially cut off or not fully visible
        
        if not signage_visible:
            # Signage not visible in image at all
            return {
                'issue_type': self.CROPPED_IMAGE,
                'issue_detected': True,
                'confidence_score': 1.0,
                'reasoning': 'Signage is not visible in image (cropped or wrong composition)',
                'manual_review_required': True,
                'details': {
                    'category': 'signage_not_visible',
                    'signage_visible': False,
                    'width': width,
                    'height': height,
                    'action': 'Resubmit image with full signage visible'
                }
            }
        
        if not resolution_ok:
            # Resolution insufficient - likely cropped/too zoomed
            return {
                'issue_type': self.CROPPED_IMAGE,
                'issue_detected': True,
                'confidence_score': 0.9,
                'reasoning': 'Image resolution too low or signage too small (possibly cropped)',
                'manual_review_required': True,
                'details': {
                    'category': 'insufficient_resolution',
                    'resolution_ok': False,
                    'width': width,
                    'height': height,
                    'minimum_width': 100,
                    'action': 'Resubmit higher resolution or wider angle image'
                }
            }
        
        # ===== PRIORITY 3: LIGHT_NOT_ON =====
        # Lights are definitively OFF
        
        if light_status == 'OFF':
            # AI confirmed lights are OFF
            return {
                'issue_type': self.LIGHT_NOT_ON,
                'issue_detected': True,
                'confidence_score': ai_confidence,
                'reasoning': 'Signage lights are confirmed OFF',
                'manual_review_required': True,
                'details': {
                    'category': 'lights_off',
                    'light_status': 'OFF',
                    'ai_confidence': ai_confidence,
                    'action': 'Check if lights should be ON, schedule repair if needed'
                }
            }
        
        # ===== PRIORITY 4: PARTIAL_LETTERS_UNLIT =====
        # Some individual letters are poorly lit
        
        if partial_letter_illumination is True:
            # AI detected some letters are poorly lit
            return {
                'issue_type': self.PARTIAL_LETTERS_UNLIT,
                'issue_detected': True,
                'confidence_score': ai_confidence,
                'reasoning': 'Some individual letters have reduced or inconsistent illumination',
                'manual_review_required': True,
                'details': {
                    'category': 'partial_letter_illumination',
                    'partial_letter_illumination': True,
                    'ai_confidence': ai_confidence,
                    'action': 'Inspect which specific letters are unlit, repair defective components'
                }
            }
        
        # ===== PRIORITY 5: NO_ISSUE_DETECTED =====
        # All checks passed, lights appear to be ON
        # Note: Blurry images or unclear light status may still reach here if AI cannot confirm OFF status
        # In such cases, we still report "no issue detected" but confidence will be lower
        
        return {
            'issue_type': self.NO_ISSUE,
            'issue_detected': False,
            'confidence_score': ai_confidence,
            'reasoning': 'All checks passed, signage lights appear to be ON',
            'manual_review_required': True,  # Even no-issue needs human approval
            'details': {
                'category': 'all_checks_passed',
                'light_status': light_status,
                'signage_visible': signage_visible,
                'partial_letter_illumination': partial_letter_illumination,
                'ai_confidence': ai_confidence,
                'is_blurry': is_blurry,
                'action': 'Human auditor must approve - AI is assistant, not decision-maker'
            }
        }
    
    def classify_batch(self, images_data):
        """
        Classify multiple images at once.
        
        Args:
            images_data (list): List of dicts, each containing:
                - validation_results
                - ai_analysis
        
        Returns:
            list: Classification results for each image
        """
        results = []
        for image_data in images_data:
            result = self.classify(
                image_data.get('validation_results', {}),
                image_data.get('ai_analysis', {})
            )
            results.append(result)
        return results
    
    def get_classification_summary(self, classification_results):
        """
        Generate summary statistics from classification results.
        
        Args:
            classification_results (list): Results from classify() or classify_batch()
        
        Returns:
            dict: Summary statistics
        """
        total = len(classification_results)
        
        # Count by category
        category_counts = {}
        for result in classification_results:
            category = result['issue_type']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count issues detected
        issues_detected = sum(1 for r in classification_results if r['issue_detected'])
        
        # Average confidence
        avg_confidence = sum(r['confidence_score'] for r in classification_results) / total if total > 0 else 0.0
        
        return {
            'total_images': total,
            'images_with_issues': issues_detected,
            'images_without_issues': total - issues_detected,
            'category_breakdown': category_counts,
            'average_confidence': avg_confidence,
            'all_require_manual_review': all(r['manual_review_required'] for r in classification_results)
        }


if __name__ == "__main__":
    
    # Example 1: Lights OFF (light_not_on)
    classifier = IssueClassifier()
    
    validation = {
        'is_readable': True,
        'resolution_ok': True,
        'is_blurry': False,
        'validation_passed': True,
        'width': 320,
        'height': 240
    }
    
    ai_analysis = {
        'is_lenskart_board': True,
        'signage_visible': True,
        'light_status': 'OFF',
        'partial_letter_illumination': False,
        'image_quality': True,
        'is_blurry': False,
        'confidence_score': 0.95
    }
    
    result = classifier.classify(validation, ai_analysis)
    print("Example 1 - Lights OFF:")
    print(f"  Issue Type: {result['issue_type']}")
    print(f"  Issue Detected: {result['issue_detected']}")
    print(f"  Confidence: {result['confidence_score']:.2f}")
    print(f"  Reasoning: {result['reasoning']}")
    print()
    
    # Example 2: Cropped Image
    validation2 = {
        'is_readable': True,
        'resolution_ok': False,
        'is_blurry': False,
        'validation_passed': False,
        'width': 80,
        'height': 60
    }
    
    ai_analysis2 = {
        'is_lenskart_board': True,
        'signage_visible': False,
        'light_status': 'UNCLEAR',
        'partial_letter_illumination': None,
        'image_quality': False,
        'is_blurry': False,
        'confidence_score': 0.5
    }
    
    result2 = classifier.classify(validation2, ai_analysis2)
    print("Example 2 - Cropped Image:")
    print(f"  Issue Type: {result2['issue_type']}")
    print(f"  Issue Detected: {result2['issue_detected']}")
    print(f"  Confidence: {result2['confidence_score']:.2f}")
    print(f"  Reasoning: {result2['reasoning']}")
    print()
    
    # Example 3: Partial Letters Unlit
    validation3 = {
        'is_readable': True,
        'resolution_ok': True,
        'is_blurry': False,
        'validation_passed': True,
        'width': 320,
        'height': 240
    }
    
    ai_analysis3 = {
        'is_lenskart_board': True,
        'signage_visible': True,
        'light_status': 'ON',
        'partial_letter_illumination': True,
        'image_quality': True,
        'is_blurry': False,
        'confidence_score': 0.85
    }
    
    result3 = classifier.classify(validation3, ai_analysis3)
    print("Example 3 - Partial Letters Unlit:")
    print(f"  Issue Type: {result3['issue_type']}")
    print(f"  Issue Detected: {result3['issue_detected']}")
    print(f"  Confidence: {result3['confidence_score']:.2f}")
    print(f"  Reasoning: {result3['reasoning']}")
    print()
    
    # Example 4: No Issue
    validation4 = {
        'is_readable': True,
        'resolution_ok': True,
        'is_blurry': False,
        'validation_passed': True,
        'width': 320,
        'height': 240
    }
    
    ai_analysis4 = {
        'is_lenskart_board': True,
        'signage_visible': True,
        'light_status': 'ON',
        'partial_letter_illumination': False,
        'image_quality': True,
        'is_blurry': False,
        'confidence_score': 0.92
    }
    
    result4 = classifier.classify(validation4, ai_analysis4)
    print("Example 4 - No Issue:")
    print(f"  Issue Type: {result4['issue_type']}")
    print(f"  Issue Detected: {result4['issue_detected']}")
    print(f"  Confidence: {result4['confidence_score']:.2f}")
    print(f"  Reasoning: {result4['reasoning']}")
    print()
    
    # Example 5: Batch classification
    batch_data = [
        {'validation_results': validation, 'ai_analysis': ai_analysis},
        {'validation_results': validation2, 'ai_analysis': ai_analysis2},
        {'validation_results': validation3, 'ai_analysis': ai_analysis3},
        {'validation_results': validation4, 'ai_analysis': ai_analysis4}
    ]
    
    batch_results = classifier.classify_batch(batch_data)
    summary = classifier.get_classification_summary(batch_results)
    
    print("Batch Classification Summary:")
    print(f"  Total Images: {summary['total_images']}")
    print(f"  With Issues: {summary['images_with_issues']}")
    print(f"  Without Issues: {summary['images_without_issues']}")
    print(f"  Average Confidence: {summary['average_confidence']:.2f}")
    print(f"  Category Breakdown:")
    for category, count in summary['category_breakdown'].items():
        print(f"    - {category}: {count}")
