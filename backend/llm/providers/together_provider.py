#!/usr/bin/env python3
"""
Together.ai Provider for OneVice
Primary LLM provider for data sovereignty and cost optimization
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TogetherUsage:
    """Token usage statistics from Together.ai"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class TogetherProvider:
    """
    Together.ai API provider with streaming and function calling support
    Optimized for Mixtral and Llama 3 models
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.together.xyz/v1"
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self.session
    
    async def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Complete a chat conversation using Together.ai
        
        Args:
            model: Together model name (e.g., "mistralai/Mixtral-8x7B-Instruct-v0.1")
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            functions: Function definitions for function calling
            stream: Whether to stream the response
        """
        
        session = await self._get_session()
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        # Add function calling if supported
        if functions and self._supports_function_calling(model):
            payload["tools"] = [
                {
                    "type": "function",
                    "function": func
                }
                for func in functions
            ]
            payload["tool_choice"] = "auto"
        
        try:
            if stream:
                return await self._complete_streaming(session, payload)
            else:
                return await self._complete_sync(session, payload)
                
        except Exception as e:
            logger.error(f"Together.ai completion error: {e}")
            raise
    
    async def _complete_sync(self, session: aiohttp.ClientSession, payload: Dict) -> Dict[str, Any]:
        """Synchronous completion"""
        
        async with session.post(f"{self.base_url}/chat/completions", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                
                # Extract response content
                choice = result["choices"][0]
                message = choice["message"]
                
                # Handle function calls
                tool_calls = message.get("tool_calls", [])
                
                return {
                    "content": message.get("content", ""),
                    "tool_calls": tool_calls,
                    "finish_reason": choice.get("finish_reason"),
                    "usage": TogetherUsage(
                        prompt_tokens=result["usage"]["prompt_tokens"],
                        completion_tokens=result["usage"]["completion_tokens"],
                        total_tokens=result["usage"]["total_tokens"]
                    ).__dict__,
                    "model": result["model"],
                    "provider": "together"
                }
            else:
                error_text = await response.text()
                raise Exception(f"Together.ai API error {response.status}: {error_text}")
    
    async def _complete_streaming(
        self, 
        session: aiohttp.ClientSession, 
        payload: Dict
    ) -> AsyncIterator[Dict[str, Any]]:
        """Streaming completion"""
        
        async with session.post(f"{self.base_url}/chat/completions", json=payload) as response:
            if response.status == 200:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        
                        if data == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            
                            if "content" in delta:
                                yield {
                                    "type": "content",
                                    "content": delta["content"],
                                    "model": chunk["model"],
                                    "provider": "together"
                                }
                            
                            if "tool_calls" in delta:
                                yield {
                                    "type": "tool_call",
                                    "tool_calls": delta["tool_calls"],
                                    "model": chunk["model"],
                                    "provider": "together"
                                }
                        
                        except json.JSONDecodeError:
                            continue
            else:
                error_text = await response.text()
                raise Exception(f"Together.ai streaming error {response.status}: {error_text}")
    
    async def get_embeddings(
        self,
        texts: List[str],
        model: str = "togethercomputer/m2-bert-80M-32k-retrieval"
    ) -> Dict[str, Any]:
        """
        Get embeddings using Together.ai's embedding models
        
        Args:
            texts: List of texts to embed
            model: Embedding model name
        """
        
        session = await self._get_session()
        
        payload = {
            "model": model,
            "input": texts
        }
        
        try:
            async with session.post(f"{self.base_url}/embeddings", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return {
                        "embeddings": [item["embedding"] for item in result["data"]],
                        "model": result["model"],
                        "usage": result["usage"],
                        "provider": "together"
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Together.ai embeddings error {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"Together.ai embeddings error: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Together.ai"""
        
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    result = await response.json()
                    return result["data"]
                else:
                    error_text = await response.text()
                    raise Exception(f"Together.ai models error {response.status}: {error_text}")
        
        except Exception as e:
            logger.error(f"Together.ai list models error: {e}")
            raise
    
    def _supports_function_calling(self, model: str) -> bool:
        """Check if model supports function calling"""
        # Mixtral and Llama 3 models support function calling
        function_calling_models = [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "meta-llama/Llama-3-70b-chat-hf",
            "meta-llama/Llama-3-8b-chat-hf"
        ]
        return model in function_calling_models
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Together.ai API"""
        
        try:
            # Simple test with Mixtral
            response = await self.complete(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                messages=[{"role": "user", "content": "Hello! Please respond with 'Connection successful'."}],
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                "status": "success",
                "provider": "together",
                "model": response["model"],
                "response": response["content"][:100],
                "usage": response["usage"]
            }
        
        except Exception as e:
            return {
                "status": "error",
                "provider": "together",
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            try:
                asyncio.create_task(self.session.close())
            except:
                pass