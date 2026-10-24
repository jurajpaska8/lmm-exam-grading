import base64
import io
import os
import html
from typing import List
from PIL.Image import Image
from visualizers.AssignmentVisualizer import AssignmentVisualizer
from models.validation_summary import ValidationSummary

class HtmlAssignmentVisualizer(AssignmentVisualizer):
    def visualize(self, images: List[Image], pdf_name: str, validation_summary: ValidationSummary) -> str:
        images_html = ""
        for idx, img in enumerate(images):
            buffered = io.BytesIO()
            # Convert to RGB to safely save as JPEG
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buffered, format="JPEG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            images_html += f'<img src="data:image/jpeg;base64,{img_b64}" style="max-width: 100%; border: 1px solid #ccc; margin-bottom: 20px;" alt="Page {idx+1}" /><br/>'

        meta = validation_summary.validation_metadata
        llm = validation_summary.llm_validation_response
        
        metadata_html = f"""
        <div class='section meta-section'>
            <h3>Validation Metadata</h3>
            <ul>
                <li><strong>Model used:</strong> {html.escape(meta.validation_model) if meta else 'N/A'}</li>
                <li><strong>Temperature:</strong> {meta.temperature if meta and meta.temperature is not None else 'N/A'}</li>
                <li><strong>Context Length:</strong> {meta.context_length if meta and meta.context_length is not None else 'N/A'}</li>
                <li><strong>Start Time:</strong> {meta.start_time.isoformat() if meta and meta.start_time else 'N/A'}</li>
                <li><strong>End Time:</strong> {meta.end_time.isoformat() if meta and meta.end_time else 'N/A'}</li>
                <li><strong>Duration (s):</strong> {f"{meta.duration:.2f}" if meta and meta.duration is not None else 'N/A'}</li>
            </ul>
        </div>
        """

        # Build student_html only if the required fields exist
        student_html = ""
        if llm and getattr(llm, 'extracted_student_name', None) and getattr(llm, 'paired_student_name', None):
            student_html = f"""
        <div class='section student-section'>
            <h3>Student Identification</h3>
            <ul>
                <li><strong>Extracted Student Name:</strong> {html.escape(llm.extracted_student_name)}</li>
                <li><strong>Paired Student Name:</strong> {html.escape(llm.paired_student_name)}</li>
                <li><strong>Pairing Confidence:</strong> {f"{llm.student_name_pairing_confidence:.2f}" if getattr(llm, 'student_name_pairing_confidence', None) else 'N/A'}</li>
            </ul>
        </div>
        """

        validations_html = "<div class='section validations-section'><h3>Sub-Assignment Validations</h3>"
        if llm and llm.validations:
            for val in llm.validations:
                extracted_text_section = ""
                if getattr(val, 'extracted_text', None):
                    extracted_text_section = f"<p><strong>Extracted Text:</strong></p><p style='background-color: #f0f0f0; padding: 8px; border-radius: 3px; font-style: italic;'>{html.escape(val.extracted_text)}</p>"
                
                validations_html += f"""
                <div class='validation-card'>
                    <h4>Task {html.escape(val.subassignment_id)} - Score: {val.percentage}</h4>
                    {extracted_text_section}
                    <p><strong>Validation:</strong></p>
                    <p>{html.escape(val.validation_text)}</p>
                </div>
                """
        else:
            validations_html += "<p>No sub-assignments found.</p>"
        validations_html += "</div>"
        
        right_panel_content = metadata_html + student_html + validations_html

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Validation: {html.escape(os.path.basename(pdf_name))}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f0f2f5;
            color: #333;
        }}
        h1 {{
            text-align: center;
            color: #444;
        }}
        .container {{
            display: flex;
            flex-direction: row;
            gap: 20px;
            height: 85vh;
        }}
        .left-panel, .right-panel {{
            flex: 1;
            overflow-y: auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: inherit;
            font-size: 15px;
            line-height: 1.6;
            margin: 0;
        }}
        /* Styling for markdown-like syntax */
        pre strong {{ font-weight: bold; color: #000; }}
        .section {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .section h3 {{
            margin-top: 0;
            color: #0056b3;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 5px;
        }}
        .section ul {{
            list-style-type: none;
            padding: 0;
            margin: 0;
        }}
        .section li {{
            margin-bottom: 8px;
        }}
        .validation-card {{
            background-color: #fff;
            border-left: 4px solid #28a745;
            padding: 12px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .validation-card h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .validation-card p {{
            margin: 0;
            white-space: pre-wrap;
            font-size: 14px;
            color: #555;
        }}
    </style>
</head>
<body>
    <h1>Assignment: {html.escape(os.path.basename(pdf_name))}</h1>
    <div class="container">
        <div class="left-panel">
            {images_html}
        </div>
        <div class="right-panel">
            {right_panel_content}
        </div>
    </div>
</body>
</html>"""
        return html_content

    def generate_front_page(self, model: str, folder: str, start_time: str, end_time: str, successful_count: int, prompt_text: str, parsed_files: List[str] = None) -> str:
        if parsed_files is None:
            parsed_files = []
        links_html = ""
        for file in parsed_files:
            file_name = html.escape(os.path.basename(file))
            links_html += f'<li><a href="{file_name}">{file_name}</a></li>\n'
            
        if not links_html:
            links_html = "<li>No files processed yet.</li>"
            
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Assignment Validation Summary</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background-color: #f0f2f5;
            color: #333;
        }}
        h1, h2 {{
            color: #444;
        }}
        .container {{
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 800px;
            margin: auto;
        }}
        .meta-info {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .meta-info strong {{
            display: inline-block;
            width: 200px;
        }}
        ul.file-list {{
            list-style-type: none;
            padding: 0;
        }}
        ul.file-list li {{
            margin: 10px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }}
        ul.file-list a {{
            text-decoration: none;
            color: #007bff;
            font-weight: bold;
        }}
        ul.file-list a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Assignment Validation Summary</h1>
        
        <div class="meta-info">
            <p><strong>Configured Model:</strong> {html.escape(model)}</p>
            <p><strong>Target Folder:</strong> {html.escape(folder)}</p>
            <p><strong>Total Files Processed:</strong> {len(parsed_files)}</p>
            <p><strong>Successfully Processed:</strong> {successful_count}</p>
            <p><strong>Start Time:</strong> {html.escape(start_time)}</p>
            <p><strong>End Time:</strong> {html.escape(end_time)}</p>
        </div>
        
        <h2>Processed Assignments</h2>
        <ul class="file-list">
            {links_html}
        </ul>
        
        <h2>Evaluation Prompt Template Used</h2>
        <div style="background-color: #fff; padding: 15px; border-radius: 5px; box-shadow: inset 0 0 5px rgba(0,0,0,0.05); border: 1px solid #ddd;">
            <pre style="white-space: pre-wrap; font-family: monospace; font-size: 13px;">{html.escape(prompt_text)}</pre>
        </div>
    </div>
</body>
</html>"""
        return html_content
