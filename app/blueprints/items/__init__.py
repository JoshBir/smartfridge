"""
Items blueprint for SmartFridge application.

Handles CRUD operations for fridge items including barcode scanning.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.item import Item, ItemCategory, ExpiryStatus
from app.forms.items import ItemForm, ItemSearchForm
from app.services.barcode import lookup_barcode


items_bp = Blueprint('items', __name__)


@items_bp.route('/')
@login_required
def index():
    """List all items for the current user."""
    form = ItemSearchForm(request.args, meta={'csrf': False})
    
    query = Item.query.filter_by(owner_id=current_user.id)
    
    # Apply search filter
    if form.search.data:
        search_term = f'%{form.search.data}%'
        query = query.filter(Item.name.ilike(search_term))
    
    # Apply category filter
    if form.category.data:
        query = query.filter_by(category=form.category.data)
    
    # Apply status filter
    if form.status.data:
        from datetime import date, timedelta
        today = date.today()
        
        if form.status.data == 'fresh':
            threshold = today + timedelta(days=3)
            query = query.filter(
                (Item.expiry_date > threshold) | (Item.expiry_date.is_(None))
            )
        elif form.status.data == 'expiring':
            threshold = today + timedelta(days=3)
            query = query.filter(
                Item.expiry_date <= threshold,
                Item.expiry_date >= today
            )
        elif form.status.data == 'expired':
            query = query.filter(Item.expiry_date < today)
    
    # Order by expiry date (nulls last)
    items = query.order_by(Item.expiry_date.asc().nullslast()).all()
    
    return render_template('items/index.html', items=items, form=form)


@items_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new item."""
    form = ItemForm()
    
    # Pre-fill from barcode lookup if provided
    barcode = request.args.get('barcode')
    if barcode and request.method == 'GET':
        product = lookup_barcode(barcode)
        if product:
            form.name.data = product.name
            form.category.data = product.category
            form.quantity.data = product.quantity or '1'
            form.barcode.data = product.barcode
            form.brand.data = product.brand
    
    if form.validate_on_submit():
        item = Item.create(
            owner_id=current_user.id,
            name=form.name.data,
            quantity=form.quantity.data,
            category=form.category.data,
            expiry_date=form.expiry_date.data,
            barcode=form.barcode.data or None,
            brand=form.brand.data or None,
            notes=form.notes.data
        )
        
        flash(f'"{item.name}" has been added to your fridge.', 'success')
        return redirect(url_for('items.index'))
    
    return render_template('items/form.html', form=form, title='Add Item')


@items_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing item."""
    item = Item.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    form = ItemForm(obj=item)
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.quantity = form.quantity.data
        item.category = form.category.data
        item.expiry_date = form.expiry_date.data
        item.barcode = form.barcode.data or None
        item.brand = form.brand.data or None
        item.notes = form.notes.data
        
        db.session.commit()
        
        flash(f'"{item.name}" has been updated.', 'success')
        return redirect(url_for('items.index'))
    
    return render_template('items/form.html', form=form, item=item, title='Edit Item')


@items_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete an item."""
    item = Item.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    name = item.name
    db.session.delete(item)
    db.session.commit()
    
    flash(f'"{name}" has been removed from your fridge.', 'success')
    return redirect(url_for('items.index'))


@items_bp.route('/<int:id>')
@login_required
def view(id):
    """View a single item."""
    item = Item.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    return render_template('items/view.html', item=item)


@items_bp.route('/expired')
@login_required
def expired():
    """List all expired items."""
    items = Item.get_expired(current_user.id)
    return render_template('items/expired.html', items=items)


@items_bp.route('/expiring')
@login_required
def expiring():
    """List items expiring soon."""
    items = Item.get_expiring_soon(current_user.id, days=3)
    return render_template('items/expiring.html', items=items)


@items_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple items."""
    item_ids = request.form.getlist('item_ids')
    
    if not item_ids:
        flash('No items selected.', 'warning')
        return redirect(url_for('items.index'))
    
    count = 0
    for item_id in item_ids:
        item = Item.query.filter_by(id=int(item_id), owner_id=current_user.id).first()
        if item:
            db.session.delete(item)
            count += 1
    
    db.session.commit()
    
    flash(f'{count} item(s) have been removed.', 'success')
    return redirect(url_for('items.index'))


# API endpoints for AJAX
@items_bp.route('/api/items', methods=['GET'])
@login_required
def api_list():
    """API: Get all items as JSON."""
    items = Item.get_by_owner(current_user.id)
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'quantity': item.quantity,
        'category': item.category,
        'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
        'expiry_status': item.expiry_status.value,
        'days_until_expiry': item.days_until_expiry,
    } for item in items])


@items_bp.route('/api/items/<int:id>', methods=['DELETE'])
@login_required
def api_delete(id):
    """API: Delete an item."""
    item = Item.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Item deleted'})


# Barcode scanning
@items_bp.route('/scan')
@login_required
def scan():
    """Barcode scanner page."""
    return render_template('items/scan.html')


@items_bp.route('/api/barcode/<barcode>')
@login_required
def api_barcode_lookup(barcode):
    """API: Look up product information by barcode."""
    product = lookup_barcode(barcode)
    
    if product:
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Product not found. You can still add it manually.'
        }), 404


@items_bp.route('/api/barcode', methods=['POST'])
@login_required
def api_add_by_barcode():
    """API: Add item by barcode (with optional manual data)."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    barcode = data.get('barcode')
    name = data.get('name')
    
    if not name:
        # Try to look up the barcode
        if barcode:
            product = lookup_barcode(barcode)
            if product:
                name = product.name
            else:
                return jsonify({'success': False, 'message': 'Product name required'}), 400
        else:
            return jsonify({'success': False, 'message': 'Product name required'}), 400
    
    # Parse expiry date if provided
    expiry_date = None
    if data.get('expiry_date'):
        from datetime import datetime
        try:
            expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    item = Item.create(
        owner_id=current_user.id,
        name=name,
        quantity=data.get('quantity', '1'),
        category=data.get('category', 'other'),
        expiry_date=expiry_date,
        barcode=barcode,
        brand=data.get('brand'),
        notes=data.get('notes')
    )
    
    return jsonify({
        'success': True,
        'message': f'"{item.name}" added to your fridge',
        'item': {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'category': item.category,
        }
    })
