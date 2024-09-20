from django import template

from irhrs.export.utils.export import ExportBase

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Returns the value of the key in the dictionary
    :param dictionary:
    :param key:
    :return:
    """
    return dictionary.get(key)


@register.filter(name="get_attr")
def get_attr(obj, name):
    return ExportBase.get_column_cell(obj, name)


@register.filter(name="get_title")
def get_title(name):
    return ExportBase.get_column_head(name)