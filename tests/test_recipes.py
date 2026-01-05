"""
SmartFridge Test Suite - Recipe Tests

Tests for recipe management and AI suggestions.
"""
import pytest
from app.models.recipe import Recipe, RecipeDraft
from app.services.recipes.rules_engine import RulesEngine


class TestRecipesView:
    """Recipe viewing tests."""
    
    def test_recipes_index_page_loads(self, auth_client):
        """Test recipes index page is accessible."""
        response = auth_client.get('/recipes/')
        
        assert response.status_code == 200
        assert b'My Recipes' in response.data
    
    def test_recipes_index_shows_recipes(self, auth_client, test_recipe):
        """Test recipes are displayed on index page."""
        response = auth_client.get('/recipes/')
        
        assert response.status_code == 200
        assert b'Test Omelette' in response.data
    
    def test_view_single_recipe(self, auth_client, test_recipe):
        """Test viewing a single recipe."""
        response = auth_client.get(f'/recipes/{test_recipe.id}')
        
        assert response.status_code == 200
        assert b'Test Omelette' in response.data
        assert b'eggs' in response.data.lower()
    
    def test_view_nonexistent_recipe(self, auth_client):
        """Test viewing non-existent recipe returns 404."""
        response = auth_client.get('/recipes/99999')
        
        assert response.status_code == 404


class TestRecipesCreate:
    """Recipe creation tests."""
    
    def test_new_recipe_page_loads(self, auth_client):
        """Test new recipe form is accessible."""
        response = auth_client.get('/recipes/new')
        
        assert response.status_code == 200
        assert b'Add Recipe' in response.data
    
    def test_create_recipe_success(self, auth_client, app):
        """Test successful recipe creation."""
        response = auth_client.post('/recipes/new', data={
            'title': 'Simple Toast',
            'ingredients_text': '• 2 slices bread\n• Butter',
            'instructions': '1. Toast bread\n2. Apply butter',
            'servings': 1,
            'prep_time_minutes': 2,
            'cook_time_minutes': 3
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            recipe = Recipe.query.filter_by(title='Simple Toast').first()
            assert recipe is not None
            assert recipe.servings == 1
    
    def test_create_recipe_missing_title(self, auth_client):
        """Test recipe creation without title fails."""
        response = auth_client.post('/recipes/new', data={
            'title': '',
            'ingredients_text': '• Something',
            'instructions': '1. Do something'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error


class TestRecipesEdit:
    """Recipe editing tests."""
    
    def test_edit_recipe_page_loads(self, auth_client, test_recipe):
        """Test edit recipe form is accessible."""
        response = auth_client.get(f'/recipes/{test_recipe.id}/edit')
        
        assert response.status_code == 200
        assert b'Edit Recipe' in response.data
        assert b'Test Omelette' in response.data
    
    def test_edit_recipe_success(self, auth_client, app, test_recipe):
        """Test successful recipe edit."""
        response = auth_client.post(f'/recipes/{test_recipe.id}/edit', data={
            'title': 'Updated Omelette',
            'ingredients_text': '• 4 eggs\n• Cheese',
            'instructions': '1. Beat eggs\n2. Add cheese\n3. Cook',
            'servings': 3
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            recipe = Recipe.query.get(test_recipe.id)
            assert recipe.title == 'Updated Omelette'
            assert recipe.servings == 3


class TestRecipesDelete:
    """Recipe deletion tests."""
    
    def test_delete_recipe_success(self, auth_client, app, test_recipe):
        """Test successful recipe deletion."""
        recipe_id = test_recipe.id
        
        response = auth_client.post(f'/recipes/{recipe_id}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            recipe = Recipe.query.get(recipe_id)
            assert recipe is None


class TestRecipeSuggestions:
    """Recipe suggestion tests."""
    
    def test_suggest_page_loads(self, auth_client):
        """Test suggestion page is accessible."""
        response = auth_client.get('/recipes/suggest')
        
        assert response.status_code == 200
        assert b'Suggestions' in response.data or b'suggest' in response.data.lower()
    
    def test_suggest_with_no_items(self, auth_client):
        """Test suggestion page with no items."""
        response = auth_client.get('/recipes/suggest')
        
        assert response.status_code == 200
        # Should show message about no items


class TestRulesEngine:
    """Rules engine unit tests."""
    
    def test_rules_engine_initialisation(self):
        """Test rules engine can be initialised."""
        engine = RulesEngine()
        assert engine is not None
    
    def test_ingredient_matching_exact(self):
        """Test exact ingredient matching."""
        engine = RulesEngine()
        
        recipe = RecipeDraft(
            title='Test Recipe',
            ingredients_text='• eggs\n• milk',
            instructions='Test instructions'
        )
        
        available = ['eggs', 'milk', 'butter']
        
        matched, missing = engine._match_ingredients(recipe, available)
        
        assert 'eggs' in matched
        assert 'milk' in matched
        assert len(missing) == 0
    
    def test_ingredient_matching_partial(self):
        """Test partial ingredient matching."""
        engine = RulesEngine()
        
        recipe = RecipeDraft(
            title='Test Recipe',
            ingredients_text='• fresh eggs\n• whole milk\n• cheddar cheese',
            instructions='Test instructions'
        )
        
        available = ['eggs', 'milk']
        
        matched, missing = engine._match_ingredients(recipe, available)
        
        assert len(matched) >= 2
        assert len(missing) >= 1
    
    def test_recipe_scoring(self):
        """Test recipe scoring algorithm."""
        engine = RulesEngine()
        
        recipe = RecipeDraft(
            title='Test Recipe',
            ingredients_text='• eggs\n• milk\n• butter',
            instructions='Test instructions'
        )
        
        # All ingredients available
        available_all = ['eggs', 'milk', 'butter']
        score_all = engine._calculate_score(recipe, available_all)
        
        # Only some ingredients
        available_some = ['eggs']
        score_some = engine._calculate_score(recipe, available_some)
        
        assert score_all > score_some
    
    def test_suggest_recipes_returns_sorted(self):
        """Test suggested recipes are sorted by score."""
        engine = RulesEngine()
        
        available = ['eggs', 'milk', 'butter', 'flour', 'sugar']
        suggestions = engine.suggest_recipes(available, limit=5)
        
        # Verify sorted by match score
        for i in range(len(suggestions) - 1):
            assert suggestions[i].match_score >= suggestions[i + 1].match_score


class TestRecipeModel:
    """Recipe model tests."""
    
    def test_recipe_ingredients_list(self, app, test_user):
        """Test ingredients list parsing."""
        with app.app_context():
            recipe = Recipe(
                title='Test',
                ingredients_text='• Eggs\n• Milk\n• Butter',
                instructions='Cook it',
                user_id=test_user.id
            )
            
            ingredients = recipe.ingredients_list
            assert len(ingredients) == 3
            assert 'Eggs' in ingredients
    
    def test_recipe_instructions_list(self, app, test_user):
        """Test instructions list parsing."""
        with app.app_context():
            recipe = Recipe(
                title='Test',
                ingredients_text='• Eggs',
                instructions='1. Beat eggs\n2. Cook\n3. Serve',
                user_id=test_user.id
            )
            
            steps = recipe.instructions_list
            assert len(steps) == 3
    
    def test_recipe_total_time(self, app, test_user):
        """Test total time calculation."""
        with app.app_context():
            recipe = Recipe(
                title='Test',
                ingredients_text='• Eggs',
                instructions='Cook',
                prep_time_minutes=10,
                cook_time_minutes=20,
                user_id=test_user.id
            )
            
            assert recipe.total_time_minutes == 30
