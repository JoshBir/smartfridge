"""
AI adapter interface for recipe generation.

Provides a pluggable interface for AI-powered recipe suggestions,
with support for local rules engine, OpenAI, and Azure OpenAI.
"""

import re
import html
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

from flask import current_app

from app.models.item import Item
from app.models.recipe import RecipeDraft
from app.services.recipes.rules_engine import get_rules_engine


class AIAdapter(Protocol):
    """Protocol for AI adapter implementations."""
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """Generate recipe suggestions from available items."""
        ...


class LocalAdapter:
    """
    Local rules-based adapter (no AI).
    
    Uses the rules engine for deterministic recipe matching.
    """
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """
        Generate recipes using local rules engine.
        
        Args:
            items: Available fridge items.
            max_results: Maximum suggestions to return.
        
        Returns:
            List of RecipeDraft suggestions.
        """
        engine = get_rules_engine()
        return engine.suggest_recipes(items, max_results=max_results)


class OpenAIAdapter:
    """
    OpenAI API adapter for recipe generation.
    
    Uses GPT models to generate creative recipe suggestions.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise OpenAI adapter.
        
        Args:
            api_key: OpenAI API key.
            model: Model to use (default: gpt-3.5-turbo).
        """
        self.api_key = api_key or current_app.config.get('AI_API_KEY')
        self.model = model or current_app.config.get('AI_MODEL', 'gpt-3.5-turbo')
    
    def _sanitise_output(self, text: str) -> str:
        """
        Sanitise AI output to prevent XSS.
        
        Args:
            text: Raw AI output.
        
        Returns:
            Sanitised text.
        """
        # HTML escape
        text = html.escape(text)
        
        # Remove any script-like patterns
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Limit length
        if len(text) > 5000:
            text = text[:5000] + '...'
        
        return text
    
    def _build_prompt(self, items: List[Item]) -> str:
        """Build prompt for recipe generation."""
        ingredients = ', '.join(item.name for item in items[:20])  # Limit items
        
        return f"""You are a helpful cooking assistant. Based on the following ingredients available in the user's fridge, suggest a recipe they could make.

Available ingredients: {ingredients}

Please provide:
1. Recipe title
2. List of ingredients (including amounts)
3. Step-by-step cooking instructions
4. Approximate prep and cook times

Format your response as:
TITLE: [recipe name]
SERVINGS: [number]
PREP_TIME: [minutes]
COOK_TIME: [minutes]
INGREDIENTS:
- [ingredient 1]
- [ingredient 2]
...
INSTRUCTIONS:
1. [step 1]
2. [step 2]
..."""
    
    def _parse_response(self, response_text: str) -> Optional[RecipeDraft]:
        """Parse AI response into RecipeDraft."""
        try:
            lines = response_text.strip().split('\n')
            
            title = ""
            servings = 4
            prep_time = 15
            cook_time = 30
            ingredients = []
            instructions = []
            
            section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.upper().startswith('TITLE:'):
                    title = line[6:].strip()
                elif line.upper().startswith('SERVINGS:'):
                    try:
                        servings = int(re.search(r'\d+', line).group())
                    except (AttributeError, ValueError):
                        pass
                elif line.upper().startswith('PREP_TIME:'):
                    try:
                        prep_time = int(re.search(r'\d+', line).group())
                    except (AttributeError, ValueError):
                        pass
                elif line.upper().startswith('COOK_TIME:'):
                    try:
                        cook_time = int(re.search(r'\d+', line).group())
                    except (AttributeError, ValueError):
                        pass
                elif line.upper().startswith('INGREDIENTS:'):
                    section = 'ingredients'
                elif line.upper().startswith('INSTRUCTIONS:'):
                    section = 'instructions'
                elif section == 'ingredients' and (line.startswith('-') or line.startswith('•')):
                    ingredients.append(line[1:].strip())
                elif section == 'instructions' and re.match(r'^\d+\.', line):
                    instructions.append(re.sub(r'^\d+\.\s*', '', line))
            
            if title and ingredients:
                return RecipeDraft(
                    title=self._sanitise_output(title),
                    ingredients_text='\n'.join(f'• {self._sanitise_output(i)}' for i in ingredients),
                    instructions='\n'.join(f'{i+1}. {self._sanitise_output(s)}' for i, s in enumerate(instructions)),
                    servings=servings,
                    prep_time_minutes=prep_time,
                    cook_time_minutes=cook_time,
                    match_score=85.0,  # AI suggestions get good score
                )
            
            return None
            
        except Exception:
            return None
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """
        Generate recipes using OpenAI API.
        
        Falls back to local rules engine if API fails.
        """
        if not self.api_key:
            # Fall back to local
            return LocalAdapter().generate_recipes(items, max_results)
        
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            results: List[RecipeDraft] = []
            
            for _ in range(min(max_results, 3)):
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant."},
                        {"role": "user", "content": self._build_prompt(items)}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                if response.choices:
                    content = response.choices[0].message.content
                    draft = self._parse_response(content)
                    if draft:
                        results.append(draft)
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"OpenAI API error: {e}")
            # Fall back to local rules engine
            return LocalAdapter().generate_recipes(items, max_results)


