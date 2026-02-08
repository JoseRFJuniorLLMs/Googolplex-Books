#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reorganiza arquivos TXT em subpastas por idioma.
txt/*.txt → txt/[idioma]/*.txt
"""

import sys
import io
import shutil
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    txt_dir = Path('txt')

    # Cria subpastas
    for lang in ['en', 'es', 'pt', 'ru', 'unknown']:
        (txt_dir / lang).mkdir(exist_ok=True)

    # Lista arquivos na raiz de txt/
    files = [f for f in txt_dir.glob('*.txt') if f.is_file()]

    print(f"📂 Organizando {len(files)} arquivos...")
    print()

    stats = {'en': 0, 'es': 0, 'pt': 0, 'ru': 0, 'unknown': 0}

    for txt_file in files:
        # Detecta idioma pelo sufixo
        if txt_file.stem.endswith('_en'):
            target_dir = txt_dir / 'en'
            lang = 'en'
        elif txt_file.stem.endswith('_es'):
            target_dir = txt_dir / 'es'
            lang = 'es'
        elif txt_file.stem.endswith('_pt'):
            target_dir = txt_dir / 'pt'
            lang = 'pt'
        elif txt_file.stem.endswith('_ru'):
            target_dir = txt_dir / 'ru'
            lang = 'ru'
        else:
            target_dir = txt_dir / 'unknown'
            lang = 'unknown'

        # Move arquivo
        target_path = target_dir / txt_file.name
        shutil.move(str(txt_file), str(target_path))
        stats[lang] += 1

    print("✅ Organização concluída!")
    print()
    print("📊 Estatísticas:")
    for lang, count in sorted(stats.items()):
        if count > 0:
            print(f"  {lang}: {count} arquivos")
    print()
    print("📁 Nova estrutura:")
    print("  txt/")
    for lang, count in sorted(stats.items()):
        if count > 0:
            print(f"    {lang}/ ({count} arquivos)")

if __name__ == '__main__':
    main()
