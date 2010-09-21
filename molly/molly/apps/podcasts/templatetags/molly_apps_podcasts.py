from django import template

register = template.Library()

@register.filter
def humanize_seconds(seconds):
    seconds = int(seconds)
    hours, seconds = seconds // 3600, seconds % 3600
    minutes, seconds = seconds // 60, seconds % 60
    if hours:
        return '%02dh%02dm' % (hours, minutes)
    elif minutes:
        return '%02dm%02ds' % (minutes, seconds)
    else:
        return '%02ds' % seconds
