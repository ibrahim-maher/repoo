from django import template

register = template.Library()

@register.filter
def get_dict_value(dictionary, key):
    """Get value from dictionary by key"""
    return dictionary.get(key, '')

@register.filter
def get_field_content(badge_contents, field_name):
    """Get the BadgeContent object for a specific field name"""
    return badge_contents.filter(field_name=field_name).first()

@register.filter
def get_position_x(content):
    """Get X position for a field"""
    return content.position_x if content else 0

@register.filter
def get_position_y(content):
    """Get Y position for a field"""
    return content.position_y if content else 0

@register.filter
def get_font_size(content):
    """Get font size for a field"""
    return content.font_size if content else 12

@register.filter
def get_font_family(content):
    """Get font family for a field"""
    return content.font_family if content else 'Helvetica'

@register.filter
def get_font_color(content):
    """Get font color for a field"""
    return content.font_color if content else '#000000'

@register.filter
def get_is_bold(content):
    """Check if field should be bold"""
    return content.is_bold if content else False

@register.filter
def get_is_italic(content):
    """Check if field should be italic"""
    return content.is_italic if content else False

@register.filter
def get_item(list_data, index):
    """
    Template filter to get an item at a specific index from a list
    """
    try:
        return list_data[index]
    except (IndexError, TypeError):
        return None
