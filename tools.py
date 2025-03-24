import math
import inspect
import importlib

class ToolManager:
    def __init__(self):
        self.available_tools = self.discover_tools()
    
    def discover_tools(self):
        """Dynamically discover available tools from this module"""
        tools = {}
        
        # Import the module itself to get access to its functions
        module = importlib.import_module(__name__)
        
        # Get all callable objects (functions) from this module
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith('_') and name not in ['ToolManager']:
                # Get function documentation and parameters
                doc = inspect.getdoc(obj) or ''
                sig = inspect.signature(obj)
                tools[name] = {
                    'function': obj,
                    'description': doc,
                    'parameters': list(sig.parameters.keys())
                }
        return tools
    
    def parse_tool_calls(self, response_text):
        """Parse the response to identify tool calls."""
        tool_calls = []
        
        if "I need to use" in response_text.lower() or "I'll use" in response_text.lower():
            lines = response_text.split("\n")
            for line in lines:
                line = line.lower().strip()
                # Look for tool mentions in the line
                for tool_name in self.available_tools.keys():
                    if tool_name.lower() in line:
                        # Extract potential parameters from the line
                        params_str = line[line.find(tool_name) + len(tool_name):].strip()
                        # Add tool call with raw parameter string
                        tool_calls.append({
                            "tool": tool_name,
                            "raw_params": params_str
                        })
        return tool_calls
    
    def execute_tool(self, tool_call, previous_results=None):
        """Execute a tool call and return the result."""
        tool_name = tool_call["tool"]
        raw_params = tool_call.get("raw_params", "")
        
        if tool_name not in self.available_tools:
            return f"Error: Tool '{tool_name}' not found."
        
        tool_info = self.available_tools[tool_name]
        tool_function = tool_info['function']
        
        try:
            # Handle parameter passing between tools
            if previous_results and tool_name in previous_results:
                params = previous_results[tool_name]
            else:
                # Convert parameters based on tool name
                if tool_name == 'fibonacci':
                    # For fibonacci, ensure we have an integer
                    try:
                        params = int(str(raw_params).strip())
                    except (ValueError, TypeError):
                        params = 6  # Default value
                elif tool_name in ['exponential', 'sum_values']:
                    # These functions expect lists
                    if isinstance(raw_params, list):
                        params = raw_params
                    elif isinstance(raw_params, (int, float)):
                        params = [raw_params]
                    else:
                        return f"Error: Invalid parameter type for {tool_name}"
                else:
                    # For other tools, try basic type conversion
                    params = raw_params
                    if isinstance(params, str):
                        params = params.strip()
                        # Try to convert to number if possible
                        try:
                            params = int(params)
                        except ValueError:
                            try:
                                params = float(params)
                            except ValueError:
                                pass
            
            # Log tool execution
            print(f"\n=== Local Tool Call: {tool_name} ===")
            print(f"Parameters: {params}")
            
            # Execute the tool
            result = tool_function(params)
            
            print(f"Result: {result}")
            print(f"=== Tool Execution Completed ===\n")
            
            return result
            
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def plan_with_local_tools(self, query):
        """Analyze query to see if it can be handled by local tools."""
        query_lower = query.lower()
        
        # Check for a sequence of operations
        if ('fibonacci' in query_lower or 'fib' in query_lower) and \
           ('exponential' in query_lower or 'exp' in query_lower or 'e^x' in query_lower) and \
           ('sum' in query_lower):
            # Extract number from query or use default
            try:
                n = int(''.join(filter(str.isdigit, query_lower)))
            except ValueError:
                n = 6  # Default value
            
            # Create tool call sequence
            return [
                {"tool": "fibonacci", "raw_params": n},  # Pass n directly as integer
                {"tool": "exponential", "raw_params": None},  # Will use previous result
                {"tool": "sum_values", "raw_params": None}  # Will use previous result
            ]
        
        return None

    def execute_local_plan(self, tool_calls):
        """Execute a sequence of local tool calls."""
        results = {}
        for i, tool_call in enumerate(tool_calls):
            # For first tool call, use raw parameters
            if i == 0:
                result = self.execute_tool(tool_call)
            else:
                # For subsequent calls, pass the previous tool's result
                prev_tool = tool_calls[i-1]['tool']
                if prev_tool in results and results[prev_tool] is not None:
                    # Pass previous result as raw_params
                    tool_call['raw_params'] = results[prev_tool]
                    result = self.execute_tool(tool_call)
                else:
                    result = f"Error: No valid result from previous tool {prev_tool}"
            
            results[tool_call['tool']] = result
            print(f"\nTOOL RESULT ({tool_call['tool']}):\n{result}")
        return results

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
        if not isinstance(numbers, list):
            if isinstance(numbers, (int, float)):
                numbers = [numbers]
            else:
                raise ValueError(f"Expected a number or list of numbers, got {type(numbers)}")
        
        results = [math.exp(num) for num in numbers]
        print(f"Calculated exponential values: {results}")
        return results
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