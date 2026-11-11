"""Gera static/img/icones.svg (sprite) a partir do pacote lucide-static (licença ISC).

Uso: python scripts/gerar_icones.py <pasta lucide-static/icons>
Para adicionar um ícone, inclua o nome em ICONES e rode de novo.
"""
import re
import sys
from pathlib import Path

ICONES = [
    "house", "clipboard-list", "hard-hat", "boxes", "car", "plane", "file-pen-line", "chart-column",
    "settings", "log-out", "menu", "x", "users", "building-2", "shield-check", "plus", "circle-alert",
    "check", "lock-keyhole", "smartphone", "paperclip", "arrow-right", "pause", "circle-check",
]


def main(origem: Path, destino: Path) -> None:
    simbolos = []
    for nome in ICONES:
        svg = (origem / f"{nome}.svg").read_text(encoding="utf-8")
        corpo = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()
        corpo = re.sub(r"\s*\n\s*", "", corpo)
        simbolos.append(
            f'<symbol id="{nome}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{corpo}</symbol>')
    destino.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><!-- Lucide (ISC) https://lucide.dev -->'
        + "".join(simbolos) + "</svg>\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(__file__).resolve().parents[1] / "static" / "img" / "icones.svg")
