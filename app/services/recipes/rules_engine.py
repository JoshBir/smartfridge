"""
Rules-based recipe matching engine for SmartFridge.

Provides deterministic recipe suggestions based on available ingredients
using a local recipe database.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from app.models.item import Item
from app.models.recipe import RecipeDraft


@dataclass
class CanonicalRecipe:
    """A recipe from the canonical recipe database."""
    id: str
    title: str
    ingredients: List[Dict[str, str]]  # [{name, quantity, optional}]
    instructions: List[str]
    servings: int
    prep_time_minutes: int
    cook_time_minutes: int
    tags: List[str]


class RulesEngine:
    """
    Rule-based recipe suggestion engine.
    
    Matches available fridge items against a canonical recipe database
    and scores recipes by ingredient availability and freshness.
    """
    
    def __init__(self, recipes_path: Optional[str] = None):
        """
        Initialise the rules engine.
        
        Args:
            recipes_path: Path to canonical recipes JSON file.
                         Defaults to data/canonical_recipes.json.
        """
        if recipes_path is None:
            recipes_path = os.path.join(
                Path(__file__).parent.parent.parent.parent,
                'data',
                'canonical_recipes.json'
            )
        
        self.recipes_path = recipes_path
        self._recipes: List[CanonicalRecipe] = []
        self._load_recipes()
    
    def _load_recipes(self) -> None:
        """Load recipes from JSON file."""
        try:
            with open(self.recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._recipes = [
                    CanonicalRecipe(
                        id=r.get('id', ''),
                        title=r.get('title', ''),
                        ingredients=r.get('ingredients', []),
                        instructions=r.get('instructions', []),
                        servings=r.get('servings', 4),
                        prep_time_minutes=r.get('prep_time_minutes', 15),
                        cook_time_minutes=r.get('cook_time_minutes', 30),
                        tags=r.get('tags', []),
                    )
                    for r in data.get('recipes', [])
                ]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Log warning but don't fail - empty recipes list
            self._recipes = []
    
    def _normalise_ingredient(self, name: str) -> str:
        """
        Normalise ingredient name for matching.
        
        Args:
            name: Ingredient name.
        
        Returns:
            Normalised lowercase name.
        """
        # Remove common suffixes and normalise
        name = name.lower().strip()
        
        # Remove quantity words
        remove_words = ['fresh', 'frozen', 'canned', 'diced', 'sliced', 
                       'chopped', 'minced', 'large', 'small', 'medium']
        for word in remove_words:
            name = name.replace(word, '').strip()
        
        return name
    
    def _get_available_ingredients(self, items: List[Item]) -> Set[str]:
        """
        Get normalised set of available ingredient names.
        
        Args:
            items: List of fridge items.
        
        Returns:
            Set of normalised ingredient names.
        """
        return {self._normalise_ingredient(item.name) for item in items}
    
    def _calculate_match_score(
        self,
        recipe: CanonicalRecipe,
        available: Set[str],
        items: List[Item]
    ) -> tuple[float, List[str]]:
        """
        Calculate match score for a recipe.
        
        Score factors:
        - Percentage of required ingredients available
        - Freshness of available ingredients (bonus for fresh items)
        - Penalty for missing non-optional ingredients
        
        Args:
            recipe: Recipe to score.
            available: Set of available ingredient names.
            items: Original items list for freshness check.
        
        Returns:
            Tuple of (score 0-100, list of missing ingredients).
        """
        required_ingredients = []
        optional_ingredients = []
        
        for ing in recipe.ingredients:
            name = self._normalise_ingredient(ing.get('name', ''))
            if ing.get('optional', False):
                optional_ingredients.append(name)
            else:
                required_ingredients.append(name)
        
        # Check which ingredients are available
        missing = []
        matched_required = 0
        matched_optional = 0
        
        for ing in required_ingredients:
            if any(ing in avail or avail in ing for avail in available):
                matched_required += 1
            else:
                missing.append(ing)
        
        for ing in optional_ingredients:
            if any(ing in avail or avail in ing for avail in available):
                matched_optional += 1
        
        # Calculate base score (0-100)
        if not required_ingredients:
            base_score = 100.0
        else:
            base_score = (matched_required / len(required_ingredients)) * 80
        
        # Bonus for optional ingredients (up to 10 points)
        if optional_ingredients:
            optional_bonus = (matched_optional / len(optional_ingredients)) * 10
            base_score += optional_bonus
        
        # Freshness bonus (up to 10 points)
        freshness_bonus = 0.0
        items_dict = {self._normalise_ingredient(i.name): i for i in items}
        
        for ing in required_ingredients:
            for avail_name, item in items_dict.items():
                if ing in avail_name or avail_name in ing:
                    days = item.days_until_expiry
                    if days is not None:
                        if days > 7:
                            freshness_bonus += 2.0
                        elif days > 3:
                            freshness_bonus += 1.0
                        elif days > 0:
                            freshness_bonus += 0.5
                    break
        
        # Cap freshness bonus
        freshness_bonus = min(freshness_bonus, 10.0)
        
        return (min(base_score + freshness_bonus, 100.0), missing)
    
    def suggest_recipes(
        self,
        items: List[Item],
        min_score: float = 50.0,
        max_results: int = 5
    ) -> List[RecipeDraft]:
        """
        Suggest recipes based on available ingredients.
        
        Args:
            items: List of available fridge items.
            min_score: Minimum match score (0-100) to include.
            max_results: Maximum number of suggestions.
        
        Returns:
            List of RecipeDraft suggestions, sorted by score.
        """
        if not items:
            return []
        
        available = self._get_available_ingredients(items)
        scored_recipes: List[tuple[float, CanonicalRecipe, List[str]]] = []
        
        for recipe in self._recipes:
            score, missing = self._calculate_match_score(recipe, available, items)
            if score >= min_score:
                scored_recipes.append((score, recipe, missing))
        
        # Sort by score descending
        scored_recipes.sort(key=lambda x: x[0], reverse=True)
        
        # Convert to RecipeDraft objects
        results: List[RecipeDraft] = []
        for score, recipe, missing in scored_recipes[:max_results]:
            ingredients_text = '\n'.join(
                f"• {ing.get('quantity', '')} {ing.get('name', '')}".strip()
                for ing in recipe.ingredients
            )
            instructions_text = '\n'.join(
                f"{i+1}. {step}" for i, step in enumerate(recipe.instructions)
            )
            
            results.append(RecipeDraft(
                title=recipe.title,
                ingredients_text=ingredients_text,
                instructions=instructions_text,
                servings=recipe.servings,
                prep_time_minutes=recipe.prep_time_minutes,
                cook_time_minutes=recipe.cook_time_minutes,
                match_score=round(score, 1),
                missing_ingredients=missing,
            ))
        
        return results
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[CanonicalRecipe]:
        """
        Get a specific recipe by ID.
        
        Args:
            recipe_id: Recipe identifier.
        
        Returns:
            CanonicalRecipe or None if not found.
        """
        for recipe in self._recipes:
            if recipe.id == recipe_id:
                return recipe
        return None
    
    def search_recipes(self, query: str) -> List[CanonicalRecipe]:
        """
        Search recipes by title or tag.
        
        Args:
            query: Search term.
        
        Returns:
            List of matching recipes.
        """
        query_lower = query.lower()
        results = []
        
        for recipe in self._recipes:
            if (query_lower in recipe.title.lower() or
                any(query_lower in tag.lower() for tag in recipe.tags)):
                results.append(recipe)
        
        return results


# Singleton instance
_rules_engine: Optional[RulesEngine] = None


def get_rules_engine() -> RulesEngine:
    """Get or create the rules engine singleton."""
    global _rules_engine
    if _rules_engine is None:
        _rules_engine = RulesEngine()
    return _rules_engine
