"""
Sites blueprint for SmartFridge application.

Handles CRUD operations for favourite cooking websites.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.site import Site
from app.forms.sites import SiteForm, SiteSearchForm


sites_bp = Blueprint('sites', __name__)


@sites_bp.route('/')
@login_required
def index():
    """List all favourite sites."""
    form = SiteSearchForm(request.args, meta={'csrf': False})
    
    query = Site.query.filter_by(owner_id=current_user.id)
    
    if form.search.data:
        search_term = f'%{form.search.data}%'
        query = query.filter(
            (Site.title.ilike(search_term)) |
            (Site.url.ilike(search_term)) |
            (Site.tags.ilike(search_term))
        )
    
    if form.tag.data:
        tag_term = f'%{form.tag.data}%'
        query = query.filter(Site.tags.ilike(tag_term))
    
    sites = query.order_by(Site.title.asc()).all()
    
    # Get all unique tags for filter dropdown
    all_tags = Site.get_all_tags(current_user.id)
    
    return render_template('sites/index.html', sites=sites, form=form, all_tags=all_tags)


@sites_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Add a new favourite site."""
    form = SiteForm(owner_id=current_user.id)
    
    if form.validate_on_submit():
        site = Site.create(
            owner_id=current_user.id,
            title=form.title.data,
            url=form.url.data,
            tags=form.tags.data or None,
            description=form.description.data or None,
        )
        
        flash(f'"{site.title}" has been added to your favourites.', 'success')
        return redirect(url_for('sites.index'))
    
    return render_template('sites/form.html', form=form, title='Add Site')


@sites_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a favourite site."""
    site = Site.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    form = SiteForm(owner_id=current_user.id, site_id=site.id, obj=site)
    
    if form.validate_on_submit():
        site.title = form.title.data
        site.url = form.url.data
        site.tags = form.tags.data or None
        site.description = form.description.data or None
        
        db.session.commit()
        
        flash(f'"{site.title}" has been updated.', 'success')
        return redirect(url_for('sites.index'))
    
    return render_template('sites/form.html', form=form, site=site, title='Edit Site')


@sites_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a favourite site."""
    site = Site.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    
    title = site.title
    db.session.delete(site)
    db.session.commit()
    
    flash(f'"{title}" has been removed from your favourites.', 'success')
    return redirect(url_for('sites.index'))


@sites_bp.route('/<int:id>')
@login_required
def view(id):
    """View site details."""
    site = Site.query.filter_by(id=id, owner_id=current_user.id).first_or_404()
    return render_template('sites/view.html', site=site)


@sites_bp.route('/tag/<tag>')
@login_required
def by_tag(tag):
    """List sites with a specific tag."""
    sites = Site.get_by_tag(current_user.id, tag)
    return render_template('sites/by_tag.html', sites=sites, tag=tag)
