"""
Custom template filters for the restaurant app.
Load with: {% load restaurant_extras %}
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Return dictionary[key], gracefully returning '' if missing."""
    if dictionary is None:
        return ''
    return dictionary.get(key, '')
