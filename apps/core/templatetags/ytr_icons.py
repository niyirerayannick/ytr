from django import template
from django.utils.safestring import mark_safe

from apps.core.icons import icon_svg, icon_tile_svg

register = template.Library()


@register.simple_tag
def icon(name, size=24, stroke="true"):
    return mark_safe(icon_svg(name, size=size, stroke=(stroke == "true")))


@register.simple_tag
def icon_tile(name, bg="#241A3D", size="100%"):
    return mark_safe(icon_tile_svg(name, bg=bg, size=size))
