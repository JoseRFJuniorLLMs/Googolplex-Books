#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RUN_PROCESSOR_BILINGUAL.PY - Executa Pipeline 2
================================================
Pipeline 2: Versão Bilíngue + Semantic Priming

Uso:
  python run_processor_bilingual.py --input translated/Autor/Livro_pt.txt
  python run_processor_bilingual.py --batch  # processa todos
"""

import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from processor_bilingual import main

if __name__ == "__main__":
    sys.exit(main())
