# Utility functions for the AI agent

import pandas as pd
import os

def generate_excel_report(results, output_path):
    """
    Generate an Excel report from the analysis results.
    
    Args:
        results (list): List of dictionaries containing analysis results
        output_path (str): Path to save the Excel file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save to Excel
    df.to_excel(output_path, index=False)
    print(f"Excel report saved to {output_path}")