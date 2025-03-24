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
        
        # Check if query can be handled by local tools
        local_plan = self.tool_manager.plan_with_local_tools(query)
        if local_plan:
            print("\nExecuting local tool plan...")
            return self.tool_manager.execute_local_plan(local_plan)
        
        # Initialize results storage
        all_results = []
        current_query = query
        max_iterations = 3  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            print(f"\n=== Iteration {iteration + 1} ===")
            print("Current Query:", current_query)
            
            # Get next steps from LLM
            print("\nGetting next steps from LLM...")
            llm_response = self.get_llm_response(current_query)
            print("\nLLM Response:")
            print(llm_response)
            
            # Parse and execute tool calls
            tool_calls = self.tool_manager.parse_tool_calls(llm_response)
            if not tool_calls:
                # No more tools to execute, we're done
                all_results.append({
                    "iteration": iteration + 1,
                    "query": current_query,
                    "llm_response": llm_response,
                    "final_result": True
                })
                break
            
            # Execute tools and collect results
            iteration_results = {}
            for tool_call in tool_calls:
                result = self.tool_manager.execute_tool(tool_call, iteration_results)
                iteration_results[tool_call['tool']] = result
                print(f"\nTOOL RESULT ({tool_call['tool']}):\n{result}")
            
            # Store results for this iteration
            all_results.append({
                "iteration": iteration + 1,
                "query": current_query,
                "llm_response": llm_response,
                "tool_results": iteration_results
            })
            
            # Prepare next query with context of all previous interactions
            current_query = f"Previous interactions:\n{json.dumps(all_results, indent=2)}\n\nBased on these results, what should be done next?"
        
        return all_results

# Main execution
if __name__ == "__main__":
    agent = Agent()
    
    # Example query that requires multiple tool calls
    system_message = "You are a helpful math assistant and can identify the steps for a given calculation problem. Just response with the required steps to solve the given problem.."
    agent.add_to_history("system", system_message)
    query = "Calculate the sum of exponential values of the first 6 Fibonacci numbers"
    
    print("QUERY:", query)
    agent.run_agent(system_message + query)