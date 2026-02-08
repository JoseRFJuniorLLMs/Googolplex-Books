#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST_SIMPLE - Teste simples de velocidade de modelo
====================================================
Testa velocidade do modelo Ollama processando texto.

Uso:
    python test_simple.py --model qwen2.5:7b
    python test_simple.py --list
"""

import sys
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Erro: requests não instalado")
    print("💡 Instale com: pip install requests")
    sys.exit(1)

MODELS = {
    'qwen2.5:32b': '20GB - Lento (melhor qualidade)',
    'qwen2.5:14b': '9GB - Médio (ótima qualidade)',
    'qwen2.5:7b': '4.7GB - Rápido (boa qualidade) ⚡',
    'gemma2:2b': '1.6GB - Muito rápido (ok) ⚡⚡',
    'llama3.2:3b': '2GB - Rápido (boa qualidade) ⚡',
}

def test_model(model_name: str, sample_text: str = None):
    """Testa velocidade de um modelo."""

    print("="*70)
    print("🧪 TESTE DE VELOCIDADE - MODELO OLLAMA")
    print("="*70)
    print(f"Modelo: {model_name}")
    if model_name in MODELS:
        print(f"Info: {MODELS[model_name]}")
    print("="*70)
    print()

    # Verifica se modelo existe
    print("1️⃣ Verificando modelo...")
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code != 200:
            print("❌ Ollama não está rodando")
            print("💡 Inicie com: ollama serve")
            return

        models_list = [m['name'] for m in r.json().get('models', [])]
        if model_name not in models_list:
            print(f"❌ Modelo {model_name} não encontrado")
            print(f"💡 Baixe com: ollama pull {model_name}")
            print()
            print(f"Modelos instalados: {models_list}")
            return

        print(f"✅ Modelo {model_name} encontrado")
        print()

    except Exception as e:
        print(f"❌ Erro ao conectar ao Ollama: {e}")
        return

    # Texto de teste
    if sample_text is None:
        sample_text = """
        A arte de observar a si mesmo é uma prática essencial no trabalho de
        transformação interior. Gurdjieff enfatizava que o homem vive em um
        estado de sono, realizando todas as suas ações de maneira mecânica e
        automática. Para despertar, é necessário começar a se observar sem
        julgamento, apenas notando o que ocorre internamente.

        A observação de si deve ser imparcial, como um cientista observando um
        experimento. Não se trata de julgar ou criticar, mas simplesmente de
        ver a realidade tal como ela é. Esta prática gradualmente revela nossos
        automatismos, nossos padrões habituais de pensamento e comportamento.
        """

    # Teste de velocidade
    print("2️⃣ Testando correção de texto...")
    print()

    prompt = f"""Corrija o texto abaixo (ortografia, gramática, pontuação).

TEXTO:
\"\"\"
{sample_text}
\"\"\"

TEXTO CORRIGIDO:"""

    start = time.time()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 8192,
                }
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            corrected = result.get('response', '').strip()
            elapsed = time.time() - start

            print("✅ Correção concluída!")
            print()
            print("─"*70)
            print("RESULTADO:")
            print("─"*70)
            print(corrected[:300] + "..." if len(corrected) > 300 else corrected)
            print("─"*70)
            print()
            print(f"⏱️ TEMPO: {elapsed:.1f}s")
            print(f"📊 TOKENS: ~{len(sample_text)//4} → ~{len(corrected)//4}")
            print(f"📊 VELOCIDADE: ~{len(corrected)/elapsed:.0f} chars/s")
            print()

            # Estimativa para livro
            book_chars = 300000  # 300k chars
            chunks = book_chars // len(sample_text)
            total_time_min = (chunks * elapsed) / 60

            print(f"📈 ESTIMATIVA LIVRO COMPLETO (300k chars, ~150 chunks):")
            print(f"   Tempo estimado: {total_time_min:.1f} minutos ({total_time_min/60:.1f} horas)")
            print()

        else:
            print(f"❌ Erro: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ Erro: {e}")

    print("="*70)

def list_files():
    """Lista arquivos traduzidos."""
    translated_dir = Path(__file__).parent / "translated"

    if not translated_dir.exists():
        print(f"❌ Pasta não existe: {translated_dir}")
        return

    files = list(translated_dir.rglob("*_pt.txt"))

    print()
    print("="*70)
    print("📚 ARQUIVOS TRADUZIDOS DISPONÍVEIS")
    print("="*70)
    print()

    for i, f in enumerate(sorted(files)[:30], 1):
        size_kb = f.stat().st_size // 1024
        rel_path = str(f.relative_to(translated_dir))
        print(f"  {i:2d}. {rel_path:<50} ({size_kb:>4}KB)")

    if len(files) > 30:
        print(f"\n  ... e mais {len(files)-30} arquivos")

    print()
    print(f"Total: {len(files)} arquivos traduzidos")
    print()
    print("="*70)

def main():
    parser = argparse.ArgumentParser(
        description="Testa velocidade de modelos Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MODELOS DISPONÍVEIS:

  qwen2.5:32b  - 20GB - Lento (melhor qualidade)
  qwen2.5:14b  - 9GB  - Médio (ótima qualidade)
  qwen2.5:7b   - 4.7GB - Rápido (boa qualidade) ⚡ RECOMENDADO
  gemma2:2b    - 1.6GB - Muito rápido (ok) ⚡⚡
  llama3.2:3b  - 2GB  - Rápido (boa qualidade) ⚡

EXEMPLOS:

  # Teste rápido
  python test_simple.py --model gemma2:2b

  # Teste com modelo recomendado
  python test_simple.py --model qwen2.5:7b

  # Lista arquivos disponíveis
  python test_simple.py --list
"""
    )

    parser.add_argument('--model', '-m', default='qwen2.5:7b',
                       help='Modelo Ollama (padrão: qwen2.5:7b)')
    parser.add_argument('--list', action='store_true',
                       help='Lista arquivos traduzidos disponíveis')

    args = parser.parse_args()

    if args.list:
        list_files()
        return 0

    test_model(args.model)
    return 0

if __name__ == '__main__':
    sys.exit(main())
