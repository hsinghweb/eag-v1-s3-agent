import os
import json
import inspect
import importlib
import google.generativeai as genai
from dotenv import load_dotenv
import tools

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
        self.tool_manager = tools.ToolManager()
    
    def add_to_history(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def format_conversation(self):
        """Format the conversation history for the API."""
        formatted_history = []
        for message in self.conversation_history:
            formatted_history.append({"role": message["role"], "parts": [{"text": message["content"]}]})
        return formatted_history
    
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
        local_tools_plan = self.tool_manager.plan_with_local_tools(query)
        if local_tools_plan:
            print("\nExecuting with local tools:")
            return self.tool_manager.execute_local_plan(local_tools_plan)
        
        # If local tools can't handle it, use LLM for planning
        print("\nNo direct local tool match, using LLM for planning...")
        llm_response = self.get_llm_response(query)
        print("\nLLM Planning Response:")
        print(llm_response)
        
        # Parse tool calls from LLM response
        tool_calls = self.tool_manager.parse_tool_calls(llm_response)
        print("\nIdentified Tool Calls:")
        print(json.dumps(tool_calls, indent=2))
        
        # Execute tools in sequence
        previous_results = {}
        for tool_call in tool_calls:
            result = self.tool_manager.execute_tool(tool_call, previous_results)
            previous_results[tool_call['tool']] = result
            print(f"\nTOOL RESULT ({tool_call['tool']}):\n{result}")
        
        return previous_results

# Main execution
if __name__ == "__main__":
    agent = Agent()
    
    # Example query that requires multiple tool calls
    query = "Calculate the sum of exponential values of the first 6 Fibonacci numbers"
    
    print("QUERY:", query)
    agent.run_agent(query)