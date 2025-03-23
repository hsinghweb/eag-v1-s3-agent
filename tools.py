# Python tools for Agentic AI Chrome Extension

import math
import re
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AgentTools')

def calculate(params):
    """
    Perform mathematical calculations using Python.
    
    Args:
        params (dict): Dictionary containing the expression to evaluate
        
    Returns:
        dict: The result of the calculation or an error message
    """
    try:
        expression = params['expression']
        logger.info(f"Called calculate with expression={expression}")
        
        # Remove any characters that aren't part of a valid mathematical expression
        sanitized_expr = re.sub(r'[^0-9+\-*/().\s^]', '', expression)
        
        # Replace ^ with ** for exponentiation
        sanitized_expr = sanitized_expr.replace('^', '**')
        
        # Evaluate the expression
        result = eval(sanitized_expr, {"__builtins__": {}}, {"math": math})
        
        output = {"result": result}
        logger.info(f"calculate output: {output}")
        return output
    except Exception as e:
        error = {"error": str(e)}
        logger.error(f"calculate error: {error}")
        return error

def fibonacci(params):
    """
    Generate Fibonacci sequence up to n numbers.
    
    Args:
        params (dict): Dictionary containing n (number of Fibonacci numbers to generate)
        
    Returns:
        dict: The Fibonacci sequence or an error message
    """
    try:
        n = params['n']
        logger.info(f"Called fibonacci with n={n}")
        
        # Validate input
        n = int(n)
        if n <= 0:
            error = {"error": "n must be a positive integer"}
            logger.error(f"fibonacci error: {error}")
            return error
        
        # Generate Fibonacci sequence
        sequence = []
        if n >= 1:
            sequence.append(0)
        if n >= 2:
            sequence.append(1)
        
        for i in range(2, n):
            sequence.append(sequence[i-1] + sequence[i-2])
        
        output = {"sequence": sequence}
        logger.info(f"fibonacci output: {output}")
        return output
    except Exception as e:
        error = {"error": str(e)}
        logger.error(f"fibonacci error: {error}")
        return error

def exponential(params):
    """
    Calculate exponential values (e^x) for a list of numbers.
    
    Args:
        params (dict): Dictionary containing list of numbers to calculate exponential values for
        
    Returns:
        list: List of dictionaries containing the numbers and their exponential values
    """
    try:
        numbers = params['numbers']
        logger.info(f"Called exponential with numbers={numbers}")
        
        # Calculate exponential values
        results = []
        for num in numbers:
            exp_value = math.exp(num)
            results.append({
                "number": num,
                "exponential": exp_value
            })
        
        logger.info(f"exponential output: {results}")
        return results
    except Exception as e:
        error = {"error": str(e)}
        logger.error(f"exponential error: {error}")
        return error