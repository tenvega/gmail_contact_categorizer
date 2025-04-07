"""
Excel exporter for Gmail Contact Categorizer.
"""

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font
from gmail_contact_categorizer.exporters.base import BaseExporter


class ExcelExporter(BaseExporter):
    """Exports categorized contacts to an Excel file."""
    
    def export(self, categories, output='contact_categories.xlsx'):
        """
        Export categorized contacts to an Excel file.
        
        Args:
            categories (dict): Dictionary of categorized contacts.
            output (str, optional): Output filename. Defaults to 'contact_categories.xlsx'.
            
        Returns:
            str: Path to the exported Excel file.
        """
        # Prepare data for export
        export_data = self._prepare_export_data(categories)
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Export to Excel
        df.to_excel(output, index=False)
        
        # Apply formatting
        self._format_excel(output)
        
        return output
    
    def _format_excel(self, filename):
        """
        Apply formatting to the Excel file.
        
        Args:
            filename (str): Path to the Excel file.
        """
        try:
            # Load the workbook
            wb = load_workbook(filename)
            ws = wb.active
            
            # Style the header row
            header_fill = PatternFill(start_color='3366CC', end_color='3366CC', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True)
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            
            # Define category color fills
            category_fills = {
                'Family & Friends': PatternFill(start_color='E6FFE6', end_color='E6FFE6', fill_type='solid'),
                'Business Contacts': PatternFill(start_color='E6E6FF', end_color='E6E6FF', fill_type='solid'),
                'Clients': PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
            }
            
            # Find the category column index
            category_col = None
            for col_idx, cell in enumerate(ws[1], 1):
                if cell.value == 'Category':
                    category_col = col_idx
                    break
            
            # Apply conditional formatting based on category
            if category_col:
                for row_idx, row in enumerate(ws.iter_rows(min_row=2), 2):
                    category = row[category_col-1].value
                    if category in category_fills:
                        for cell in row:
                            cell.fill = category_fills[category]
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                
                adjusted_width = max_length + 2
                ws.column_dimensions[column].width = adjusted_width
            
            # Save the formatted workbook
            wb.save(filename)
            
        except Exception as e:
            print(f"Warning: Could not apply Excel formatting: {e}")
