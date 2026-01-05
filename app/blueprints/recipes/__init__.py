"""
Recipes blueprint for SmartFridge application.

Handles recipe suggestions, viewing, and CRUD operations.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.item import Item
from app.models.recipe import Recipe, RecipeDraft
from app.forms.recipes import RecipeForm, RecipeSearchForm, SaveSuggestionForm
from app.services.recipes import get_ai_adapter, get_rules_engine


recipes_bp = Blueprint('recipes', __name__)


@recipes_bp.route('/')
@login_required
def index():
    """List all saved recipes."""
    form = RecipeSearchForm(request.args, meta={'csrf': False})
    
    query = Recipe.query.filter_by(owner_id=current_user.id)
    
    if form.search.data:
        search_term = f'%{form.search.data}%'
        query = query.filter(
            (Recipe.title.ilike(search_term)) |
            (Recipe.ingredients_text.ilike(search_term))
        )
    
    recipes = query.order_by(Recipe.created_at.desc()).all()
    
    return render_template('recipes/index.html', recipes=recipes, form=form)


@recipes_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new recipe manually."""
    form = RecipeForm()
    
    if form.validate_on_submit():
        recipe = Recipe.create(
            owner_id=current_user.id,
            title=form.title.data,
            ingredients_text=form.ingredients_text.data,
            instructions=form.instructions.data,
            source_url=form.source_url.data or None,
            servings=form.servings.data,
            prep_time_minutes=form.prep_time_minutes.data,
            cook_time_minutes=form.cook_time_minutes.data,
        )
        
        flash(f'Recipe "{recipe.title}" has been saved.', 'success')
        return redirect(url_for('recipes.view', id=recipe.id))
    
    return render_template('recipes/form.html', form=form, title='Add Recipe')


@recipes_bp.route('/<int:id>')
@login_required
def view(id):
    """View a single recipe."""
    recipe = Recipe.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    return render_template('recipes/view.html', recipe=recipe)


@recipes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing recipe."""
    recipe = Recipe.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    form = RecipeForm(obj=recipe)
    
    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.ingredients_text = form.ingredients_text.data
        recipe.instructions = form.instructions.data
        recipe.source_url = form.source_url.data or None
        recipe.servings = form.servings.data
        recipe.prep_time_minutes = form.prep_time_minutes.data
        recipe.cook_time_minutes = form.cook_time_minutes.data
        
        db.session.commit()
        
        flash(f'Recipe "{recipe.title}" has been updated.', 'success')
        return redirect(url_for('recipes.view', id=recipe.id))
    
    return render_template('recipes/form.html', form=form, recipe=recipe, title='Edit Recipe')


@recipes_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a recipe."""
    recipe = Recipe.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    title = recipe.title
    db.session.delete(recipe)
    db.session.commit()
    
    flash(f'Recipe "{title}" has been deleted.', 'success')
    return redirect(url_for('recipes.index'))


@recipes_bp.route('/<int:id>/cook', methods=['GET', 'POST'])
@login_required
def cook(id):
    """
    Cook a recipe - shows matched ingredients and removes them from fridge.
    """
    recipe = Recipe.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    # Get user's fridge items
    user_items = Item.get_by_owner(current_user.id, include_expired=False)
    
    # Match recipe ingredients to fridge items
    matched_items = []
    recipe_ingredients = recipe.ingredients_list
    
    for item in user_items:
        item_name_lower = item.name.lower()
        for ingredient in recipe_ingredients:
            ingredient_lower = ingredient.lower()
            # Check if item name appears in ingredient line
            if item_name_lower in ingredient_lower or any(
                word in ingredient_lower 
                for word in item_name_lower.split()
                if len(word) > 2
            ):
                matched_items.append({
                    'item': item,
                    'ingredient_line': ingredient,
                    'selected': True
                })
                break
    
    if request.method == 'POST':
        # Get selected item IDs to remove
        items_to_remove = request.form.getlist('remove_items')
        
        removed_count = 0
        for item_id in items_to_remove:
            item = Item.query.filter_by(id=int(item_id), owner_id=current_user.id).first()
            if item:
                db.session.delete(item)
                removed_count += 1
        
        db.session.commit()
        
        if removed_count > 0:
            flash(f'Enjoy your {recipe.title}! {removed_count} ingredient(s) removed from your fridge.', 'success')
        else:
            flash(f'Enjoy your {recipe.title}!', 'success')
        
        return redirect(url_for('recipes.view', id=recipe.id))
    
    return render_template(
        'recipes/cook.html',
        recipe=recipe,
        matched_items=matched_items,
        total_items=len(user_items)
    )


@recipes_bp.route('/suggest', methods=['GET', 'POST'])
@login_required
def suggest():
    """Get recipe suggestions based on available items."""
    items = Item.get_by_owner(current_user.id, include_expired=False)
    suggestions = []
    
    if request.method == 'POST' or request.args.get('generate'):
        if not items:
            flash('Add some items to your fridge first to get suggestions!', 'warning')
        else:
            # Get suggestions from AI adapter
            adapter = get_ai_adapter()
            suggestions = adapter.generate_recipes(items, max_results=5)
            
            if not suggestions:
                flash('No recipe suggestions found. Try adding more ingredients!', 'info')
    
    # Create save forms for each suggestion
    save_forms = []
    for i, suggestion in enumerate(suggestions):
        form = SaveSuggestionForm(prefix=f'suggestion_{i}')
        form.title.data = suggestion.title
        form.ingredients_text.data = suggestion.ingredients_text
        form.instructions.data = suggestion.instructions
        form.servings.data = suggestion.servings
        form.prep_time_minutes.data = suggestion.prep_time_minutes
        form.cook_time_minutes.data = suggestion.cook_time_minutes
        save_forms.append((suggestion, form))
    
    return render_template(
        'recipes/suggest.html',
        items=items,
        suggestions=save_forms,
    )


@recipes_bp.route('/save-suggestion', methods=['POST'])
@login_required
def save_suggestion():
    """Save a recipe suggestion to the user's recipes."""
    title = request.form.get('title')
    ingredients_text = request.form.get('ingredients_text')
    instructions = request.form.get('instructions')
    servings = request.form.get('servings')
    prep_time = request.form.get('prep_time_minutes')
    cook_time = request.form.get('cook_time_minutes')
    
    if not title or not ingredients_text:
        flash('Invalid recipe data.', 'danger')
        return redirect(url_for('recipes.suggest'))
    
    recipe = Recipe.create(
        owner_id=current_user.id,
        title=title,
        ingredients_text=ingredients_text,
        instructions=instructions or '',
        is_ai_generated=True,
        servings=int(servings) if servings else None,
        prep_time_minutes=int(prep_time) if prep_time else None,
        cook_time_minutes=int(cook_time) if cook_time else None,
    )
    
    flash(f'Recipe "{recipe.title}" has been saved!', 'success')
    return redirect(url_for('recipes.view', id=recipe.id))


# API endpoints
@recipes_bp.route('/api/suggest', methods=['POST'])
@login_required
def api_suggest():
    """API: Get recipe suggestions as JSON."""
    items = Item.get_by_owner(current_user.id, include_expired=False)
    
    if not items:
        return jsonify({'suggestions': [], 'message': 'No items in fridge'})
    
    adapter = get_ai_adapter()
    suggestions = adapter.generate_recipes(items, max_results=5)
    
    return jsonify({
        'suggestions': [s.to_dict() for s in suggestions]
    })
