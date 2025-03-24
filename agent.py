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
        
        # Initialize results storage
        all_results = []
        current_query = query
        max_iterations = 3  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            print(f"\n=== Iteration {iteration + 1} ===")
            print("Current Query:", current_query)
            
            # Always get initial plan from LLM first
            print("\nGetting next steps from LLM...")
            llm_response = self.get_llm_response(current_query)
            print("\nLLM Response:")
            print(llm_response)
            
            # Store LLM response in results
            current_iteration = {
                "iteration": iteration + 1,
                "query": current_query,
                "llm_response": llm_response
            }
            
            # Parse and execute tool calls if any
            tool_calls = self.tool_manager.parse_tool_calls(llm_response)
            if tool_calls:
                # Execute tools sequentially and collect results
                iteration_results = {}
                for tool_call in tool_calls:
                    result = self.tool_manager.execute_tool(tool_call, iteration_results)
                    iteration_results[tool_call['tool']] = result
                    print(f"\nTOOL RESULT ({tool_call['tool']}):\n{result}")
                
                current_iteration["tool_results"] = iteration_results
            else:
                # No more tools to execute, mark as final
                current_iteration["final_result"] = True
                all_results.append(current_iteration)
                break
            
            # Add current iteration results to history
            all_results.append(current_iteration)
            
            # Prepare next query with complete interaction history
            history_context = json.dumps(all_results, indent=2)
            current_query = f"Previous interactions:\n{history_context}\n\nBased on these results and previous steps, what should be done next? If all steps are complete, please indicate that."
        
        return all_results

# Main execution
if __name__ == "__main__":
    agent = Agent()
    
    # Example query that requires multiple tool calls
    system_message = "You are a helpful math assistant and can identify the steps for a given calculation problem. Just response with the required steps to solve the given problem.."
    query = "Calculate the sum of exponential values of the first 6 Fibonacci numbers"
    
    print("QUERY:", query)
    agent.run_agent(system_message + query)