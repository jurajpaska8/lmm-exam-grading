import re

def get_parameters(prompt: str) -> list:
    """
    Extracts parameters from a prompt string in the format "~~~PARAMETER~~~".
    
    Args:
        prompt (str): The input prompt containing parameters.
        
    Returns:
        list: A list of the parameter names (without ~~~)
    """
    parameters = []
    
    # regex explanation:
    # ~~~       : matches the literal prefix
    # (         : starts a capturing group
    #   .*?     : matches any character (non-greedy) to stop at the next ~~~
    # )         : ends the capturing group
    # ~~~       : matches the literal suffix
    pattern = r"~~~(.*?)~~~"
    
    # findall returns a list of the captured groups (the text inside ~~~)
    matches = re.findall(pattern, prompt)
        
    return matches

def load_prompt_template(file_path: str) -> str:
    """
    Loads a prompt template from a file.
    
    Args:
        file_path (str): The path to the prompt template file.
    Returns:
        str: The content of the prompt template.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        template = file.read()
    return template

def fill_prompt_template(template: str, parameters: dict) -> str:
    """
    Fills a prompt template with provided parameters.
    
    Args:
        template (str): The prompt template containing placeholders in the format "~~~PARAMETER~~~".
        parameters (dict): A dictionary where keys are parameter names and values are the values to replace in the template.
        
    Returns:
        str: The filled prompt with all placeholders replaced by their corresponding values.
    """
    filled_prompt = template
    for key, value in parameters.items():
        placeholder = f"~~~{key}~~~"
        filled_prompt = filled_prompt.replace(placeholder, str(value))

    if re.search(r"~~~.*?~~~", filled_prompt):
        raise ValueError("Not all parameters were filled in the prompt template.")
    return filled_prompt