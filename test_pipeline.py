#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST_PIPELINE - Testa Pipeline 1 com arquivo único
===================================================
Permite testar velocidade com diferentes modelos.

Uso:
    python test_pipeline.py --input translated/Autor/Livro_pt.txt --model qwen2.5:7b
"""

import sys
import time
import argparse
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Importa componentes do pipeline
from processor import (
    ModelClient, create_chunks, process_chunks_parallel,
    extract_footnotes, generate_docx, count_tokens, logger
)
from config.settings import TEMPLATE_DOCX, OUTPUT_DOCX_DIR

# Modelos disponíveis
MODELS = {
    'qwen2.5:32b': {'size': '20GB', 'speed': 'Lento (melhor qualidade)', 'ram': '32GB'},
    'qwen2.5:14b': {'size': '9GB', 'speed': 'Médio (ótima qualidade)', 'ram': '16GB'},
    'qwen2.5:7b': {'size': '4.7GB', 'speed': 'Rápido (boa qualidade)', 'ram': '8GB'},
    'gemma2:2b': {'size': '1.6GB', 'speed': 'Muito rápido (ok)', 'ram': '4GB'},
    'llama3.2:3b': {'size': '2GB', 'speed': 'Rápido (boa qualidade)', 'ram': '4GB'},
}

async def test_pipeline(input_file: Path, model_name: str, author: str = "Teste"):
    """Testa pipeline com arquivo único."""

    print("="*70)
    print("🧪 TESTE DE PIPELINE - GOOGOLPLEX BOOKS")
    print("="*70)
    print(f"Arquivo: {input_file.name}")
    print(f"Modelo: {model_name}")

    if model_name in MODELS:
        info = MODELS[model_name]
        print(f"  • Tamanho: {info['size']}")
        print(f"  • Velocidade: {info['speed']}")
        print(f"  • RAM mínima: {info['ram']}")

    print("="*70)
    print()

    # 1. Lê arquivo
    print("📖 1/5 - Lendo arquivo...")
    start_read = time.time()

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    elapsed_read = time.time() - start_read
    print(f"   ✓ {len(text):,} caracteres (~{count_tokens(text):,} tokens)")
    print(f"   ⏱️ {elapsed_read:.2f}s")
    print()

    # 2. Cria chunks
    print("✂️ 2/5 - Dividindo em chunks...")
    start_chunk = time.time()

    chunks = create_chunks(text)

    elapsed_chunk = time.time() - start_chunk
    print(f"   ✓ {len(chunks)} chunks")
    print(f"   ⏱️ {elapsed_chunk:.2f}s")
    print()

    # 3. Inicializa modelo
    print(f"🤖 3/5 - Inicializando modelo {model_name}...")
    start_init = time.time()

    try:
        import os
        os.environ['OLLAMA_MODEL'] = model_name

        # Força reload do módulo com novo modelo
        import importlib
        import config.settings
        config.settings.OLLAMA_MODEL = model_name

        client = ModelClient('ollama')

        elapsed_init = time.time() - start_init
        print(f"   ✓ Modelo OK")
        print(f"   ⏱️ {elapsed_init:.2f}s")
        print()

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        print()
        print("💡 Dica:")
        print(f"   ollama pull {model_name}")
        return

    # 4. Correção (MEDIDOR DE VELOCIDADE)
    print(f"⚡ 4/5 - Corrigindo texto ({len(chunks)} chunks)...")
    print(f"   Modelo: {model_name}")
    print()

    start_corr = time.time()

    import asyncio
    corrected = await process_chunks_parallel(client, chunks, author, "correction")
    corrected_text = "\n\n".join(corrected)

    elapsed_corr = time.time() - start_corr
    chunks_per_sec = len(chunks) / elapsed_corr if elapsed_corr > 0 else 0

    print()
    print(f"   ✓ Correção concluída")
    print(f"   ⏱️ {elapsed_corr:.1f}s ({elapsed_corr/60:.1f} min)")
    print(f"   📊 Velocidade: {chunks_per_sec:.2f} chunks/s")
    print(f"   📊 Tempo/chunk: {elapsed_corr/len(chunks):.1f}s")
    print()

    # 5. Identificação de notas
    print("📝 5/5 - Identificando notas de rodapé...")
    start_notes = time.time()

    note_chunks = create_chunks(corrected_text)
    marked = await process_chunks_parallel(client, note_chunks, author, "footnotes")
    marked_text = "\n\n".join(marked)

    elapsed_notes = time.time() - start_notes
    print(f"   ✓ Notas identificadas")
    print(f"   ⏱️ {elapsed_notes:.1f}s")
    print()

    # 6. Extrai e gera DOCX
    print("📄 6/5 - Gerando DOCX...")
    start_docx = time.time()

    final_text, footnotes = extract_footnotes(marked_text)

    output_dir = OUTPUT_DOCX_DIR / "teste"
    output_file = output_dir / f"{input_file.stem}_TEST.docx"

    success = generate_docx(
        final_text, footnotes, TEMPLATE_DOCX,
        output_file, author, input_file.stem
    )

    elapsed_docx = time.time() - start_docx

    if success:
        print(f"   ✓ DOCX gerado: {output_file}")
        print(f"   ⏱️ {elapsed_docx:.2f}s")
    else:
        print(f"   ❌ Erro ao gerar DOCX")

    print()

    # RESUMO FINAL
    total_time = time.time() - start_read

    print("="*70)
    print("📊 RESUMO DO TESTE")
    print("="*70)
    print(f"Modelo: {model_name}")
    print(f"Arquivo: {input_file.name}")
    print(f"Tamanho: {len(text):,} chars, {len(chunks)} chunks")
    print()
    print(f"⏱️ TEMPOS:")
    print(f"  Leitura:   {elapsed_read:>8.2f}s")
    print(f"  Chunks:    {elapsed_chunk:>8.2f}s")
    print(f"  Modelo:    {elapsed_init:>8.2f}s")
    print(f"  Correção:  {elapsed_corr:>8.1f}s ({elapsed_corr/60:.1f} min) ⚡")
    print(f"  Notas:     {elapsed_notes:>8.1f}s")
    print(f"  DOCX:      {elapsed_docx:>8.2f}s")
    print(f"  {'─'*30}")
    print(f"  TOTAL:     {total_time:>8.1f}s ({total_time/60:.1f} min)")
    print()
    print(f"📊 PERFORMANCE:")
    print(f"  Velocidade: {chunks_per_sec:.2f} chunks/s")
    print(f"  Tempo/chunk: {elapsed_corr/len(chunks):.1f}s")
    print(f"  Notas encontradas: {len(footnotes)}")
    print()

    # Estimativa para livro completo
    if len(text) < 100000:  # Se for < 100k chars, estima livro completo
        full_book_chars = 300000  # 300k chars (livro médio)
        full_book_chunks = (full_book_chars / len(text)) * len(chunks)
        estimated_time = (full_book_chunks / chunks_per_sec) / 60 if chunks_per_sec > 0 else 0

        print(f"📈 ESTIMATIVA LIVRO COMPLETO (300k chars):")
        print(f"  Chunks estimados: {int(full_book_chunks)}")
        print(f"  Tempo estimado: {estimated_time:.1f} minutos")
        print()

    print("="*70)

def main():
    parser = argparse.ArgumentParser(
        description="Testa Pipeline 1 com arquivo único",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
MODELOS DISPONÍVEIS:

{'Modelo':<20} {'Tamanho':<10} {'Velocidade':<25} {'RAM'}
{'─'*70}
"""
    + "\n".join([
        f"{m:<20} {info['size']:<10} {info['speed']:<25} {info['ram']}"
        for m, info in MODELS.items()
    ]) + """

EXEMPLOS:

  # Teste rápido com modelo pequeno
  python test_pipeline.py --input translated/Autor/Livro_pt.txt --model gemma2:2b

  # Teste com modelo recomendado
  python test_pipeline.py --input translated/Autor/Livro_pt.txt --model qwen2.5:7b

  # Teste com modelo de máxima qualidade
  python test_pipeline.py --input translated/Autor/Livro_pt.txt --model qwen2.5:32b

  # Lista arquivos disponíveis
  python test_pipeline.py --list
"""
    )

    parser.add_argument('--input', '-i', type=Path,
                       help='Arquivo TXT traduzido para processar')
    parser.add_argument('--model', '-m', default='qwen2.5:7b',
                       help='Modelo Ollama (padrão: qwen2.5:7b)')
    parser.add_argument('--author', '-a', default='Teste',
                       help='Nome do autor')
    parser.add_argument('--list', action='store_true',
                       help='Lista arquivos traduzidos disponíveis')

    args = parser.parse_args()

    # Lista arquivos
    if args.list:
        translated_dir = Path(__file__).parent / "translated"
        files = list(translated_dir.rglob("*_pt.txt"))

        print("\n📚 ARQUIVOS TRADUZIDOS DISPONÍVEIS:\n")
        for i, f in enumerate(sorted(files)[:20], 1):
            size_kb = f.stat().st_size // 1024
            print(f"  {i:2d}. {f.relative_to(translated_dir)} ({size_kb}KB)")

        if len(files) > 20:
            print(f"\n  ... e mais {len(files)-20} arquivos")

        print(f"\nTotal: {len(files)} arquivos\n")
        return 0

    # Validação
    if not args.input:
        parser.print_help()
        return 1

    if not args.input.exists():
        print(f"❌ Arquivo não encontrado: {args.input}")
        return 1

    # Executa teste
    import asyncio
    asyncio.run(test_pipeline(args.input, args.model, args.author))

    return 0

if __name__ == '__main__':
    sys.exit(main())
