"""
LLM Service Abstraction for OpenAI and Anthropic Claude Integration

This module provides a unified interface for multiple LLM providers, allowing 
seamless switching between OpenAI and Claude while maintaining consistent 
functionality and error handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging
import asyncio
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    CLAUDE = "claude"


class LLMMessage:
    """Standardized message format for LLM interactions"""
    
    def __init__(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_openai_format(self) -> Dict[str, str]:
        """Convert to OpenAI message format"""
        return {
            "role": self.role,
            "content": self.content
        }
    
    def to_claude_format(self) -> Dict[str, str]:
        """Convert to Claude message format"""
        # Claude uses similar format but has some specific requirements
        role_mapping = {
            "system": "system",
            "user": "user", 
            "assistant": "assistant"
        }
        return {
            "role": role_mapping.get(self.role, self.role),
            "content": self.content
        }


class LLMResponse:
    """Standardized response format from LLM providers"""
    
    def __init__(self, 
                 content: str, 
                 provider: LLMProvider,
                 model: str,
                 usage: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.provider = provider
        self.model = model
        self.usage = usage or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.config = kwargs
        self._client = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the LLM provider"""
        pass
    
    @abstractmethod
    async def generate_response(self, 
                              messages: List[LLMMessage],
                              temperature: float = 0.1,
                              max_tokens: Optional[int] = None,
                              **kwargs) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding (if supported)"""
        pass
    
    def is_available(self) -> bool:
        """Check if the provider is available"""
        return bool(self.api_key and self._client)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-ada-002")
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
            
            # Test the connection
            await self._client.models.list()
            logger.info(f"OpenAI provider initialized with model: {self.model}")
            return True
            
        except ImportError:
            logger.error("OpenAI library not installed. Run: pip install openai")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False
    
    async def generate_response(self, 
                              messages: List[LLMMessage],
                              temperature: float = 0.1,
                              max_tokens: Optional[int] = None,
                              **kwargs) -> LLMResponse:
        """Generate response using OpenAI"""
        try:
            if not self._client:
                raise RuntimeError("OpenAI client not initialized")
            
            # Convert messages to OpenAI format
            openai_messages = [msg.to_openai_format() for msg in messages]
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # Add any additional parameters
            request_params.update(kwargs)
            
            # Make the API call
            response = await self._client.chat.completions.create(**request_params)
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Extract usage information
            usage = {}
            if hasattr(response, 'usage'):
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=self.model,
                usage=usage,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            if not self._client:
                raise RuntimeError("OpenAI client not initialized")
            
            response = await self._client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.max_tokens_default = kwargs.get("max_tokens_default", 4000)
    
    async def initialize(self) -> bool:
        """Initialize Claude client"""
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            logger.info(f"Claude provider initialized with model: {self.model}")
            return True
            
        except ImportError:
            logger.error("Anthropic library not installed. Run: pip install anthropic")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Claude provider: {e}")
            return False
    
    async def generate_response(self, 
                              messages: List[LLMMessage],
                              temperature: float = 0.1,
                              max_tokens: Optional[int] = None,
                              **kwargs) -> LLMResponse:
        """Generate response using Claude"""
        try:
            if not self._client:
                raise RuntimeError("Claude client not initialized")
            
            # Claude requires at least max_tokens parameter
            if max_tokens is None:
                max_tokens = self.max_tokens_default
            
            # Separate system messages from conversation messages
            system_messages = [msg for msg in messages if msg.role == "system"]
            conversation_messages = [msg for msg in messages if msg.role != "system"]
            
            # Combine system messages into one
            system_content = "\n\n".join([msg.content for msg in system_messages]) if system_messages else None
            
            # Convert conversation messages to Claude format
            claude_messages = [msg.to_claude_format() for msg in conversation_messages]
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": claude_messages,
            }
            
            if system_content:
                request_params["system"] = system_content
            
            # Add any additional parameters
            request_params.update(kwargs)
            
            # Make the API call
            response = await self._client.messages.create(**request_params)
            
            # Extract response content
            content = ""
            if response.content:
                # Claude returns a list of content blocks
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Extract usage information
            usage = {}
            if hasattr(response, 'usage'):
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.CLAUDE,
                model=self.model,
                usage=usage,
                metadata={"response_id": response.id}
            )
            
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Claude doesn't support embeddings directly - fallback to OpenAI"""
        logger.warning("Claude doesn't support embeddings. Consider using OpenAI for embeddings.")
        raise NotImplementedError("Claude doesn't support embeddings. Use OpenAI provider for embeddings.")