class AzureOpenAIAdapter(OpenAIAdapter):
    """
    Azure OpenAI adapter.
    
    Uses Azure-hosted OpenAI models.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None
    ):
        """
        Initialise Azure OpenAI adapter.
        
        Args:
            api_key: Azure OpenAI API key.
            endpoint: Azure OpenAI endpoint URL.
            deployment: Deployment name.
        """
        super().__init__(api_key)
        self.endpoint = endpoint or current_app.config.get('AI_AZURE_ENDPOINT')
        self.deployment = deployment or current_app.config.get('AI_MODEL', 'gpt-35-turbo')
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """Generate recipes using Azure OpenAI."""
        if not self.api_key or not self.endpoint:
            return LocalAdapter().generate_recipes(items, max_results)
        
        try:
            from openai import AzureOpenAI
            
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-02-01",
                azure_endpoint=self.endpoint
            )
            
            results: List[RecipeDraft] = []
            
            for _ in range(min(max_results, 3)):
                response = client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant."},
                        {"role": "user", "content": self._build_prompt(items)}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                if response.choices:
                    content = response.choices[0].message.content
                    draft = self._parse_response(content)
                    if draft:
                        results.append(draft)
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Azure OpenAI API error: {e}")
            return LocalAdapter().generate_recipes(items, max_results)


class MockAdapter:
    """
    Mock adapter for testing.
    
    Returns deterministic results without API calls.
    """
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """Generate mock recipe suggestions."""
        if not items:
            return []
        
        item_names = ', '.join(item.name for item in items[:5])
        
        return [
            RecipeDraft(
                title=f"Quick {items[0].name.title()} Stir-Fry",
                ingredients_text=f"• {item_names}\n• 2 tbsp oil\n• Salt and pepper to taste",
                instructions="1. Heat oil in a pan.\n2. Add ingredients and stir-fry for 5-7 minutes.\n3. Season and serve.",
                servings=2,
                prep_time_minutes=10,
                cook_time_minutes=10,
                match_score=90.0,
            ),
            RecipeDraft(
                title=f"Simple {items[0].name.title()} Bake",
                ingredients_text=f"• {item_names}\n• 100g cheese\n• Herbs to taste",
                instructions="1. Preheat oven to 180°C.\n2. Layer ingredients in a baking dish.\n3. Top with cheese and bake for 25 minutes.",
                servings=4,
                prep_time_minutes=15,
                cook_time_minutes=25,
                match_score=85.0,
            ),
        ][:max_results]


class GeminiAdapter(OpenAIAdapter):
    """
    Google Gemini API adapter for recipe generation.
    
    Uses the new google-genai package (generous free tier: 15 RPM, 1M tokens/day).
    Get your free API key at: https://aistudio.google.com/app/apikey
    
    Install: pip install google-genai
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise Gemini adapter.
        
        Args:
            api_key: Google AI API key.
            model: Model to use (default: gemini-2.0-flash).
        """
        self.api_key = api_key or current_app.config.get('AI_API_KEY')
        self.model = model or current_app.config.get('AI_MODEL', 'gemini-2.0-flash')
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """
        Generate recipes using Google Gemini API.
        
        Falls back to local rules engine if API fails.
        """
        if not self.api_key:
            return LocalAdapter().generate_recipes(items, max_results)
        
        try:
            from google import genai
            
            client = genai.Client(api_key=self.api_key)
            
            results: List[RecipeDraft] = []
            
            for _ in range(min(max_results, 3)):
                response = client.models.generate_content(
                    model=self.model,
                    contents=self._build_prompt(items),
                )
                
                if response.text:
                    draft = self._parse_response(response.text)
                    if draft:
                        results.append(draft)
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Gemini API error: {e}")
            return LocalAdapter().generate_recipes(items, max_results)


class GroqAdapter(OpenAIAdapter):
    """
    Groq API adapter for recipe generation.
    
    Uses Groq's fast inference (free tier: 30 RPM, 14,400 req/day).
    Get your free API key at: https://console.groq.com/keys
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise Groq adapter.
        
        Args:
            api_key: Groq API key.
            model: Model to use (default: llama-3.1-8b-instant).
        """
        self.api_key = api_key or current_app.config.get('AI_API_KEY')
        self.model = model or current_app.config.get('AI_MODEL', 'llama-3.1-8b-instant')
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """
        Generate recipes using Groq API.
        
        Falls back to local rules engine if API fails.
        """
        if not self.api_key:
            return LocalAdapter().generate_recipes(items, max_results)
        
        try:
            from groq import Groq
            
            client = Groq(api_key=self.api_key)
            
            results: List[RecipeDraft] = []
            
            for _ in range(min(max_results, 3)):
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant."},
                        {"role": "user", "content": self._build_prompt(items)}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                if response.choices:
                    content = response.choices[0].message.content
                    draft = self._parse_response(content)
                    if draft:
                        results.append(draft)
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Groq API error: {e}")
            return LocalAdapter().generate_recipes(items, max_results)


class OpenRouterAdapter(OpenAIAdapter):
    """
    OpenRouter API adapter for recipe generation.
    
    OpenRouter provides access to many models via OpenAI-compatible API.
    Free models available! Get your API key at: https://openrouter.ai/keys
    
    Free models include:
    - meta-llama/llama-3.2-3b-instruct:free
    - google/gemma-2-9b-it:free
    - mistralai/mistral-7b-instruct:free
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise OpenRouter adapter.
        
        Args:
            api_key: OpenRouter API key.
            model: Model to use (default: meta-llama/llama-3.2-3b-instruct:free).
        """
        self.api_key = api_key or current_app.config.get('AI_API_KEY')
        self.model = model or current_app.config.get('AI_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')
    
    def generate_recipes(
        self,
        items: List[Item],
        max_results: int = 3
    ) -> List[RecipeDraft]:
        """
        Generate recipes using OpenRouter API.
        
        Falls back to local rules engine if API fails.
        """
        if not self.api_key:
            return LocalAdapter().generate_recipes(items, max_results)
        
        try:
            import openai
            
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
            
            results: List[RecipeDraft] = []
            
            for _ in range(min(max_results, 3)):
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant."},
                        {"role": "user", "content": self._build_prompt(items)}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                if response.choices:
                    content = response.choices[0].message.content
                    draft = self._parse_response(content)
                    if draft:
                        results.append(draft)
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"OpenRouter API error: {e}")
            return LocalAdapter().generate_recipes(items, max_results)


def get_ai_adapter() -> AIAdapter:
    """
    Get the configured AI adapter.
    
    Returns appropriate adapter based on AI_PROVIDER config.
    """
    provider = current_app.config.get('AI_PROVIDER', 'local')
    
    if provider == 'openai':
        return OpenAIAdapter()
    elif provider == 'azure':
        return AzureOpenAIAdapter()
    elif provider == 'gemini':
        return GeminiAdapter()
    elif provider == 'groq':
        return GroqAdapter()
    elif provider == 'openrouter':
        return OpenRouterAdapter()
    elif provider == 'mock':
        return MockAdapter()
    else:
        return LocalAdapter()

