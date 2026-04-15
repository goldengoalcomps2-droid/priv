#!/usr/bin/env python3
"""
Generate PNG app icons from icon.svg for PWA / Android app.
Requires: Pillow and cairosvg
Install: pip install Pillow cairosvg

Usage: python generate-icons.py
"""
import os
from pathlib import Path

ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
ICON_DIR = Path(__file__).parent
SVG_FILE = ICON_DIR / "icon.svg"


def generate_icons():
    try:
        import cairosvg
    except ImportError:
        print("Installing cairosvg...")
        os.system("pip install cairosvg Pillow")
        import cairosvg

    if not SVG_FILE.exists():
        print(f"Error: {SVG_FILE} not found")
        return

    for size in ICON_SIZES:
        output = ICON_DIR / f"icon-{size}.png"
        cairosvg.svg2png(
            url=str(SVG_FILE),
            write_to=str(output),
            output_width=size,
            output_height=size,
        )
        print(f"Generated {output.name}")

    # Also create Apple touch icon
    apple_icon = ICON_DIR / "apple-touch-icon.png"
    cairosvg.svg2png(
        url=str(SVG_FILE),
        write_to=str(apple_icon),
        output_width=180,
        output_height=180,
    )
    print(f"Generated {apple_icon.name}")

    # Favicon
    favicon = ICON_DIR / "favicon.png"
    cairosvg.svg2png(
        url=str(SVG_FILE),
        write_to=str(favicon),
        output_width=32,
        output_height=32,
    )
    print(f"Generated {favicon.name}")

    print("\nDone! All icons generated successfully.")


if __name__ == "__main__":
    generate_icons()
