document.addEventListener('DOMContentLoaded', function() {
  const chatContainer = document.getElementById('chatContainer');
  const userInput = document.getElementById('userInput');
  const sendButton = document.getElementById('sendButton');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const saveApiKeyButton = document.getElementById('saveApiKey');
  
  let conversationHistory = [];
  let apiKey = '';
  
  // Load API key from storage
  chrome.storage.local.get(['geminiApiKey'], function(result) {
    if (result.geminiApiKey) {
      apiKey = result.geminiApiKey;
      apiKeyInput.value = apiKey;
    }
  });
  
  // Save API key
  saveApiKeyButton.addEventListener('click', function() {
    apiKey = apiKeyInput.value.trim();
    if (apiKey) {
      chrome.storage.local.set({ geminiApiKey: apiKey }, function() {
        addMessage('API key saved successfully!', 'ai-message');
      });
    } else {
      addMessage('Please enter a valid API key', 'ai-message');
    }
  });
  
  // Send message when button is clicked
  sendButton.addEventListener('click', sendMessage);
  
  // Send message when Enter key is pressed (Shift+Enter for new line)
  userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  function sendMessage() {
    const userMessage = userInput.value.trim();
    if (!userMessage) return;
    
    // Check if API key is available
    if (!apiKey) {
      addMessage('Please enter your Gemini API key first', 'ai-message');
      return;
    }
    
    // Add user message to chat
    addMessage(userMessage, 'user-message');
    
    // Add user message to conversation history
    conversationHistory.push({ role: 'user', parts: [{ text: userMessage }] });
    
    // Clear input field
    userInput.value = '';
    
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
    chatContainer.appendChild(loadingDiv);
    
    // Send message to background script
    chrome.runtime.sendMessage({
      action: 'sendToGemini',
      message: userMessage,
      history: conversationHistory
    }, function(response) {
      // Remove loading indicator
      chatContainer.removeChild(loadingDiv);
      
      if (response.error) {
        addMessage(`Error: ${response.error}`, 'ai-message');
        return;
      }
      
      // Handle tool calls if present
      if (response.toolCalls && response.toolCalls.length > 0) {
        handleToolCalls(response.toolCalls);
      } else {
        // Add AI response to chat
        addMessage(response.text, 'ai-message');
        
        // Add AI response to conversation history
        conversationHistory.push({ role: 'model', parts: [{ text: response.text }] });
      }
    });
  }
  
  function handleToolCalls(toolCalls) {
    // Display tool calls in the chat
    toolCalls.forEach(toolCall => {
      const toolMessage = `Tool Call: ${toolCall.functionName}\nParameters: ${JSON.stringify(toolCall.parameters, null, 2)}`;
      addMessage(toolMessage, 'tool-message');
      
      // Send tool call to background script for execution
      chrome.runtime.sendMessage({
        action: 'executeToolCall',
        toolCall: toolCall,
        history: conversationHistory
      }, function(response) {
        if (response.error) {
          addMessage(`Tool Error: ${response.error}`, 'tool-message');
          return;
        }
        
        // Display tool result
        const resultMessage = `Tool Result: ${response.result}`;
        addMessage(resultMessage, 'tool-message');
        
        // Add tool call and result to conversation history
        conversationHistory.push({ 
          role: 'function', 
          parts: [{ text: response.result }],
          functionResponse: { name: toolCall.functionName }
        });
        
        // Continue the conversation with the tool result
        continueConversation();
      });
    });
  }
  
  function continueConversation() {
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
    chatContainer.appendChild(loadingDiv);
    
    // Send updated conversation to background script
    chrome.runtime.sendMessage({
      action: 'continueConversation',
      history: conversationHistory
    }, function(response) {
      // Remove loading indicator
      chatContainer.removeChild(loadingDiv);
      
      if (response.error) {
        addMessage(`Error: ${response.error}`, 'ai-message');
        return;
      }
      
      // Handle tool calls if present
      if (response.toolCalls && response.toolCalls.length > 0) {
        handleToolCalls(response.toolCalls);
      } else {
        // Add AI response to chat
        addMessage(response.text, 'ai-message');
        
        // Add AI response to conversation history
        conversationHistory.push({ role: 'model', parts: [{ text: response.text }] });
      }
    });
  }
  
  function addMessage(text, className) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    
    // Check if the message contains code blocks
    if (text.includes('```')) {
      const parts = text.split(/```(\w*\n|\n)?/);
      let html = '';
      
      for (let i = 0; i < parts.length; i++) {
        if (i % 2 === 0) {
          // Regular text
          html += `<p>${formatText(parts[i])}</p>`;
        } else {
          // Code block
          html += `<div class="code-block">${parts[i]}</div>`;
        }
      }
      
      messageDiv.innerHTML = html;
    } else {
      messageDiv.innerHTML = formatText(text);
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  
  function formatText(text) {
    // Convert line breaks to <br>
    return text.replace(/\n/g, '<br>');
  }
});