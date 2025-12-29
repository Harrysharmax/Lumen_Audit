# ...existing code...
# AI Agent for Store Signage Illumination Compliance
# Main entry point and orchestrator for the application

import os
import sys
from pathlib import Path

from .config import Config
from .image_validator import ImageValidator
from .ai_inspector import AIInspector
from .audit_issue_detector import AuditIssueDetector
from .report_generator import ReportGenerator


class SignageComplianceAgent:
    """
    Main orchestrator for the store signage illumination compliance audit.
    
    Workflow:
    1. Read images from input folder
    2. Extract store code from filename
    3. Validate image quality (OpenCV)
    4. If valid, perform AI inspection
    5. AI identifies potential issues (not PASS/FAIL decisions)
    6. Collect all findings for human audit
    7. Generate structured audit report
    """
    
    # Supported image file extensions
    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg')
    
    def __init__(self, config=None):
        """
        Initialize the compliance audit agent.
        
        Args:
            config (Config, optional): Configuration object. If None, creates default config.
        """
        self.config = config or Config()
        self.validator = ImageValidator()
        self.inspector = AIInspector(self.config.api_key)
        self.issue_detector = AuditIssueDetector()
        self.report_generator = ReportGenerator()
        self.results = []
    
    def run_audit(self):
        """
        Execute the complete signage audit pipeline.
        
        Processes:
        - Discovers all valid image files in input folder
        - Performs image validation and AI inspection
        - Identifies issues for human audit
        - Generates structured audit report
        
        Returns:
            tuple: (results list, output report path)
        """
        print("\n" + "="*70)
        print("STORE SIGNAGE ILLUMINATION COMPLIANCE AUDIT")
        print("="*70)
        
        # Step 1: Discover and process images
        print(f"\nStep 1: Discovering images in '{self.config.image_folder}'...")
        image_files = self._discover_images()
        
        if not image_files:
            print("[!] Warning: No image files found in input folder.")
            return [], None
        
            print(f"[OK] Found {len(image_files)} image(s) to process")
        
        # Step 2: Process each image through the pipeline
        print(f"\nStep 2: Processing images through validation and AI inspection...")
        for idx, image_path in enumerate(image_files, 1):
            print(f"\n  [{idx}/{len(image_files)}] Processing: {os.path.basename(image_path)}")
            self._process_single_image(image_path)
        
        # Step 3: Generate report
        print(f"\nStep 3: Generating audit report...")
        output_path = self._generate_report()
        
        # Step 4: Summary
        print(f"\nStep 4: Audit Complete")
        self._print_summary()
        
        print("\n" + "="*70 + "\n")
        
        return self.results, output_path
    
    def _discover_images(self):
        
        image_files = []
        # Scan folder for supported image formats
        for filename in os.listdir(self.config.image_folder):
            if filename.lower().endswith(self.SUPPORTED_EXTENSIONS):
                image_path = os.path.join(self.config.image_folder, filename)
                if os.path.isfile(image_path):
                    image_files.append(image_path)
        # Sort by filename for consistent processing
        return sorted(image_files)
    
    def _process_single_image(self, image_path):
        """
        Process a single image through the audit pipeline.
        
        Pipeline Steps:
        1. Extract store code from filename
        2. Validate image quality (readability, resolution, blur)
        3. If validation passes, run AI inspection
        4. AI identifies potential issues (not decisions)
        5. Collect findings for human audit
        
        Args:
            image_path (str): Full path to image file
        """
        filename = os.path.basename(image_path)
        store_code = os.path.splitext(filename)[0]
        
        try:
            # ===== PHASE 1: Image Validation =====
            # Check if image is readable, meets resolution, and is not blurry
            print(f"    -> Running image validation...")
            validation_results = self.validator.validate_image(image_path)
            
            # Log validation results
            if validation_results.get('is_readable'):
                print(f"      [OK] Image readable: {validation_results['width']}x{validation_results['height']}")
                print(f"      [OK] Resolution OK: {validation_results['resolution_ok']}")
                print(f"      [OK] Blur check: {'SHARP' if not validation_results['is_blurry'] else 'BLURRY'}")
            else:
                print(f"      [X] Image validation failed: {validation_results.get('error')}")
            
            # ===== PHASE 2: AI Inspection =====
            # Only perform AI inspection if basic validation passed
            if validation_results.get('validation_passed', False):
                print(f"    -> Running AI signage inspection...")
                ai_analysis = self.inspector.analyze_signage(image_path)
                
                # Log AI analysis results
                print(f"      [OK] Signage visible: {ai_analysis.get('signage_visible', False)}")
                print(f"      [OK] Light status: {ai_analysis.get('light_status', 'UNCLEAR')}")
                print(f"      [OK] Partial illumination: {ai_analysis.get('partial_illumination', False)}")
                print(f"      [OK] AI Confidence: {ai_analysis.get('confidence_score', 0.0):.2f}")
            else:
                # If basic validation failed, create null AI analysis
                print(f"    -> Skipping AI inspection (image validation failed)")
                ai_analysis = {
                    'signage_visible': False,
                    'light_status': 'UNCLEAR',
                    'partial_illumination': None,
                    'image_relevance': False,
                    'image_quality': False,
                    'confidence_score': 0.0,
                    'detailed_explanation': 'AI inspection skipped due to image validation failure',
                    'api_used': 'none',
                    'error': None
                }
            
            # ===== PHASE 3: Issue Detection for Audit =====
            # AI identifies issues - HUMANS make final approval decisions
            print(f"    -> Detecting issues for audit...")
            audit_findings = self.issue_detector.detect_issues(validation_results, ai_analysis)
            
            # Log audit findings
            print(f"      [OK] Issue Detected: {audit_findings['issue_detected']}")
            print(f"      [OK] Issue Type: {audit_findings['issue_type']}")
            print(f"      [OK] AI Confidence: {audit_findings['confidence_score']:.2f}")
            print(f"      [OK] Manual Review: {audit_findings['manual_review_required']}")
            
            # ===== PHASE 4: Aggregate Audit Results =====
            # Combine all findings into a single audit record
            result = {
                'store_id': store_code,
                'filename': filename,
                # Validation results
                'is_readable': validation_results.get('is_readable'),
                'width': validation_results.get('width'),
                'height': validation_results.get('height'),
                'resolution_ok': validation_results.get('resolution_ok'),
                'is_blurry': validation_results.get('is_blurry'),
                'laplacian_variance': validation_results.get('laplacian_variance'),
                'validation_passed': validation_results.get('validation_passed'),
                'validation_error': validation_results.get('error'),
                # AI analysis results
                'signage_visible': ai_analysis.get('signage_visible'),
                'light_status': ai_analysis.get('light_status'),
                'partial_illumination': ai_analysis.get('partial_illumination'),
                'image_relevance': ai_analysis.get('image_relevance'),
                'image_quality': ai_analysis.get('image_quality'),
                'confidence_score': ai_analysis.get('confidence_score'),
                'ai_explanation': ai_analysis.get('detailed_explanation'),
                'ai_error': ai_analysis.get('error'),
                # Audit findings (NOT compliance decisions)
                'issue_detected': audit_findings.get('issue_detected'),
                'issue_type': audit_findings.get('issue_type'),
                'issue_description': audit_findings.get('issue_description'),
                'issue_confidence': audit_findings.get('confidence_score'),
                'manual_review_required': audit_findings.get('manual_review_required'),
                'audit_details': str(audit_findings.get('details', {}))
            }
            
            self.results.append(result)
        
        except Exception as e:
            # Capture any unexpected errors in processing
            print(f"    [X] Error processing image: {str(e)}")
            
            # Record error result
            error_result = {
                'store_id': store_code,
                'filename': filename,
                'is_readable': False,
                'validation_error': str(e),
                'issue_detected': True,
                'issue_type': 'unclear_image',
                'issue_description': f'Error during processing: {str(e)}',
                'manual_review_required': True
            }
            self.results.append(error_result)
    
    def _generate_report(self):
        """
        Generate the final Excel audit report.
        
        Returns:
            str: Path to generated Excel file
        """
        try:
            output_path = self.report_generator.generate_excel_report(
                self.results, 
                self.config.output_file
            )
            print(f"[OK] Report generated: {output_path}")
            return output_path
        except Exception as e:
            print(f"[X] Error generating report: {str(e)}")
            return None
    
    def _print_summary(self):
        """Print audit summary statistics."""
        total = len(self.results)
        issues_detected = sum(1 for r in self.results if r.get('issue_detected', False))
        requires_review = sum(1 for r in self.results if r.get('manual_review_required', False))
        
        # Count by issue type
        issue_counts = {}
        for r in self.results:
            issue_type = r.get('issue_type', 'unknown')
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        print(f"Audit Summary:")
        print(f"  • Total stores audited: {total}")
        print(f"  • Issues detected: {issues_detected} ({(issues_detected/total*100 if total else 0):.1f}%)")
        print(f"  • Require manual review: {requires_review} ({(requires_review/total*100 if total else 0):.1f}%)")
        print(f"  • Issue breakdown:")
        for issue_type, count in sorted(issue_counts.items()):
            print(f"    - {issue_type}: {count}")


def main():
    """
    Main entry point for the signage compliance audit application.
    Creates agent instance and runs the complete audit pipeline.
    """
    try:
        # Initialize agent with configuration
        agent = SignageComplianceAgent()
        
        # Run the complete audit pipeline
        results, output_path = agent.run_audit()
        
        # Exit with success
        sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\n[!] Audit cancelled by user.")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n[X] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()