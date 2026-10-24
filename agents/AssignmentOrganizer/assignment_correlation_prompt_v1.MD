# Overview
Read student assignment image and determine which student it belongs to. 

# Rules for name extraction
1) Student name is written on the top of the page in handwriting. 
2) Name consist of at least first name and last name. 
3) Before name there is a word "Name:" 

# Student names rules
1) Student names are provided in a comma-separated list as part of this prompt.
2) Find closest match of the name on the scanned image to the names in the provided list and return name from the list.
        
# Output format:
1) Provide the student full name (student_name), index (student_idx), and confidence score (confidence_score) for the association . Name should be exactly as in the provided list of student names.
2) If student name is not readable, provide empty string and confidence score of 0 and student_idx = -1, set is_illegible_name to true
3) If student name is blank, provide empty string and confidence score of 1. Set is_blank_name to true and student_idx = -1


# Arguments
Student names list: ~~~STUDENT_NAMES~~~