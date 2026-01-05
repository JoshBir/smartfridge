"""
Forms package for SmartFridge application.
"""

from app.forms.auth import (
    LoginForm,
    RegistrationForm,
    ChangePasswordForm,
    RequestPasswordResetForm,
    ResetPasswordForm,
)
from app.forms.items import ItemForm, ItemSearchForm, BulkDeleteForm
from app.forms.recipes import (
    RecipeForm,
    RecipeSuggestionForm,
    SaveSuggestionForm,
    RecipeSearchForm,
)
from app.forms.sites import SiteForm, SiteSearchForm
from app.forms.admin import (
    UserEditForm,
    AdminResetPasswordForm,
    CreateUserForm,
    UserSearchForm,
)

__all__ = [
    # Auth forms
    'LoginForm',
    'RegistrationForm',
    'ChangePasswordForm',
    'RequestPasswordResetForm',
    'ResetPasswordForm',
    # Item forms
    'ItemForm',
    'ItemSearchForm',
    'BulkDeleteForm',
    # Recipe forms
    'RecipeForm',
    'RecipeSuggestionForm',
    'SaveSuggestionForm',
    'RecipeSearchForm',
    # Site forms
    'SiteForm',
    'SiteSearchForm',
    # Admin forms
    'UserEditForm',
    'AdminResetPasswordForm',
    'CreateUserForm',
    'UserSearchForm',
]