class LLMService:
    """Main LLM service that manages multiple providers"""
    
    def __init__(self, default_provider: LLMProvider = LLMProvider.OPENAI):
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.default_provider = default_provider
        self._initialized = False
    
    async def initialize(self):
        """Initialize all available providers"""
        try:
            # Initialize OpenAI if API key is available
            if settings.OPENAI_API_KEY:
                openai_provider = OpenAIProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model="gpt-3.5-turbo"
                )
                if await openai_provider.initialize():
                    self.providers[LLMProvider.OPENAI] = openai_provider
                    logger.info("OpenAI provider initialized successfully")
            
            # Initialize Claude if API key is available
            if settings.ANTHROPIC_API_KEY:
                claude_provider = ClaudeProvider(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model="claude-3-sonnet-20240229"
                )
                if await claude_provider.initialize():
                    self.providers[LLMProvider.CLAUDE] = claude_provider
                    logger.info("Claude provider initialized successfully")
            
            # Set default provider to first available if current default is not available
            if self.default_provider not in self.providers and self.providers:
                self.default_provider = next(iter(self.providers.keys()))
                logger.info(f"Default provider switched to: {self.default_provider}")
            
            self._initialized = True
            logger.info(f"LLM Service initialized. Available providers: {list(self.providers.keys())}")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            raise
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """Get a specific provider or the default one"""
        if provider is None:
            provider = self.default_provider
        
        if provider not in self.providers:
            available = list(self.providers.keys())
            raise ValueError(f"Provider {provider} not available. Available providers: {available}")
        
        return self.providers[provider]
    
    async def generate_response(self, 
                              query: str,
                              system_prompt: Optional[str] = None,
                              provider: Optional[LLMProvider] = None,
                              temperature: float = 0.1,
                              max_tokens: Optional[int] = None,
                              **kwargs) -> LLMResponse:
        """Generate a response using the specified or default provider"""
        if not self._initialized:
            await self.initialize()
        
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append(LLMMessage("system", system_prompt))
        
        messages.append(LLMMessage("user", query))
        
        # Get provider and generate response
        llm_provider = self.get_provider(provider)
        return await llm_provider.generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def generate_response_with_context(self,
                                           query: str,
                                           context_documents: List[str],
                                           system_prompt: Optional[str] = None,
                                           provider: Optional[LLMProvider] = None,
                                           temperature: float = 0.1,
                                           max_tokens: Optional[int] = None,
                                           **kwargs) -> LLMResponse:
        """Generate a response with document context"""
        if not self._initialized:
            await self.initialize()
        
        # Build context-aware system prompt
        context_text = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(context_documents)])
        
        enhanced_system_prompt = system_prompt or ""
        if context_documents:
            enhanced_system_prompt += f"\n\nHere are some relevant documents for context:\n\n{context_text}"
        
        return await self.generate_response(
            query=query,
            system_prompt=enhanced_system_prompt,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def generate_embedding(self, 
                               text: str, 
                               provider: Optional[LLMProvider] = None) -> List[float]:
        """Generate embedding using available provider"""
        if not self._initialized:
            await self.initialize()
        
        # For embeddings, prefer OpenAI since Claude doesn't support them
        embedding_provider = provider
        if embedding_provider is None or embedding_provider == LLMProvider.CLAUDE:
            if LLMProvider.OPENAI in self.providers:
                embedding_provider = LLMProvider.OPENAI
            else:
                raise ValueError("No embedding-capable provider available")
        
        llm_provider = self.get_provider(embedding_provider)
        return await llm_provider.generate_embedding(text)
    
    def set_default_provider(self, provider: LLMProvider):
        """Set the default provider"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not available")
        
        self.default_provider = provider
        logger.info(f"Default provider set to: {provider}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about available providers"""
        info = {
            "initialized": self._initialized,
            "default_provider": self.default_provider,
            "available_providers": [],
            "provider_details": {}
        }
        
        for provider_type, provider in self.providers.items():
            info["available_providers"].append(provider_type)
            info["provider_details"][provider_type] = {
                "model": provider.model,
                "available": provider.is_available()
            }
        
        return info


# Global LLM service instance
llm_service = LLMService()