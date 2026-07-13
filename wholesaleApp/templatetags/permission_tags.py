from django import template

register = template.Library()

@register.filter(name='dict_key')
def dict_key(d, key):
    """Retrieve dictionary value by dynamic key variable."""
    try:
        return d.get(key, {}).items()
    except (AttributeError, TypeError):
        return []
