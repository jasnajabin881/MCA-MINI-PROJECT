from django import template

register = template.Library()

@register.filter
def range_filter(value):
    """Creates a range for use in a for loop in templates."""
    return range(int(value))

@register.filter
def multiply(value, arg):
    """Multiplies two values"""
    return value * arg

@register.filter
def multiply(value, arg):
    return value * arg