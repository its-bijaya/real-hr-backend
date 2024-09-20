from django import template

register = template.Library()


@register.simple_tag
def reduce_percentage(value_in_100_percent, value_in_desired_percent):
    """
    Reduce 100% to certain percentage
    Ex: reduce_percentage(50, 50) results 25
        reduce_percentage(100, 50) results 50
        reduce_percentage(100, 25) results 25

    :param value_in_100_percent: value to be converted
    :param value_in_desired_percent: % to be converted
    :return:
    """

    try:
        dividend_value = 100 / value_in_desired_percent
        return '{:0.2f}'.format(
            float(value_in_100_percent) / float(dividend_value)
        )
    except (ValueError, TypeError):
        return 'No given'


@register.simple_tag
def sort_list(sort_item, sort_by, reverse=False):
    return True


@register.simple_tag
def sum_float(*numbers):
    try:
        return sum([float(i) for i in numbers])
    except ValueError:
        return float(0)
