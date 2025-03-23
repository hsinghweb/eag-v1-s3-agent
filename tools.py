# Python tools for Agentic AI Chrome Extension

import math
import re

def calculate(expression):
    """
    Perform mathematical calculations using Python.
    
    Args:
        expression (str): The mathematical expression to evaluate
        
    Returns:
        str: The result of the calculation or an error message
    """
    try:
        # Remove any characters that aren't part of a valid mathematical expression
        # Only allow numbers, operators, parentheses, and common math functions
        sanitized_expr = re.sub(r'[^0-9+\-*/().\s^]', '', expression)
        
        # Replace ^ with ** for exponentiation
        sanitized_expr = sanitized_expr.replace('^', '**')
        
        # Evaluate the expression
        result = eval(sanitized_expr, {"__builtins__": {}}, {"math": math})
        
        return f"Calculation result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"

def fibonacci(n):
    """
    Generate Fibonacci sequence up to n numbers.
    
    Args:
        n (int): Number of Fibonacci numbers to generate
        
    Returns:
        str: The Fibonacci sequence or an error message
    """
    try:
        # Validate input
        n = int(n)
        if n <= 0:
            return "Error: n must be a positive integer"
        
        # Generate Fibonacci sequence
        fibonacci_seq = []
        if n >= 1:
            fibonacci_seq.append(0)
        if n >= 2:
            fibonacci_seq.append(1)
        
        for i in range(2, n):
            fibonacci_seq.append(fibonacci_seq[i-1] + fibonacci_seq[i-2])
        
        return f"Fibonacci sequence ({n} numbers): {', '.join(map(str, fibonacci_seq))}"
    except Exception as e:
        return f"Error generating Fibonacci sequence: {str(e)}"

def exponential(numbers):
    """
    Calculate exponential values (e^x) for a list of numbers.
    
    Args:
        numbers (list): List of numbers to calculate exponential values for
        
    Returns:
        str: The exponential values or an error message
    """
    try:
        # Validate input
        if not isinstance(numbers, list):
            return "Error: Input must be a list of numbers"
        
        # Calculate exponential values
        results = []
        for num in numbers:
            results.append({
                "number": num,
                "exponential": math.exp(num)
            })
        
        # Format the results
        formatted_results = [f"e^{item['number']} = {item['exponential']}" for item in results]
        
        return f"Exponential values:\n{', '.join(formatted_results)}"
    except Exception as e:
        return f"Error calculating exponential values: {str(e)}"

# For testing purposes
if __name__ == "__main__":
    print(calculate("2^10 * 3.14"))
    print(fibonacci(10))
    print(exponential([1, 2, 3]))