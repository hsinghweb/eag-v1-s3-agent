import json
import logging
from typing import Dict, List, Any, Optional
from tools import fibonacci, exponential, calculate
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AgentFramework')

class Agent:
    def __init__(self, api_key: str = None):
        load_dotenv()
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY not found in environment variables')
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.tools = {
            'fibonacci': fibonacci,
            'exponential': exponential,
            'calculate': calculate
        }
        self.conversation_history = []

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse the model's response to identify tool calls."""
        try:
            # First try to parse as JSON
            try:
                tool_calls = json.loads(response)
                if isinstance(tool_calls, dict):
                    return tool_calls.get('tool_calls', [])
            except json.JSONDecodeError:
                pass

            # If JSON parsing fails, try to extract tool calls from text
            import re
            tool_pattern = r'"tool_name"\s*:\s*"([^"]+)"[^{]*"params"\s*:\s*({[^}]+})'            
            matches = re.finditer(tool_pattern, response)
            
            tool_calls = []
            for match in matches:
                tool_name = match.group(1)
                try:
                    params = json.loads(match.group(2))
                    tool_calls.append({
                        'tool_name': tool_name,
                        'params': params
                    })
                except json.JSONDecodeError:
                    continue
            
            return tool_calls

        except Exception as e:
            logger.error(f"Failed to parse tool calls: {e}")
            return []

    def _substitute_results(self, params: Dict[str, Any], previous_result: Dict[str, Any]) -> Dict[str, Any]:
        """Replace result placeholders with actual values from previous tool execution."""
        new_params = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                if 'sequence' in previous_result:
                    new_params[key] = previous_result['sequence']
                elif isinstance(previous_result, list):
                    if key == 'expression':
                        # Format exponential values into a sum expression
                        values = [str(item.get('exponential', item.get('number', 0))) for item in previous_result]
                        new_params[key] = ' + '.join(values)
                    elif isinstance(previous_result, list):
                        new_params[key] = [item.get('exponential', item.get('number', 0)) for item in previous_result]
                    else:
                        new_params[key] = value
                else:
                    new_params[key] = value
            else:
                new_params[key] = value
        return new_params

    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        try:
            # Validate and convert parameters based on tool type
            if tool_name == 'exponential':
                if 'numbers' in params:
                    params['numbers'] = [float(n) if isinstance(n, str) else n for n in params['numbers']]
            elif tool_name == 'fibonacci':
                if 'n' in params:
                    params['n'] = int(params['n']) if isinstance(params['n'], str) else params['n']
            elif tool_name == 'calculate':
                if 'expression' not in params:
                    return {"error": "Missing required parameter: expression"}

            tool_fn = self.tools[tool_name]
            result = tool_fn(params)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query using Gemini and execute required tools."""
        try:
            # Add user query to conversation history
            self.conversation_history.append({"role": "user", "content": query})

            # Get model's response
            response = await self.model.generate_content_async([
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"""
                            Based on this query: {query}
                            Available tools: {list(self.tools.keys())}
                            Return a JSON with tool_calls array containing sequence of tools to use.
                            Each tool call should have: tool_name and params.
                            """
                        }
                    ]
                }
            ]
            )

            # Parse tool calls from response
            tool_calls = self._parse_tool_calls(response.text)
            if not tool_calls:
                return {"error": "No tool calls identified"}

            # Execute tools in sequence and handle result chaining
            results = []
            previous_result = None
            for tool_call in tool_calls:
                tool_name = tool_call.get('tool_name')
                params = tool_call.get('params', {})
                
                if not tool_name:
                    continue

                # Replace placeholders with previous results if needed
                if previous_result:
                    params = self._substitute_results(params, previous_result)

                result = self._execute_tool(tool_name, params)
                previous_result = result
                results.append({
                    "tool": tool_name,
                    "params": params,
                    "result": result
                })

            # Generate final answer using results
            final_prompt = f"""
            Based on the query: {query}
            And these tool results: {json.dumps(results)}
            Provide a natural language answer.
            """
            final_response = await self.model.generate_content_async([
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": final_prompt
                        }
                    ]
                }
            ])
            
            return {
                "answer": final_response.text,
                "steps": results
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    import asyncio
    import os
    
    async def main():
        # Get API key from environment variable
        api_key = 'AIzaSyBUK_bEDOm4wP4M2DnxsmVHW3mkL2QjGFQ'
        if not api_key:
            print("Please set GEMINI_API_KEY environment variable")
            return

        agent = Agent(api_key)
        query = "Calculate the sum of exponential values of first 6 Fibonacci numbers"
        result = await agent.process_query(query)
        print(json.dumps(result, indent=2))

    asyncio.run(main())