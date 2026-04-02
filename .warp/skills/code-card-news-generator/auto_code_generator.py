#!/usr/bin/env python3
"""
Auto Code Card Generator
Generate multiple code explanation cards from structured input
"""

import argparse
import os
import sys
import re
from generate_code_card import create_title_card, create_explanation_card


def parse_code_cards(content_text):
    """
    Parse structured code card content

    Expected format:
    TITLE: React|Router|Hooks
    SUBTITLE: Optional subtitle

    1. useNavigate
    Description: It's used for...
    Code:
    const navigate = useNavigate();
    ...
    Explanation: In this example...

    2. useParams
    ...
    """
    cards = []
    lines = content_text.strip().split('\n')

    title = None
    subtitle = None
    current_card = None
    current_section = None
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Parse TITLE
        if line.startswith('TITLE:'):
            title = line.replace('TITLE:', '').strip()
            i += 1
            continue

        # Parse SUBTITLE
        if line.startswith('SUBTITLE:'):
            subtitle = line.replace('SUBTITLE:', '').strip()
            i += 1
            continue

        # Parse card number (e.g., "1. useNavigate")
        match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match:
            # Save previous card
            if current_card:
                if code_lines:
                    current_card['code'] = '\n'.join(code_lines)
                    code_lines = []
                cards.append(current_card)

            # Start new card
            number = match.group(1)
            function_name = match.group(2)
            current_card = {
                'number': number,
                'function': function_name,
                'description': '',
                'code': '',
                'explanation': ''
            }
            current_section = None
            i += 1
            continue

        # Parse Description
        if line.startswith('Description:'):
            current_section = 'description'
            desc_text = line.replace('Description:', '').strip()
            if desc_text:
                current_card['description'] = desc_text
            i += 1
            continue

        # Parse Code section
        if line.startswith('Code:'):
            current_section = 'code'
            code_lines = []
            i += 1
            continue

        # Parse Explanation
        if line.startswith('Explanation:'):
            if code_lines:
                current_card['code'] = '\n'.join(code_lines)
                code_lines = []
            current_section = 'explanation'
            explain_text = line.replace('Explanation:', '').strip()
            if explain_text:
                current_card['explanation'] = explain_text
            i += 1
            continue

        # Add content to current section
        if current_card and line:
            if current_section == 'description':
                if current_card['description']:
                    current_card['description'] += ' ' + line
                else:
                    current_card['description'] = line
            elif current_section == 'code':
                code_lines.append(line)
            elif current_section == 'explanation':
                if current_card['explanation']:
                    current_card['explanation'] += ' ' + line
                else:
                    current_card['explanation'] = line

        i += 1

    # Save last card
    if current_card:
        if code_lines:
            current_card['code'] = '\n'.join(code_lines)
        cards.append(current_card)

    return title, subtitle, cards


def generate_code_cards(topic, output_dir, base_filename="code_card"):
    """
    Generate code explanation cards from stdin input

    Args:
        topic: Main topic (for logs)
        output_dir: Where to save cards
        base_filename: Base name for output files
    """
    print(f"주제: {topic}")
    print(f"출력 디렉토리: {output_dir}")
    print()
    print("=" * 60)
    print("코드 카드 내용을 입력하세요.")
    print()
    print("형식:")
    print("TITLE: React|Router|Hooks")
    print("SUBTITLE: (선택사항)")
    print()
    print("1. useNavigate")
    print("Description: 설명...")
    print("Code:")
    print("코드 예제...")
    print("Explanation: 추가 설명...")
    print()
    print("입력이 끝나면 Ctrl+D (Mac/Linux) 또는 Ctrl+Z (Windows)를 누르세요.")
    print("=" * 60)
    print()

    # Read all content from stdin
    content_text = sys.stdin.read()

    # Parse content
    title, subtitle, cards = parse_code_cards(content_text)

    if not title:
        print("❌ TITLE을 찾을 수 없습니다.")
        return []

    if not cards:
        print("❌ 카드 내용을 찾을 수 없습니다.")
        return []

    print(f"\n✓ 제목: {title}")
    if subtitle:
        print(f"✓ 부제목: {subtitle}")
    print(f"✓ {len(cards)}개의 카드를 찾았습니다.\n")

    # Generate files
    generated_files = []

    # Create title card
    title_filename = f"{base_filename}_00_title.png"
    title_path = os.path.join(output_dir, title_filename)

    print(f"제목 카드 생성 중...")
    create_title_card(
        title=title,
        subtitle=subtitle,
        output_path=title_path
    )
    generated_files.append(title_path)
    print(f"  ✓ 저장: {title_path}\n")

    # Create explanation cards
    for card in cards:
        filename = f"{base_filename}_{int(card['number']):02d}.png"
        output_path = os.path.join(output_dir, filename)

        print(f"카드 {card['number']} 생성 중: {card['function']}")

        create_explanation_card(
            number=card['number'],
            function_name=card['function'],
            description=card['description'],
            code=card['code'],
            explanation=card['explanation'] if card['explanation'] else None,
            output_path=output_path
        )

        generated_files.append(output_path)
        print(f"  ✓ 저장: {output_path}\n")

    return generated_files


def main():
    parser = argparse.ArgumentParser(
        description='Generate multiple code explanation cards from structured input'
    )

    parser.add_argument('--topic', required=True, help='Main topic (for display)')
    parser.add_argument('--output-dir', default='./output', help='Output directory')
    parser.add_argument('--base-filename', default='code_card', help='Base filename for cards')

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate cards
    files = generate_code_cards(
        topic=args.topic,
        output_dir=args.output_dir,
        base_filename=args.base_filename
    )

    if files:
        print("=" * 60)
        print(f"✅ 완료! {len(files)}개의 카드가 생성되었습니다.")
        print("=" * 60)
        for f in files:
            print(f"  📁 {f}")


if __name__ == '__main__':
    main()
