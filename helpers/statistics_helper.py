def calculate_correlation(array_1: list[float], array_2: list[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two arrays.
    
    Args:
        array_1: First array of float values
        array_2: Second array of float values
        
    Returns:
        Pearson correlation coefficient between -1 and 1.
        Returns 0 if correlation cannot be calculated (empty arrays, 
        different lengths, or zero variance in either array).
    """
    # Validate inputs
    if not array_1 or not array_2:
        return 0.0
    
    if len(array_1) != len(array_2):
        return 0.0
    
    if len(array_1) == 1:
        # Single element - cannot determine correlation
        return 0.0
    
    # Calculate means
    mean_1 = sum(array_1) / len(array_1)
    mean_2 = sum(array_2) / len(array_2)
    
    # Calculate deviations and products
    numerator = 0.0
    denominator_1 = 0.0
    denominator_2 = 0.0
    
    for x, y in zip(array_1, array_2):
        dev_1 = x - mean_1
        dev_2 = y - mean_2
        numerator += dev_1 * dev_2
        denominator_1 += dev_1 * dev_1
        denominator_2 += dev_2 * dev_2
    
    # Handle zero variance cases
    if denominator_1 == 0 or denominator_2 == 0:
        return 0.0
    
    # Calculate correlation
    correlation = numerator / (denominator_1 * denominator_2) ** 0.5
    
    return correlation