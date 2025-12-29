# Compliance Evaluator module for determining signage illumination compliance

class ComplianceEvaluator:
    """
    Determines compliance status based on image validation and AI inspection results.
    Uses rule-based logic to evaluate night-time illumination requirements.
    """
    
    # Compliance decision constants
    STATUS_PASS = "PASS"
    STATUS_FAIL = "FAIL"
    STATUS_ATTENTION_NEEDED = "ATTENTION NEEDED"
    
    def __init__(self):
        """Initialize the Compliance Evaluator with decision rules."""
        pass
    
    def evaluate_compliance(self, validation_results, ai_analysis):
        print("\n[DEBUG] Raw validation_results:", validation_results)
        print("[DEBUG] Raw ai_analysis:", ai_analysis)
        """
        Evaluate store signage compliance based on validation and AI inspection.
        
        Decision Logic:
        ===============
        FAIL Cases (Critical Issues):
        - Image validation failed (unreadable, too small, blurry)
        - Signage not visible in image
        - Image is not relevant/correct type
        - Light is OFF (non-compliant)
        
        ATTENTION NEEDED Cases (Minor Issues):
        - Partial illumination detected (some letters not fully lit)
        - Image quality is poor but analysis was possible
        - Confidence score is low (model uncertain)
        
        PASS Cases (Compliant):
        - Image is valid and readable
        - Signage is visible and relevant
        - Light is ON and fully illuminated
        - High confidence in analysis
        
        Args:
            validation_results (dict): Output from ImageValidator.validate_image()
                Expected keys: is_readable, width, height, resolution_ok, 
                              is_blurry, validation_passed
            
            ai_analysis (dict): Output from AIInspector.analyze_signage()
                Expected keys: signage_visible, light_status, partial_illumination,
                              image_relevance, image_quality, confidence_score,
                              detailed_explanation, error
        
        Returns:
            dict: Comprehensive compliance evaluation with keys:
                - compliance_status (str): "PASS", "FAIL", or "ATTENTION NEEDED"
                - primary_reason (str): Main reason for the decision
                - secondary_reasons (list): Additional findings
                - final_remarks (str): Detailed explanation for manual review
                - confidence_overall (float): Combined confidence score (0.0-1.0)
                - requires_manual_review (bool): Whether human review is needed
        """
        
        # Initialize evaluation results
        primary_reason = ""
        secondary_reasons = []
        compliance_status = self.STATUS_PASS
        confidence_overall = 0.5
        requires_manual_review = False
        print("[DEBUG] Initial compliance_status:", compliance_status)
        
        # =================================================================
        # PHASE 1: Check Image Validity (Critical Foundation)
        # =================================================================
        # If the image cannot be validated, we cannot assess compliance
        if not validation_results.get('is_readable', False):
            compliance_status = self.STATUS_FAIL
            primary_reason = "Image is not readable or file is corrupted"
            confidence_overall = 0.0
            requires_manual_review = True
            print("[DEBUG] FAIL: Image not readable. Reason:", primary_reason)
            final_remarks = (
                f"The image file could not be loaded: {validation_results.get('error', 'Unknown error')}. "
                f"Please verify the image file is valid and in a supported format (JPG, PNG)."
            )
            return {
                'compliance_status': compliance_status,
                'primary_reason': primary_reason,
                'secondary_reasons': secondary_reasons,
                'final_remarks': final_remarks,
                'confidence_overall': confidence_overall,
                'requires_manual_review': requires_manual_review
            }
        
        # =================================================================
        # PHASE 2: Check Image Quality (Resolution & Blur)
        # =================================================================
        # Resolution must meet minimum requirements for accurate analysis
        if not validation_results.get('resolution_ok', False):
            compliance_status = self.STATUS_FAIL
            primary_reason = "Image resolution below minimum requirement (500x300 pixels)"
            width = validation_results.get('width', 'Unknown')
            height = validation_results.get('height', 'Unknown')
            secondary_reasons.append(f"Actual resolution: {width}x{height}")
            requires_manual_review = True
            print("[DEBUG] FAIL: Resolution check failed. Reason:", primary_reason)
        
        # Blur significantly impacts AI analysis accuracy
        if validation_results.get('is_blurry', False):
            if compliance_status == self.STATUS_PASS:
                compliance_status = self.STATUS_ATTENTION_NEEDED
                primary_reason = "Image is blurry - analysis accuracy may be compromised"
                print("[DEBUG] ATTENTION NEEDED: Image is blurry.")
            else:
                secondary_reasons.append("Image is blurry - further compromises analysis")
                print("[DEBUG] Additional blur issue on already failed image.")
            laplacian_var = validation_results.get('laplacian_variance', 0)
            secondary_reasons.append(f"Laplacian variance (sharpness score): {laplacian_var:.2f} (threshold: 100)")
            requires_manual_review = True
        
        # =================================================================
        # PHASE 3: Check AI Analysis Results
        # =================================================================
        
        # Check if AI analysis encountered an error
        if ai_analysis.get('error') is not None:
            compliance_status = self.STATUS_FAIL
            primary_reason = "AI analysis failed"
            secondary_reasons.append(f"AI Error: {ai_analysis.get('error')}")
            requires_manual_review = True
            print("[DEBUG] FAIL: AI analysis error:", ai_analysis.get('error'))

        # --- 3-state logic for signage_visible ---
        signage_visible = ai_analysis.get('signage_visible', None)
        if signage_visible is False or signage_visible == 'no' or signage_visible == 'poor':
            # Major penalty: signage not visible or poor
            compliance_status = self.STATUS_FAIL
            if not primary_reason:
                primary_reason = "Signage is not visible or not in frame"
            else:
                secondary_reasons.append("Signage not visible in image")
            requires_manual_review = True
            print("[DEBUG] Major penalty: signage_visible=no/poor")
        elif signage_visible is None or signage_visible == 'unclear':
            # Small penalty: unclear, but never FAIL by itself
            if compliance_status == self.STATUS_PASS:
                compliance_status = self.STATUS_ATTENTION_NEEDED
                primary_reason = "Signage visibility is unclear - manual inspection recommended"
                print("[DEBUG] Small penalty: signage_visible=unclear")
            else:
                secondary_reasons.append("Signage visibility is unclear")
            requires_manual_review = True
        # else: signage_visible is True or 'yes' → no penalty

        # --- 3-state logic for light_status ---
        light_status = ai_analysis.get('light_status', 'UNCLEAR')
        if light_status in ['OFF', 'no', 'poor']:
            # Major penalty: light is off or poor
            compliance_status = self.STATUS_FAIL
            if not primary_reason:
                primary_reason = "Signage light is OFF (non-compliant with illumination requirements)"
            else:
                secondary_reasons.append("Signage light is OFF or poor")
            requires_manual_review = True
            print("[DEBUG] Major penalty: light_status=no/poor/OFF")
        elif light_status in ['UNCLEAR', 'unclear', None]:
            # Small penalty: unclear, but never FAIL by itself
            if compliance_status == self.STATUS_PASS:
                compliance_status = self.STATUS_ATTENTION_NEEDED
                secondary_reasons.append("Light status is unclear - manual inspection recommended")
                print("[DEBUG] Small penalty: light_status=unclear")
            else:
                secondary_reasons.append("Light status is unclear")
            requires_manual_review = True
        # else: light_status is 'ON' or 'yes' → no penalty
        
        # =================================================================
        # PHASE 5: Check for Partial Illumination (Quality Check)
        # =================================================================
        if ai_analysis.get('partial_illumination', False):
            # Some letters are not fully illuminated - minor non-compliance
            if compliance_status == self.STATUS_PASS:
                compliance_status = self.STATUS_ATTENTION_NEEDED
                primary_reason = "Partial letter illumination detected"
                print("[DEBUG] ATTENTION NEEDED: Partial illumination detected.")
            else:
                secondary_reasons.append("Some letters show partial illumination")
                print("[DEBUG] Additional: Partial illumination on already non-pass image.")
            requires_manual_review = True
        
        # =================================================================
        # PHASE 6: Check Image Quality Assessment from AI
        # =================================================================
        if not ai_analysis.get('image_quality', False):
            secondary_reasons.append("AI flagged image quality issues")
            if compliance_status == self.STATUS_PASS:
                compliance_status = self.STATUS_ATTENTION_NEEDED
                print("[DEBUG] ATTENTION NEEDED: AI flagged image quality issues.")
            else:
                print("[DEBUG] Additional: AI flagged image quality issues on already non-pass image.")
            requires_manual_review = True
        
        # =================================================================
        # PHASE 7: Confidence Score Analysis (Revised)
        # =================================================================
        ai_confidence = ai_analysis.get('confidence_score', 0.0)
        print(f"[DEBUG] AI confidence: {ai_confidence}")
        if ai_confidence < 0.25:
            secondary_reasons.append(f"Very low AI confidence ({ai_confidence:.2f}) - manual review required")
            requires_manual_review = True
            print("[DEBUG] MANUAL REVIEW: Confidence < 0.25")
        elif ai_confidence < 0.5:
            secondary_reasons.append(f"Low AI confidence ({ai_confidence:.2f}) - recommend review (soft penalty)")
            if compliance_status == self.STATUS_PASS:
                compliance_status = self.STATUS_ATTENTION_NEEDED
                print("[DEBUG] ATTENTION NEEDED: Confidence between 0.25 and 0.5 (soft penalty)")
        # confidence >= 0.5: no penalty, do nothing
        
        # =================================================================
        # PHASE 8: Compute Final Remarks
        # =================================================================
        final_remarks = self._generate_final_remarks(
            compliance_status, primary_reason, secondary_reasons,
            validation_results, ai_analysis
        )
        
        # Calculate overall confidence (weighted average)
        validation_confidence = 0.8 if validation_results.get('validation_passed', False) else 0.3
        confidence_overall = (validation_confidence * 0.4) + (ai_confidence * 0.6)
        print(f"[DEBUG] Final compliance_status: {compliance_status}")
        print(f"[DEBUG] Final primary_reason: {primary_reason}")
        print(f"[DEBUG] Final secondary_reasons: {secondary_reasons}")
        print(f"[DEBUG] Final confidence_overall: {confidence_overall}")
        print(f"[DEBUG] Final requires_manual_review: {requires_manual_review}")
        
        return {
            'compliance_status': compliance_status,
            'primary_reason': primary_reason if primary_reason else "Compliant with illumination requirements",
            'secondary_reasons': secondary_reasons,
            'final_remarks': final_remarks,
            'confidence_overall': round(confidence_overall, 2),
            'requires_manual_review': requires_manual_review
        }
    
    def _generate_final_remarks(self, status, primary_reason, secondary_reasons, 
                               validation_results, ai_analysis):
        """
        Generate detailed final remarks explaining the compliance decision.
        
        Args:
            status (str): Compliance status (PASS/FAIL/ATTENTION NEEDED)
            primary_reason (str): Primary reason for decision
            secondary_reasons (list): Additional reasons
            validation_results (dict): Image validation output
            ai_analysis (dict): AI inspection output
        
        Returns:
            str: Formatted final remarks for manual review
        """
        remarks = []
        
        # Status-specific header
        if status == self.STATUS_PASS:
            remarks.append("✓ COMPLIANT: Store signage meets night-time illumination requirements.")
        elif status == self.STATUS_FAIL:
            remarks.append("✗ NON-COMPLIANT: Store signage does not meet illumination requirements.")
        else:  # ATTENTION NEEDED
            remarks.append("⚠ ATTENTION NEEDED: Store signage requires manual verification.")
        
        remarks.append("")
        
        # Primary reason
        if primary_reason:
            remarks.append(f"Primary Finding: {primary_reason}")
        
        # Secondary reasons
        if secondary_reasons:
            remarks.append("\nAdditional Findings:")
            for i, reason in enumerate(secondary_reasons, 1):
                remarks.append(f"  {i}. {reason}")
        
        # Image validation summary
        remarks.append("\nImage Validation Summary:")
        remarks.append(f"  • Readable: {validation_results.get('is_readable', False)}")
        remarks.append(f"  • Resolution: {validation_results.get('width', 'N/A')}x{validation_results.get('height', 'N/A')} (Min: 500x300)")
        remarks.append(f"  • Quality: {'Sharp' if not validation_results.get('is_blurry', False) else 'Blurry'}")
        
        # AI Analysis summary
        remarks.append("\nAI Analysis Summary:")
        remarks.append(f"  • Signage Visible: {ai_analysis.get('signage_visible', False)}")
        remarks.append(f"  • Light Status: {ai_analysis.get('light_status', 'UNCLEAR')}")
        remarks.append(f"  • Partial Illumination: {ai_analysis.get('partial_illumination', False)}")
        remarks.append(f"  • Image Relevance: {ai_analysis.get('image_relevance', False)}")
        remarks.append(f"  • Confidence Score: {ai_analysis.get('confidence_score', 0.0):.2f}/1.0")
        
        # AI explanation
        if ai_analysis.get('detailed_explanation'):
            remarks.append(f"\nAI Explanation: {ai_analysis.get('detailed_explanation')}")
        
        # Recommendation
        remarks.append("\nRecommendation:")
        if status == self.STATUS_FAIL:
            remarks.append("  → Immediate action required. Store signage does not meet compliance standards.")
            remarks.append("  → Contact store manager to fix illumination or provide corrected image.")
        elif status == self.STATUS_ATTENTION_NEEDED:
            remarks.append("  → Manual review recommended. Send image to supervisor for visual verification.")
            remarks.append("  → If uncertain, request store to provide new image under better lighting.")
        else:  # PASS
            remarks.append("  → No action required. Store is compliant with illumination standards.")
        
        return "\n".join(remarks)
