# Agentic AI Chrome Extension

A Chrome extension that provides agentic AI capabilities using Google Gemini. This extension allows you to interact with an AI assistant that can perform complex tasks by using tools when needed.

## Features

- Chat interface to interact with Google Gemini AI
- Tool-using capabilities for tasks that require computation
- Support for multi-step reasoning
- Conversation history tracking
- API key management

## Available Tools

The extension currently supports the following Python-based tools:

1. **Calculate**: Perform mathematical calculations
   - Example: "Calculate 2^10 * 3.14"

2. **Fibonacci**: Generate Fibonacci sequence up to n numbers
   - Example: "Generate the first 10 Fibonacci numbers"

3. **Exponential**: Calculate exponential values (e^x) for a list of numbers
   - Example: "Calculate e^x for x = [1, 2, 3]"

## Installation

### From Source

1. Clone this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top-right corner
4. Click "Load unpacked" and select the directory containing this extension
5. The extension icon should appear in your browser toolbar

## Usage

1. Click on the extension icon to open the chat interface
2. Enter your Gemini API key in the field at the bottom and click "Save API Key"
   - You can get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Type your question or request in the input field and press Enter or click "Send"
4. The AI will respond and may use tools when necessary to complete complex tasks

## Example Queries

- "Calculate the sum of exponential values of the first 6 Fibonacci numbers"
- "What is the result of 2^10 divided by 3?"
- "Generate the first 8 Fibonacci numbers and calculate their average"

## Development

### Project Structure

- `manifest.json`: Extension configuration
- `popup.html`: Main UI for the extension
- `popup.js`: Frontend logic for the chat interface
- `background.js`: Background script for API communication and tool execution
- `styles.css`: Styling for the extension UI

## License

MIT
