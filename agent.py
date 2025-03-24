import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from tools import calculate, fibonacci, exponential, sum_values

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
model = genai.GenerativeModel('gemini-1.5-flash')

class Agent:
    def __init__(self):
        self.conversation_history = []
        self.available_tools = {
            "calculate": calculate,
            "fibonacci": fibonacci,
            "exponential": exponential,
            "sum_values": sum_values
        }
    
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
        # Look for tool calls in the format: TOOL_CALL[tool_name(parameters)]
        tool_calls = []
        
        # Simple parsing logic - in a real implementation, you might want to use regex or more robust parsing
        if "I need to use the following tools:" in response_text or "I'll use these tools:" in response_text:
            lines = response_text.split("\n")
            plan_lines = []
            tool_section = False
            
            for line in lines:
                if "I need to use the following tools:" in line or "I'll use these tools:" in line or "Here's my plan:" in line:
                    tool_section = True
                    plan_lines.append(line)
                elif tool_section and line.strip() and not line.startswith("Final answer:"):
                    plan_lines.append(line)
                    
                    # Check for tool names
                    for tool_name in self.available_tools.keys():
                        if tool_name in line.lower():
                            # Extract parameters - this is a simplified approach
                            if tool_name == "calculate" and "calculate" in line.lower():
                                # Extract the expression
                                parts = line.split("calculate", 1)[1].strip()
                                if parts:
                                    tool_calls.append({"tool": "calculate", "params": parts})
                            
                            elif tool_name == "fibonacci" and "fibonacci" in line.lower():
                                # Extract the number
                                parts = line.lower().split("fibonacci", 1)[1].strip()
                                try:
                                    n = int(''.join(filter(str.isdigit, parts)))
                                    tool_calls.append({"tool": "fibonacci", "params": n})
                                except:
                                    pass
                            
                            elif tool_name == "exponential" and "exponential" in line.lower():
                                # This would need more sophisticated parsing in a real implementation
                                if "fibonacci" in self.conversation_history[-2]["content"].lower():
                                    tool_calls.append({"tool": "exponential", "params": "fibonacci_result"})
                            
                            elif tool_name == "sum_values" and "sum" in line.lower():
                                if "exponential" in self.conversation_history[-2]["content"].lower():
                                    tool_calls.append({"tool": "sum_values", "params": "exponential_result"})
            
            # Print the plan
            if plan_lines:
                print("\nPLAN:")
                for line in plan_lines:
                    print(line)
                print()
        
        return tool_calls
    
    def execute_tool(self, tool_call, previous_results=None):
        """Execute a tool call and return the result."""
        tool_name = tool_call["tool"]
        params = tool_call["params"]
        
        if tool_name not in self.available_tools:
            return f"Error: Tool '{tool_name}' not found."
        
        tool_function = self.available_tools[tool_name]
        
        # Handle special parameter cases
        if params == "fibonacci_result" and previous_results and "fibonacci" in previous_results:
            params = previous_results["fibonacci"]
        elif params == "exponential_result" and previous_results and "exponential" in previous_results:
            params = previous_results["exponential"]
        
        # Log before calling the tool
        print(f"CALLING TOOL: {tool_name}")
        print(f"INPUT: {params}")
        
        # Call the tool
        result = tool_function(params)
        
        # Log after calling the tool
        print(f"OUTPUT: {result}\n")
        
        return result
    
    def get_llm_response(self, query):
        """Send query to Gemini API and return the response."""
        try:
            # Add user query to conversation history
            self.add_to_history("user", query)
            
            # Generate response using Gemini model
            response = model.generate_content(
                contents=self.format_conversation()
            )
            
            # Add AI response to conversation history
            self.add_to_history("assistant", response.text)
            
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def run_agent(self, query):
        """Run the agent with a user query."""
        # Send query to LLM for planning
        llm_response = self.get_llm_response(query)
        print("\nLLM RESPONSE:")
        print(llm_response)
        
        # Parse tool calls from LLM response
        tool_calls = self.parse_tool_calls(llm_response)
        print("\nTOOL CALLS:")
        print(tool_calls)
        
        # Execute tools in sequence
        previous_results = {}
        for tool_call in tool_calls:
            result = self.execute_tool(tool_call, previous_results)
            previous_results[tool_call['tool']] = result
            print(f"\nTOOL RESULT ({tool_call['tool']}):")
            print(result)
        
        return previous_results

# Main execution
if __name__ == "__main__":
    agent = Agent()
    
    # Example query that requires multiple tool calls
    query = "Calculate the sum of exponential values of the first 6 Fibonacci numbers"
    
    print("QUERY:", query)
    agent.run_agent(query)