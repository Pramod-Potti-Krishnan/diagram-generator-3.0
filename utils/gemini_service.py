"""
Optimized Gemini Service for Efficient API Usage

Centralizes Gemini model management and optimizes API calls.
"""

import asyncio
from typing import Dict, Any, Optional
import google.generativeai as genai
from functools import lru_cache
import time

from utils.logger import setup_logger
from config import configure_gemini, is_gemini_configured

logger = setup_logger(__name__)


class GeminiService:
    """
    Singleton service for optimized Gemini API usage.
    
    Features:
    - Shared model instances
    - Request batching
    - Caching of common patterns
    - Rate limiting
    - Optimized prompts
    """
    
    _instance = None
    _models: Dict[str, Any] = {}
    _last_request_time: Dict[str, float] = {}
    MIN_REQUEST_INTERVAL = 0.1  # Minimum 100ms between requests per model
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._models = {}
        self._last_request_time = {}
        self._prompt_cache = {}
        
    def initialize(self, api_key: str) -> bool:
        """Initialize Gemini with API key"""
        try:
            if configure_gemini(api_key):
                # Pre-load commonly used models
                self._models['flash'] = genai.GenerativeModel('gemini-2.5-flash')
                self._models['flash-lite'] = genai.GenerativeModel('gemini-2.0-flash-lite')
                logger.info("GeminiService initialized with models")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize GeminiService: {e}")
        return False
    
    def get_model(self, model_name: str = 'flash') -> Optional[Any]:
        """Get or create a model instance"""
        if model_name not in self._models:
            try:
                if model_name == 'flash':
                    self._models[model_name] = genai.GenerativeModel('gemini-2.5-flash')
                elif model_name == 'flash-lite':
                    self._models[model_name] = genai.GenerativeModel('gemini-2.0-flash-lite')
                else:
                    logger.warning(f"Unknown model: {model_name}")
                    return None
            except Exception as e:
                logger.error(f"Failed to create model {model_name}: {e}")
                return None
        return self._models.get(model_name)
    
    async def generate_content(
        self,
        prompt: str,
        model_name: str = 'flash',
        cache_key: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate content with optimizations.
        
        Args:
            prompt: The prompt to send
            model_name: Model to use ('flash' or 'flash-lite')
            cache_key: Optional cache key for response caching
            use_cache: Whether to use response caching
            
        Returns:
            Generated text or None on error
        """
        
        # Check cache first
        if use_cache and cache_key and cache_key in self._prompt_cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._prompt_cache[cache_key]
        
        # Get model
        model = self.get_model(model_name)
        if not model:
            return None
        
        # Rate limiting
        await self._rate_limit(model_name)
        
        try:
            # Generate content
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            result = response.text
            
            # Cache if requested
            if use_cache and cache_key:
                self._prompt_cache[cache_key] = result
                # Limit cache size
                if len(self._prompt_cache) > 100:
                    # Remove oldest entries
                    keys = list(self._prompt_cache.keys())[:50]
                    for k in keys:
                        del self._prompt_cache[k]
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return None
    
    async def _rate_limit(self, model_name: str):
        """Apply rate limiting per model"""
        last_time = self._last_request_time.get(model_name, 0)
        current_time = time.time()
        
        time_since_last = current_time - last_time
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            wait_time = self.MIN_REQUEST_INTERVAL - time_since_last
            await asyncio.sleep(wait_time)
        
        self._last_request_time[model_name] = time.time()
    
    def optimize_prompt(self, prompt: str, max_length: int = 2000) -> str:
        """
        Optimize prompt for better performance.
        
        - Removes unnecessary whitespace
        - Truncates overly long content
        - Focuses on essential information
        """
        
        # Remove excessive whitespace
        lines = prompt.split('\n')
        optimized_lines = [line.strip() for line in lines if line.strip()]
        optimized = '\n'.join(optimized_lines)
        
        # Truncate if too long
        if len(optimized) > max_length:
            # Keep the most important parts (beginning and end)
            keep_start = int(max_length * 0.7)
            keep_end = int(max_length * 0.2)
            optimized = optimized[:keep_start] + "\n...[content truncated]...\n" + optimized[-keep_end:]
        
        return optimized
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._prompt_cache.clear()
        logger.info("Prompt cache cleared")


# Global service instance
_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the global Gemini service"""
    global _service
    if _service is None:
        _service = GeminiService()
    return _service


async def optimized_generate(
    prompt: str,
    model_type: str = 'flash',
    cache_key: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function for optimized generation.
    
    Args:
        prompt: The prompt to send
        model_type: 'flash' for complex tasks, 'flash-lite' for simple routing
        cache_key: Optional cache key for response caching
        
    Returns:
        Generated text or None on error
    """
    
    service = get_gemini_service()
    
    # Initialize if needed
    if not is_gemini_configured():
        from config import get_settings
        settings = get_settings()
        if not service.initialize(settings.google_api_key):
            return None
    
    # Optimize prompt
    optimized_prompt = service.optimize_prompt(prompt)
    
    # Generate
    return await service.generate_content(
        optimized_prompt,
        model_name=model_type,
        cache_key=cache_key,
        use_cache=True
    )