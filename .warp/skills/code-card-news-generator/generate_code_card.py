#!/usr/bin/env python3
"""
Code Card News Generator
Generate code explanation cards with syntax highlighting
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import textwrap


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width"""
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            lines.append('')
            continue

        words = paragraph.split(' ')
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

    return lines


def create_title_card(
    title,
    subtitle=None,
    output_path="title_card.png",
    width=600,
    height=600
):
    """
    Create a title card for code series

    Args:
        title: Main title (can use | to separate parts for coloring)
        subtitle: Optional subtitle
        output_path: Where to save the image
        width: Image width
        height: Image height
    """
    # Colors
    bg_color = "#1a1a1a"  # Dark background
    text_color = "#ffffff"  # White text
    accent_color = "#26de81"  # Green accent

    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Load fonts
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cafe24_font = os.path.join(script_dir, "fonts", "Cafe24Ssurround-v2.0.ttf")

    try:
        title_font = ImageFont.truetype(cafe24_font, 60)
        subtitle_font = ImageFont.truetype(cafe24_font, 30)
    except:
        print("Warning: Using default font", file=sys.stderr)
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # Parse title for colored parts (using | as separator)
    # Example: "React|Router|Hooks" -> "React" (white), "Router" (pink), "Hooks" (white)
    if '|' in title:
        parts = title.split('|')

        # Calculate total height
        current_y = height // 2 - 100

        for i, part in enumerate(parts):
            color = accent_color if i % 2 == 1 else text_color
            bbox = draw.textbbox((0, 0), part, font=title_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (width - text_width) // 2
            draw.text((x, current_y), part, fill=color, font=title_font)
            current_y += text_height + 20
    else:
        # Single title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        if subtitle:
            y -= 50

        draw.text((x, y), title, fill=text_color, font=title_font)

    # Draw subtitle if provided
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_width = bbox[2] - bbox[0]
        sub_x = (width - sub_width) // 2
        sub_y = (height // 2) + 100

        draw.text((sub_x, sub_y), subtitle, fill=accent_color, font=subtitle_font)

    # Save
    img.save(output_path)
    print(f"Title card saved: {output_path}")


def create_explanation_card(
    number,
    function_name,
    description,
    code,
    explanation=None,
    output_path="explanation_card.png",
    width=600,
    height=600
):
    """
    Create an explanation card with code example

    Args:
        number: Card number (e.g., "1")
        function_name: Function/concept name (e.g., "useNavigate")
        description: Korean description
        code: Code example
        explanation: Additional explanation
        output_path: Where to save
        width: Image width
        height: Image height
    """
    # Colors
    bg_color = "#1a1a1a"
    text_color = "#ffffff"
    accent_color = "#26de81"  # Green accent
    code_bg = "#2d2d2d"
    code_border = accent_color

    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Load fonts
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cafe24_font = os.path.join(script_dir, "fonts", "Cafe24Ssurround-v2.0.ttf")
    consolas_font = os.path.join(script_dir, "fonts", "Consolas-Regular.ttf")

    try:
        title_font = ImageFont.truetype(cafe24_font, 36)
        desc_font = ImageFont.truetype(cafe24_font, 20)

        # Use Consolas for code (bundled)
        try:
            code_font = ImageFont.truetype(consolas_font, 18)
        except:
            # Fallback to system monospace fonts
            code_font = None
            mono_fonts = [
                "/System/Library/Fonts/Menlo.ttc",
                "/System/Library/Fonts/Monaco.dfont",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
            ]
            for mono_path in mono_fonts:
                try:
                    code_font = ImageFont.truetype(mono_path, 18)
                    break
                except:
                    continue

            if code_font is None:
                code_font = ImageFont.truetype(cafe24_font, 16)

        explain_font = ImageFont.truetype(cafe24_font, 18)
    except Exception as e:
        print(f"Warning: Font loading issue: {e}", file=sys.stderr)
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        code_font = ImageFont.load_default()
        explain_font = ImageFont.load_default()

    # Layout
    padding = 40
    max_text_width = width - (padding * 2)

    # Calculate total content height first for vertical centering
    # Header
    header_text = f"{number}. {function_name}"
    bbox = draw.textbbox((0, 0), header_text, font=title_font)
    header_height = bbox[3] - bbox[1]

    # Description
    desc_lines = wrap_text(description, desc_font, max_text_width, draw)
    desc_height = 0
    for line in desc_lines:
        bbox = draw.textbbox((0, 0), line, font=desc_font)
        desc_height += bbox[3] - bbox[1] + 10

    # Code box
    code_lines = code.strip().split('\n')
    code_box_padding = 20
    max_code_width = 0

    for line in code_lines:
        bbox = draw.textbbox((0, 0), line, font=code_font)
        line_width = bbox[2] - bbox[0]
        max_code_width = max(max_code_width, line_width)

    code_box_width = min(max_code_width + (code_box_padding * 2), max_text_width)
    code_box_height = len(code_lines) * 28 + (code_box_padding * 2)

    # Explanation
    explain_height = 0
    if explanation:
        explain_lines = wrap_text(explanation, explain_font, max_text_width, draw)
        for line in explain_lines:
            bbox = draw.textbbox((0, 0), line, font=explain_font)
            explain_height += bbox[3] - bbox[1] + 8

    # Total height
    total_height = header_height + 25 + desc_height + 20 + code_box_height
    if explanation:
        total_height += 25 + explain_height

    # Start Y position for vertical centering
    current_y = (height - total_height) // 2

    # Draw number and function name
    draw.text((padding, current_y), header_text, fill=accent_color, font=title_font)
    current_y += header_height + 25

    # Draw description
    for line in desc_lines:
        draw.text((padding, current_y), line, fill=text_color, font=desc_font)
        bbox = draw.textbbox((padding, current_y), line, font=desc_font)
        current_y = bbox[3] + 10

    current_y += 20

    # Draw code box
    code_box_left = padding
    code_box_top = current_y
    code_box_right = code_box_left + code_box_width
    code_box_bottom = code_box_top + code_box_height

    # Draw code box background
    draw.rectangle(
        [(code_box_left, code_box_top), (code_box_right, code_box_bottom)],
        fill=code_bg
    )

    # Draw code box border
    draw.rectangle(
        [(code_box_left, code_box_top), (code_box_right, code_box_bottom)],
        outline=code_border,
        width=3
    )

    # Draw code lines
    code_y = code_box_top + code_box_padding
    for line in code_lines:
        # Simple syntax highlighting
        if 'const' in line or 'let' in line or 'var' in line:
            # Keywords in pink
            parts = line.split(' ')
            code_x = code_box_left + code_box_padding
            for part in parts:
                if part in ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while']:
                    draw.text((code_x, code_y), part, fill=accent_color, font=code_font)
                else:
                    draw.text((code_x, code_y), part, fill=text_color, font=code_font)
                bbox = draw.textbbox((code_x, code_y), part + ' ', font=code_font)
                code_x = bbox[2]
        else:
            draw.text((code_box_left + code_box_padding, code_y), line, fill=text_color, font=code_font)

        code_y += 28

    current_y = code_box_bottom + 25

    # Draw explanation if provided
    if explanation:
        for line in explain_lines:
            # Highlight specific words in pink
            if 'will navigate' in line or '/home' in line:
                # Split and color
                words = line.split(' ')
                explain_x = padding
                for word in words:
                    if word in ['will', 'navigate', 'user', '/home', 'route'] or word.startswith('/'):
                        color = accent_color
                    else:
                        color = text_color

                    draw.text((explain_x, current_y), word, fill=color, font=explain_font)
                    bbox = draw.textbbox((explain_x, current_y), word + ' ', font=explain_font)
                    explain_x = bbox[2]
            else:
                draw.text((padding, current_y), line, fill=text_color, font=explain_font)

            bbox = draw.textbbox((padding, current_y), line, font=explain_font)
            current_y = bbox[3] + 8

    # Save
    img.save(output_path)
    print(f"Explanation card saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate code explanation cards')

    subparsers = parser.add_subparsers(dest='card_type', help='Card type')

    # Title card
    title_parser = subparsers.add_parser('title', help='Create title card')
    title_parser.add_argument('--title', required=True, help='Title (use | for colored parts)')
    title_parser.add_argument('--subtitle', help='Subtitle')
    title_parser.add_argument('--output', required=True, help='Output path')

    # Explanation card
    explain_parser = subparsers.add_parser('explain', help='Create explanation card')
    explain_parser.add_argument('--number', required=True, help='Card number')
    explain_parser.add_argument('--function', required=True, help='Function name')
    explain_parser.add_argument('--description', required=True, help='Description')
    explain_parser.add_argument('--code', required=True, help='Code example')
    explain_parser.add_argument('--explanation', help='Additional explanation')
    explain_parser.add_argument('--output', required=True, help='Output path')

    args = parser.parse_args()

    if args.card_type == 'title':
        create_title_card(
            title=args.title,
            subtitle=args.subtitle,
            output_path=args.output
        )
    elif args.card_type == 'explain':
        create_explanation_card(
            number=args.number,
            function_name=args.function,
            description=args.description,
            code=args.code,
            explanation=args.explanation,
            output_path=args.output
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
