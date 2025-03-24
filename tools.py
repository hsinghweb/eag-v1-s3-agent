import math

def calculate(expression):
    """
    Evaluates a mathematical expression.
    
    Args:
        expression (str): A string containing a mathematical expression
        
    Returns:
        float: The result of the calculation
    """
    print(f"Entering calculate with expression: {expression}")
    try:
        # Using eval is generally not recommended for security reasons,
        # but for this simple example, we'll use it with caution
        # In a production environment, you'd want to use a safer alternative
        result = eval(expression)
        return result
    except Exception as e:
        print(f"Exiting calculate with error: {str(e)}")
        return f"Error in calculation: {str(e)}"

def fibonacci(n):
    """
    Generates the first n numbers in the Fibonacci sequence.
    
    Args:
        n (int): The number of Fibonacci numbers to generate
        
    Returns:
        list: A list containing the first n Fibonacci numbers
    """
    print(f"Entering fibonacci with n: {n}")
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
    
    print(f"Exiting fibonacci with sequence: {fib_sequence}")
    return fib_sequence

def exponential(numbers):
    """
    Calculates e^x for each number in the input list.
    
    Args:
        numbers (list): A list of numbers for which to calculate e^x
        
    Returns:
        list: A list containing e^x for each input number
    """
    print(f"Entering exponential with numbers: {numbers}")
    try:
        return [math.exp(num) for num in numbers]
    except Exception as e:
        print(f"Exiting exponential with error: {str(e)}")
        return f"Error in exponential calculation: {str(e)}"

def sum_values(numbers):
    """
    Calculates the sum of a list of numbers.
    
    Args:
        numbers (list): A list of numbers to sum
        
    Returns:
        float: The sum of the input numbers
    """
    print(f"Entering sum_values with numbers: {numbers}")
    try:
        return sum(numbers)
    except Exception as e:
        print(f"Exiting sum_values with error: {str(e)}")
        return f"Error in sum calculation: {str(e)}"