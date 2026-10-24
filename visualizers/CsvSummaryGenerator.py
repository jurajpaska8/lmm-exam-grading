import csv
import io
from typing import List
from models.validation_summary import ValidationSummary

class CsvSummaryGenerator:
    def generate_csv(self, summaries: List[ValidationSummary]) -> str:
        """
        Generates a CSV string representation of the validation summaries.
        
        :param summaries: List of ValidationSummary objects
        :return: CSV formatted string
        """
        if not summaries:
            return ""

        # Collect all unique subassignment IDs to create columns
        subassignment_ids = set()
        for summary in summaries:
            if summary.llm_validation_response and summary.llm_validation_response.validations:
                for validation in summary.llm_validation_response.validations:
                    subassignment_ids.add(validation.subassignment_id)
        
        # Sort subassignment IDs for consistent column ordering
        # Sort using standard string sort which visually orders items like "T1", "T2" properly
        sorted_subassignments = sorted(list(subassignment_ids))
        
        # Setup headers
        headers = ["Student Name"] + sorted_subassignments + ["Filename", "Model", "Temperature"]
        
        output = io.StringIO()
        # Use lineterminator='\n' to prevent double spaces in windows resulting from default CRLF
        writer = csv.DictWriter(output, fieldnames=headers, lineterminator='\n')
        
        writer.writeheader()
        
        for summary in summaries:
            row = {}
            if summary.llm_validation_response:
                row["Student Name"] = getattr(summary.llm_validation_response, 'paired_student_name', None) or summary.filename
            else:
                row["Student Name"] = "Unknown"
            
            # Subassignments
            if summary.llm_validation_response and summary.llm_validation_response.validations:
                for validation in summary.llm_validation_response.validations:
                    row[validation.subassignment_id] = f"{validation.percentage:.2f}"
            
            row["Filename"] = summary.filename
            row["Model"] = summary.validation_metadata.validation_model if summary.validation_metadata else "Unknown"
            row["Temperature"] = summary.validation_metadata.temperature if summary.validation_metadata and summary.validation_metadata.temperature is not None else "Unknown"
            
            writer.writerow(row)
            
        return output.getvalue()
