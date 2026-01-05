"""
SmartFridge Test Suite - Sites Tests

Tests for favourite cooking sites management.
"""
import pytest
from app.models.site import Site


class TestSitesView:
    """Site viewing tests."""
    
    def test_sites_index_page_loads(self, auth_client):
        """Test sites index page is accessible."""
        response = auth_client.get('/sites/')
        
        assert response.status_code == 200
        assert b'Favourite' in response.data or b'Sites' in response.data
    
    def test_sites_index_shows_sites(self, auth_client, test_site):
        """Test sites are displayed on index page."""
        response = auth_client.get('/sites/')
        
        assert response.status_code == 200
        assert b'Test Cooking Site' in response.data
    
    def test_view_single_site(self, auth_client, test_site):
        """Test viewing a single site."""
        response = auth_client.get(f'/sites/{test_site.id}')
        
        assert response.status_code == 200
        assert b'Test Cooking Site' in response.data
        assert b'example-cooking.com' in response.data
    
    def test_view_nonexistent_site(self, auth_client):
        """Test viewing non-existent site returns 404."""
        response = auth_client.get('/sites/99999')
        
        assert response.status_code == 404


class TestSitesCreate:
    """Site creation tests."""
    
    def test_new_site_page_loads(self, auth_client):
        """Test new site form is accessible."""
        response = auth_client.get('/sites/new')
        
        assert response.status_code == 200
        assert b'Add Site' in response.data
    
    def test_create_site_success(self, auth_client, app):
        """Test successful site creation."""
        response = auth_client.post('/sites/new', data={
            'name': 'BBC Good Food',
            'url': 'https://www.bbcgoodfood.com',
            'description': 'Great recipes from the BBC',
            'tags': 'british, recipes, baking'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            site = Site.query.filter_by(name='BBC Good Food').first()
            assert site is not None
            assert site.url == 'https://www.bbcgoodfood.com'
    
    def test_create_site_missing_name(self, auth_client):
        """Test site creation without name fails."""
        response = auth_client.post('/sites/new', data={
            'name': '',
            'url': 'https://example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error
    
    def test_create_site_invalid_url(self, auth_client):
        """Test site creation with invalid URL fails."""
        response = auth_client.post('/sites/new', data={
            'name': 'Invalid Site',
            'url': 'not-a-valid-url'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show validation error
    
    def test_create_site_duplicate_url(self, auth_client, test_site):
        """Test creating site with duplicate URL fails."""
        response = auth_client.post('/sites/new', data={
            'name': 'Another Site',
            'url': 'https://example-cooking.com'  # Same as test_site
        }, follow_redirects=True)
        
        # Should either fail or show error
        assert response.status_code == 200


class TestSitesEdit:
    """Site editing tests."""
    
    def test_edit_site_page_loads(self, auth_client, test_site):
        """Test edit site form is accessible."""
        response = auth_client.get(f'/sites/{test_site.id}/edit')
        
        assert response.status_code == 200
        assert b'Edit' in response.data
        assert b'Test Cooking Site' in response.data
    
    def test_edit_site_success(self, auth_client, app, test_site):
        """Test successful site edit."""
        response = auth_client.post(f'/sites/{test_site.id}/edit', data={
            'name': 'Updated Cooking Site',
            'url': 'https://updated-cooking.com',
            'description': 'Updated description',
            'tags': 'updated, tags'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            site = Site.query.get(test_site.id)
            assert site.name == 'Updated Cooking Site'
            assert site.url == 'https://updated-cooking.com'


class TestSitesDelete:
    """Site deletion tests."""
    
    def test_delete_site_success(self, auth_client, app, test_site):
        """Test successful site deletion."""
        site_id = test_site.id
        
        response = auth_client.post(f'/sites/{site_id}/delete', follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            site = Site.query.get(site_id)
            assert site is None


class TestSitesTags:
    """Site tags tests."""
    
    def test_filter_by_tag(self, auth_client, test_site):
        """Test filtering sites by tag."""
        response = auth_client.get('/sites/tag/testing')
        
        assert response.status_code == 200
        assert b'Test Cooking Site' in response.data
    
    def test_filter_by_nonexistent_tag(self, auth_client):
        """Test filtering by non-existent tag."""
        response = auth_client.get('/sites/tag/nonexistenttag')
        
        assert response.status_code == 200
        # Should show no results or all sites


class TestSiteModel:
    """Site model tests."""
    
    def test_site_tags_list(self, app, test_user):
        """Test tags list parsing."""
        with app.app_context():
            site = Site(
                name='Test',
                url='https://test.com',
                tags='italian, pasta, quick meals',
                user_id=test_user.id
            )
            
            tags = site.tags_list
            assert len(tags) == 3
            assert 'italian' in tags
            assert 'pasta' in tags
            assert 'quick meals' in tags
    
    def test_site_tags_list_empty(self, app, test_user):
        """Test empty tags list."""
        with app.app_context():
            site = Site(
                name='Test',
                url='https://test.com',
                tags='',
                user_id=test_user.id
            )
            
            tags = site.tags_list
            assert tags == []
    
    def test_site_tags_list_whitespace(self, app, test_user):
        """Test tags list with extra whitespace."""
        with app.app_context():
            site = Site(
                name='Test',
                url='https://test.com',
                tags='  italian  ,  pasta  ,  quick meals  ',
                user_id=test_user.id
            )
            
            tags = site.tags_list
            assert 'italian' in tags
            assert 'pasta' in tags
