from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def icone(nome: str, rotulo: str = "", classe: str = "icone"):
    """Ícone Lucide do sprite local. Sem rótulo, fica oculto para leitores de tela."""
    href = f"{static('img/icones.svg')}#{nome}"
    if rotulo:
        return format_html('<svg class="{}" role="img" aria-label="{}"><use href="{}"></use></svg>', classe, rotulo, href)
    return format_html('<svg class="{}" aria-hidden="true" focusable="false"><use href="{}"></use></svg>', classe, href)
