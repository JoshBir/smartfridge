"""
Barcode lookup service for SmartFridge application.

Uses Open Food Facts API (free, no API key required) to look up
product information from barcodes (EAN/UPC).
"""

import re
from dataclasses import dataclass
from typing import Optional
import httpx
from flask import current_app

from app.models.item import ItemCategory


@dataclass
class ProductInfo:
    """Product information from barcode lookup."""
    barcode: str
    name: str
    brand: Optional[str] = None
    category: str = ItemCategory.OTHER.value
    quantity: Optional[str] = None
    image_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        return {
            'barcode': self.barcode,
            'name': self.name,
            'brand': self.brand,
            'category': self.category,
            'quantity': self.quantity,
            'image_url': self.image_url,
        }


# Category mapping from Open Food Facts categories to our categories
CATEGORY_MAPPING = {
    # Dairy
    'dairy': ItemCategory.DAIRY.value,
    'milk': ItemCategory.DAIRY.value,
    'cheese': ItemCategory.DAIRY.value,
    'yogurt': ItemCategory.DAIRY.value,
    'butter': ItemCategory.DAIRY.value,
    'cream': ItemCategory.DAIRY.value,
    'eggs': ItemCategory.DAIRY.value,
    
    # Meat
    'meat': ItemCategory.MEAT.value,
    'beef': ItemCategory.MEAT.value,
    'pork': ItemCategory.MEAT.value,
    'chicken': ItemCategory.MEAT.value,
    'poultry': ItemCategory.MEAT.value,
    'lamb': ItemCategory.MEAT.value,
    'sausage': ItemCategory.MEAT.value,
    'bacon': ItemCategory.MEAT.value,
    'ham': ItemCategory.MEAT.value,
    
    # Fish
    'fish': ItemCategory.FISH.value,
    'seafood': ItemCategory.FISH.value,
    'salmon': ItemCategory.FISH.value,
    'tuna': ItemCategory.FISH.value,
    'shrimp': ItemCategory.FISH.value,
    'prawns': ItemCategory.FISH.value,
    
    # Vegetables
    'vegetable': ItemCategory.VEGETABLES.value,
    'vegetables': ItemCategory.VEGETABLES.value,
    'salad': ItemCategory.VEGETABLES.value,
    'tomato': ItemCategory.VEGETABLES.value,
    'potato': ItemCategory.VEGETABLES.value,
    'carrot': ItemCategory.VEGETABLES.value,
    'onion': ItemCategory.VEGETABLES.value,
    
    # Fruits
    'fruit': ItemCategory.FRUITS.value,
    'fruits': ItemCategory.FRUITS.value,
    'apple': ItemCategory.FRUITS.value,
    'banana': ItemCategory.FRUITS.value,
    'orange': ItemCategory.FRUITS.value,
    'berry': ItemCategory.FRUITS.value,
    'berries': ItemCategory.FRUITS.value,
    
    # Beverages
    'beverage': ItemCategory.BEVERAGES.value,
    'beverages': ItemCategory.BEVERAGES.value,
    'drink': ItemCategory.BEVERAGES.value,
    'drinks': ItemCategory.BEVERAGES.value,
    'juice': ItemCategory.BEVERAGES.value,
    'soda': ItemCategory.BEVERAGES.value,
    'water': ItemCategory.BEVERAGES.value,
    'coffee': ItemCategory.BEVERAGES.value,
    'tea': ItemCategory.BEVERAGES.value,
    'beer': ItemCategory.BEVERAGES.value,
    'wine': ItemCategory.BEVERAGES.value,
    
    # Condiments
    'condiment': ItemCategory.CONDIMENTS.value,
    'sauce': ItemCategory.CONDIMENTS.value,
    'sauces': ItemCategory.CONDIMENTS.value,
    'ketchup': ItemCategory.CONDIMENTS.value,
    'mustard': ItemCategory.CONDIMENTS.value,
    'mayonnaise': ItemCategory.CONDIMENTS.value,
    'dressing': ItemCategory.CONDIMENTS.value,
    'spice': ItemCategory.CONDIMENTS.value,
    'spices': ItemCategory.CONDIMENTS.value,
    'seasoning': ItemCategory.CONDIMENTS.value,
    'oil': ItemCategory.CONDIMENTS.value,
    'vinegar': ItemCategory.CONDIMENTS.value,
    
    # Frozen
    'frozen': ItemCategory.FROZEN.value,
    'ice cream': ItemCategory.FROZEN.value,
    'frozen food': ItemCategory.FROZEN.value,
}


