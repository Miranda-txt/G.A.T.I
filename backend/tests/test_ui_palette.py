"""Testes isolados dos tokens e da integracao visual Enterprise Blue.

Nao acessam banco, rede, views ou sessao: protegem apenas o contrato visual.
"""

import re
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
THEME_FILE = BACKEND_ROOT / "static/gati/css/gati-enterprise-blue.css"
TEMPLATE_ROOT = BACKEND_ROOT / "templates"

# Fonte normativa: GATI_Paleta_Cores_Enterprise_Blue_v1.0.0.md.
COLORS = {
    "sidebar": "#0F253D",
    "sidebar-hover": "#183A59",
    "sidebar-active": "#244B70",
    "sidebar-text": "#CBD5E1",
    "accent": "#1D4ED8",
    "accent-dark": "#1E40AF",
    "surface": "#FFFFFF",
    "paper": "#F8FAFC",
    "line": "#E2E8F0",
    "ink": "#0F172A",
    "muted": "#475569",
    "primary-soft": "#EFF6FF",
    "success": "#166534",
    "warning": "#92400E",
    "danger": "#B91C1C",
    "environment-staging-bg": "#FFF4CC",
    "environment-staging-text": "#78350F",
}


def luminance(color: str) -> float:
    """Calcula luminancia relativa segundo WCAG 2.x para uma cor RGB opaca."""
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(foreground: str, background: str) -> float:
    """Calcula a razao de contraste entre texto e superficie sem opacidade."""
    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class PaletteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = THEME_FILE.read_text(encoding="utf-8")

    def test_exact_palette_tokens(self):
        # Evita que a camada visual se desvie do documento aprovado.
        for token, hex_value in COLORS.items():
            pattern = rf"--{re.escape(token)}\s*:\s*{re.escape(hex_value)}\s*;"
            self.assertRegex(self.css, pattern, token)

        direct_colors = {value.upper() for value in re.findall(r"#[0-9a-fA-F]{6}\b", self.css)}
        self.assertEqual(direct_colors, set(COLORS.values()))

    def test_theme_is_loaded_after_legacy_css_in_private_and_public_screens(self):
        for name in ("base.html", "public.html"):
            with self.subTest(template=name):
                html = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
                legacy = "{% static 'gati/css/gati.css' %}"
                blue = "{% static 'gati/css/gati-enterprise-blue.css' %}"
                self.assertIn(legacy, html)
                self.assertEqual(html.count(blue), 1)
                self.assertLess(html.index(legacy), html.index(blue))

    def test_accessible_text_pairings(self):
        pairs = (
            ("surface", "accent"),
            ("surface", "accent-dark"),
            ("surface", "sidebar-active"),
            ("sidebar-text", "sidebar"),
            ("ink", "paper"),
            ("muted", "surface"),
            ("environment-staging-text", "environment-staging-bg"),
            ("success", "surface"),
            ("warning", "surface"),
            ("danger", "surface"),
        )
        for foreground, background in pairs:
            with self.subTest(pair=f"{foreground}/{background}"):
                self.assertGreaterEqual(contrast(COLORS[foreground], COLORS[background]), 4.5)

    def test_semantic_and_focus_states_are_not_removed(self):
        for selector in (
            ":focus-visible",
            ".sidebar nav > a.selected",
            ".btn-primary:hover",
            ".environment-banner",
            ".development-banner",
            ".alert-success",
            ".alert-warning",
            ".alert-danger",
            ".public-body",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, self.css)
        self.assertNotIn("!important", self.css)
        self.assertNotIn("@import", self.css)

    def test_existing_staging_banner_remains_textually_identified(self):
        html = (TEMPLATE_ROOT / "base.html").read_text(encoding="utf-8")
        self.assertIn("AMBIENTE DE HOMOLOGAÇÃO", html)
        self.assertIn("AMBIENTE LOCAL", html)


if __name__ == "__main__":
    unittest.main()
