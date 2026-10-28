"""Validadores reutilizáveis do projeto."""

from django.conf import settings
from django.core.exceptions import ValidationError


def validar_imagem_tamanho(arquivo):
    """Limita o tamanho dos arquivos de imagem enviados (MAX_UPLOAD_SIZE)."""
    limite = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
    if arquivo and arquivo.size and arquivo.size > limite:
        raise ValidationError(
            f'O arquivo excede o tamanho máximo permitido de '
            f'{limite // (1024 * 1024)}MB.'
        )