def _detect_category(categories_tags: list, product_name: str) -> str:
    """
    Detect item category from Open Food Facts tags.
    
    Args:
        categories_tags: List of category tags from API.
        product_name: Product name for fallback matching.
    
    Returns:
        ItemCategory value.
    """
    # Check category tags first
    for tag in categories_tags:
        tag_lower = tag.lower().replace('en:', '').replace('-', ' ')
        for keyword, category in CATEGORY_MAPPING.items():
            if keyword in tag_lower:
                return category
    
    # Fallback: check product name
    name_lower = product_name.lower()
    for keyword, category in CATEGORY_MAPPING.items():
        if keyword in name_lower:
            return category
    
    return ItemCategory.OTHER.value


def lookup_barcode(barcode: str) -> Optional[ProductInfo]:
    """
    Look up product information by barcode using Open Food Facts API.
    
    Args:
        barcode: Product barcode (EAN/UPC).
    
    Returns:
        ProductInfo if found, None otherwise.
    """
    # Clean barcode - remove any non-digit characters
    barcode = re.sub(r'\D', '', barcode)
    
    if not barcode or len(barcode) < 8:
        return None
    
    try:
        # Open Food Facts API - free, no key needed
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers={
                'User-Agent': 'SmartFridge/1.0 (https://github.com/smartfridge)'
            })
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if data.get('status') != 1:
            return None
        
        product = data.get('product', {})
        
        # Get product name (try multiple fields)
        name = (
            product.get('product_name_en') or
            product.get('product_name') or
            product.get('generic_name_en') or
            product.get('generic_name') or
            'Unknown Product'
        )
        
        # Get brand
        brand = product.get('brands', '').split(',')[0].strip() or None
        
        # Get quantity
        quantity = product.get('quantity') or product.get('serving_size') or None
        
        # Detect category
        categories_tags = product.get('categories_tags', [])
        category = _detect_category(categories_tags, name)
        
        # Get image
        image_url = product.get('image_front_small_url') or product.get('image_url')
        
        return ProductInfo(
            barcode=barcode,
            name=name.strip(),
            brand=brand,
            category=category,
            quantity=quantity,
            image_url=image_url,
        )
        
    except Exception as e:
        current_app.logger.error(f"Barcode lookup error: {e}")
        return None


def lookup_barcode_upcitemdb(barcode: str) -> Optional[ProductInfo]:
    """
    Alternative lookup using UPCitemdb API (free tier: 100 req/day).
    
    Args:
        barcode: Product barcode (EAN/UPC).
    
    Returns:
        ProductInfo if found, None otherwise.
    """
    barcode = re.sub(r'\D', '', barcode)
    
    if not barcode or len(barcode) < 8:
        return None
    
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            return None
        
        item = items[0]
        
        name = item.get('title', 'Unknown Product')
        brand = item.get('brand') or None
        category = item.get('category', '').lower()
        
        # Map category
        detected_category = ItemCategory.OTHER.value
        for keyword, cat in CATEGORY_MAPPING.items():
            if keyword in category:
                detected_category = cat
                break
        
        return ProductInfo(
            barcode=barcode,
            name=name,
            brand=brand,
            category=detected_category,
            quantity=None,
            image_url=item.get('images', [None])[0] if item.get('images') else None,
        )
        
    except Exception as e:
        current_app.logger.error(f"UPCitemdb lookup error: {e}")
        return None
