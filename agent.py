import os
import json
import inspect
import importlib
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with your API key
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    print("Please create a .env file with your API key or set it in your environment.")
    exit(1)

genai.configure(api_key=API_KEY)

# Set up the model
model = genai.GenerativeModel('gemini-2.0-flash')

class Agent:
    def __init__(self):
        self.conversation_history = []
        self.available_tools = self.discover_tools()
    
    def discover_tools(self):
        """Dynamically discover available tools from tools.py"""
        try:
            tools_module = importlib.import_module('tools')
            tools = {}
            
            # Get all callable objects (functions) from tools module
            for name, obj in inspect.getmembers(tools_module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    # Get function documentation and parameters
                    doc = inspect.getdoc(obj) or ''
                    sig = inspect.signature(obj)
                    tools[name] = {
                        'function': obj,
                        'description': doc,
                        'parameters': list(sig.parameters.keys())
                    }
            return tools
        except ImportError:
            print("Error: Could not import tools module")
            return {}
    
    def add_to_history(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def format_conversation(self):
        """Format the conversation history for the API."""
        formatted_history = []
        for message in self.conversation_history:
            formatted_history.append({"role": message["role"], "parts": [{"text": message["content"]}]})
        return formatted_history
    
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
            print(f"Parameters: {json.dumps(params, indent=2)}")
            
            # Execute the tool
            result = tool_function(params)
            
            print(f"Result: {result}")
            print(f"=== Tool Execution Completed ===\n")
            
            return result
            
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def get_llm_response(self, query):
        """Send query to Gemini API and return the response."""
        try:
            print("\n=== LLM Call ===\nSending query to Gemini model...")
            
            # Add user query to conversation history
            self.add_to_history("user", query)
            
            # Generate response using Gemini model
            response = model.generate_content(
                contents=self.format_conversation()
            )
            
            # Add AI response to conversation history
            self.add_to_history("assistant", response.text)
            
            print("=== LLM Response Received ===\n")
            
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def run_agent(self, query):
        """Run the agent with a user query."""
        print("\n=== Starting Agent Execution ===")
        print("Query:", query)
        
        # First check if we can handle this with local tools
        local_tools_plan = self.plan_with_local_tools(query)
        if local_tools_plan:
            print("\nExecuting with local tools:")
            return self.execute_local_plan(local_tools_plan)
        
        # If local tools can't handle it, use LLM for planning
        print("\nNo direct local tool match, using LLM for planning...")
        llm_response = self.get_llm_response(query)
        print("\nLLM Planning Response:")
        print(llm_response)
        
        # Parse tool calls from LLM response
        tool_calls = self.parse_tool_calls(llm_response)
        print("\nIdentified Tool Calls:")
        print(json.dumps(tool_calls, indent=2))
        
        # Execute tools in sequence
        previous_results = {}
        for tool_call in tool_calls:
            result = self.execute_tool(tool_call, previous_results)
            previous_results[tool_call['tool']] = result
            print(f"\nTOOL RESULT ({tool_call['tool']}):\n{result}")
        
        return previous_results

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

# Main execution
if __name__ == "__main__":
    agent = Agent()
    
    # Example query that requires multiple tool calls
    query = "Calculate the sum of exponential values of the first 6 Fibonacci numbers"
    
    print("QUERY:", query)
    agent.run_agent(query)