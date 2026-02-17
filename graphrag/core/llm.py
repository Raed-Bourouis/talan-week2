"""LLM service using Ollama."""
import ollama
from typing import List, Dict, Any, Optional


class LLMService:
    """Service for interacting with Ollama LLM."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.1"):
        """Initialize the LLM service.
        
        Args:
            host: Ollama server host
            model: Model name to use
        """
        self.client = ollama.Client(host=host)
        self.model = model
    
    def generate(self, prompt: str, system: Optional[str] = None, 
                temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options=options
        )
        
        return response["message"]["content"]
    
    def chat(self, messages: List[Dict[str, str]], 
            temperature: float = 0.7) -> str:
        """Chat with the LLM using a conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={"temperature": temperature}
        )
        
        return response["message"]["content"]
    
    def generate_with_context(self, query: str, context: List[str], 
                             system: Optional[str] = None) -> str:
        """Generate text using retrieved context.
        
        Args:
            query: User query
            context: List of context strings
            system: Optional system message
            
        Returns:
            Generated response
        """
        context_text = "\n\n".join([f"Context {i+1}: {ctx}" 
                                   for i, ctx in enumerate(context)])
        
        prompt = f"""Based on the following context, answer the question.

{context_text}

Question: {query}

Answer:"""
        
        return self.generate(prompt, system=system)
