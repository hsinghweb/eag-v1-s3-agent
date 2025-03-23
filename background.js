// Background script for Agentic AI Assistant

// Gemini API endpoint
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

// Tool definitions
const tools = [
  {
    functionDeclarations: [
      {
        name: 'calculate',
        description: 'Perform mathematical calculations using Python',
        parameters: {
          type: 'object',
          properties: {
            expression: {
              type: 'string',
              description: 'The mathematical expression to evaluate'
            }
          },
          required: ['expression']
        }
      },
      {
        name: 'fibonacci',
        description: 'Generate Fibonacci sequence up to n numbers',
        parameters: {
          type: 'object',
          properties: {
            n: {
              type: 'integer',
              description: 'Number of Fibonacci numbers to generate'
            }
          },
          required: ['n']
        }
      },
      {
        name: 'exponential',
        description: 'Calculate exponential values (e^x) for a list of numbers',
        parameters: {
          type: 'object',
          properties: {
            numbers: {
              type: 'array',
              items: {
                type: 'number'
              },
              description: 'List of numbers to calculate exponential values for'
            }
          },
          required: ['numbers']
        }
      }
    ]
  }
];

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sendToGemini') {
    sendToGemini(request.message, request.history)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Indicates async response
  } else if (request.action === 'executeToolCall') {
    executeToolCall(request.toolCall)
      .then(result => sendResponse({ result }))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Indicates async response
  } else if (request.action === 'continueConversation') {
    continueConversation(request.history)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Indicates async response
  }
});

// Send message to Gemini API
async function sendToGeminiAPI(history) {
  try {
    // Get API key from storage
    const result = await chrome.storage.local.get(['geminiApiKey']);
    const apiKey = result.geminiApiKey;
    
    if (!apiKey) {
      throw new Error('API key not found');
    }
    
    // Prepare request body
    const requestBody = {
      contents: history,
      tools: tools,
      generationConfig: {
        temperature: 0.7,
        topP: 0.95,
        topK: 40,
        maxOutputTokens: 2048
      }
    };
    
    // Send request to Gemini API
    const response = await fetch(`${GEMINI_API_URL}?key=${apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`API Error: ${errorData.error.message}`);
    }
    
    const data = await response.json();
    
    // Check if there are tool calls
    if (data.candidates[0].content.parts && 
        data.candidates[0].content.parts.some(part => part.functionCall)) {
      // Extract tool calls
      const toolCalls = data.candidates[0].content.parts
        .filter(part => part.functionCall)
        .map(part => ({
          functionName: part.functionCall.name,
          parameters: part.functionCall.args
        }));
      
      return { toolCalls };
    } else {
      // Extract text response
      const text = data.candidates[0].content.parts
        .filter(part => part.text)
        .map(part => part.text)
        .join('\n');
      
      return { text };
    }
  } catch (error) {
    console.error('Error communicating with Gemini:', error);
    throw error;
  }
}

// Send message to Gemini API
async function sendToGemini(message, history) {
  return sendToGeminiAPI(history);
}

// Continue conversation with updated history
async function continueConversation(history) {
  return sendToGeminiAPI(history);
}

// Execute tool call
async function executeToolCall(toolCall) {
  try {
    const { functionName, parameters } = toolCall;
    const { PythonShell } = await import('python-shell');
    
    // Validate tool name
    const validTools = tools[0].functionDeclarations.map(t => t.name);
    if (!validTools.includes(functionName)) {
      throw new Error(`Unknown tool: ${functionName}`);
    }

    // Create script to execute Python tool
    const script = `
import sys
import json
from tools import ${functionName}

# Get parameters from command line arguments
params = json.loads(sys.argv[1])

# Call the tool function
result = ${functionName}(params)

# Print the result
print(result)
`;

    // Execute Python script
    const options = {
      mode: 'text',
      pythonPath: 'python',
      pythonOptions: ['-u'],
      scriptPath: '.',
      args: [JSON.stringify(parameters)]
    };

    return new Promise((resolve, reject) => {
      PythonShell.runString(script, options, (err, results) => {
        if (err) {
          console.error('Python execution error:', err);
          reject(`Error executing Python tool: ${err.message}`);
        } else {
          resolve(results[results.length - 1]);
        }
      });
    });
  } catch (error) {
    console.error('Error executing tool call:', error);
    throw error;
  }
}

// Python calculation tool
async function calculateWithPython(expression) {
  try {
    // Create a safe version of the expression
    const safeExpression = expression.replace(/[^0-9+\-*/().\s]/g, '');
    
    // Use JavaScript's eval for simple calculations (in a real extension, you'd use a safer method)
    // In a production environment, you would call a Python backend service
    const result = eval(safeExpression);
    
    return `Calculation result: ${result}`;
  } catch (error) {
    return `Error calculating: ${error.message}`;
  }
}

// Generate Fibonacci sequence
async function generateFibonacci(n) {
    try {
      const fibonacci = [];
      if (n >= 1) fibonacci.push(0);
      if (n >= 2) fibonacci.push(1);
      
      for (let i = 2; i < n; i++) {
        fibonacci.push(fibonacci[i-1] + fibonacci[i-2]);
      }
      
      return `Fibonacci sequence (${n} numbers): ${fibonacci.join(', ')}`;
    } catch (error) {
      return `Error generating Fibonacci sequence: ${error.message}`;
    }
  }
  
  // Calculate exponential values
  async function calculateExponential(numbers) {
    try {
      const results = numbers.map(num => {
        return {
          number: num,
          exponential: Math.exp(num)
        };
      });
      
      return `Exponential values: ${JSON.stringify(results)}`;
    } catch (error) {
      return `Error calculating exponential values: ${error.message}`;
    }
  }