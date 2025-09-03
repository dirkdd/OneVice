#!/usr/bin/env python3
"""
Anthropic Provider for OneVice
Fallback provider for complex reasoning when data sensitivity allows
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AnthropicUsage:
    """Token usage statistics from Anthropic"""
    input_tokens: int
    output_tokens: int
    total_tokens: int

class AnthropicProvider:
    """
    Anthropic Claude API provider
    Used as fallback for complex reasoning on non-sensitive data
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
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
        Complete a chat conversation using Anthropic Claude
        
        Args:
            model: Claude model name (e.g., "claude-3-5-sonnet-20241022")
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            functions: Function definitions for tool use
            stream: Whether to stream the response
        """
        
        session = await self._get_session()
        
        # Separate system message from conversation
        system_message = ""
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append(msg)
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": conversation_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        if system_message:
            payload["system"] = system_message
        
        # Add tools if provided
        if functions:
            payload["tools"] = [
                {
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                }
                for func in functions
            ]
        
        try:
            if stream:
                return await self._complete_streaming(session, payload)
            else:
                return await self._complete_sync(session, payload)
                
        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            raise
    
    async def _complete_sync(self, session: aiohttp.ClientSession, payload: Dict) -> Dict[str, Any]:
        """Synchronous completion"""
        
        async with session.post(f"{self.base_url}/messages", json=payload) as response:
            if response.status == 200:
                result = await response.json()
                
                # Extract content
                content_blocks = result["content"]
                text_content = ""
                tool_calls = []
                
                for block in content_blocks:
                    if block["type"] == "text":
                        text_content += block["text"]
                    elif block["type"] == "tool_use":
                        tool_calls.append({
                            "id": block["id"],
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block["input"])
                            }
                        })
                
                return {
                    "content": text_content,
                    "tool_calls": tool_calls,
                    "finish_reason": result.get("stop_reason"),
                    "usage": AnthropicUsage(
                        input_tokens=result["usage"]["input_tokens"],
                        output_tokens=result["usage"]["output_tokens"],
                        total_tokens=result["usage"]["input_tokens"] + result["usage"]["output_tokens"]
                    ).__dict__,
                    "model": result["model"],
                    "provider": "anthropic"
                }
            else:
                error_text = await response.text()
                raise Exception(f"Anthropic API error {response.status}: {error_text}")
    
    async def _complete_streaming(
        self, 
        session: aiohttp.ClientSession, 
        payload: Dict
    ) -> AsyncIterator[Dict[str, Any]]:
        """Streaming completion"""
        
        async with session.post(f"{self.base_url}/messages", json=payload) as response:
            if response.status == 200:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        
                        try:
                            chunk = json.loads(data)
                            
                            if chunk["type"] == "content_block_delta":
                                delta = chunk["delta"]
                                if delta["type"] == "text_delta":
                                    yield {
                                        "type": "content",
                                        "content": delta["text"],
                                        "model": payload["model"],
                                        "provider": "anthropic"
                                    }
                            
                            elif chunk["type"] == "content_block_start":
                                content_block = chunk["content_block"]
                                if content_block["type"] == "tool_use":
                                    yield {
                                        "type": "tool_call_start",
                                        "tool_call": {
                                            "id": content_block["id"],
                                            "name": content_block["name"]
                                        },
                                        "model": payload["model"],
                                        "provider": "anthropic"
                                    }
                        
                        except json.JSONDecodeError:
                            continue
            else:
                error_text = await response.text()
                raise Exception(f"Anthropic streaming error {response.status}: {error_text}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Anthropic API"""
        
        try:
            # Simple test with Claude
            response = await self.complete(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": "Hello! Please respond with 'Connection successful'."}],
                max_tokens=50,
                temperature=0.1
            )
            
            return {
                "status": "success",
                "provider": "anthropic",
                "model": response["model"],
                "response": response["content"][:100],
                "usage": response["usage"]
            }
        
        except Exception as e:
            return {
                "status": "error",
                "provider": "anthropic",
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