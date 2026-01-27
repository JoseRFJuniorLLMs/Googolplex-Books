#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RUN_ALL.PY - Executa Hunter e Translator em Paralelo
=====================================================
Automatiza todo o processo:
1. Verifica/baixa modelo Ollama em paralelo com download de livros
2. Traduz livros automaticamente

Uso:
    python run_all.py --languages en es --limit 20
    python run_all.py --languages en es ru --limit 50 --model qwen2.5:7b
"""

import os
import sys
import time
import argparse
import subprocess
import threading
from pathlib import Path

# Configurações
sys.path.insert(0, str(Path(__file__).parent))
from config.settings import OLLAMA_BASE_URL

# ============================================================================
# VERIFICAÇÕES
# ============================================================================

def check_ollama_running():
    """Verifica se Ollama está rodando."""
    import requests
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama_background():
    """Inicia Ollama em background (se não estiver rodando)."""
    if check_ollama_running():
        print("✅ Ollama já está rodando")
        return None

    print("🚀 Iniciando Ollama em background...")

    if sys.platform == 'win32':
        # Windows: inicia sem janela
        process = subprocess.Popen(
            ['ollama', 'serve'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
    else:
        # Linux/Mac
        process = subprocess.Popen(
            ['ollama', 'serve'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    # Espera iniciar
    for i in range(10):
        time.sleep(1)
        if check_ollama_running():
            print("✅ Ollama iniciado com sucesso")
            return process

    print("⚠️ Ollama pode não ter iniciado corretamente")
    return process

def check_model_exists(model_name: str) -> bool:
    """Verifica se modelo existe localmente."""
    import requests
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return any(m['name'] == model_name for m in models)
    except:
        pass
    return False

# ============================================================================
# EXECUÇÃO EM PARALELO
# ============================================================================

class ParallelRunner:
    """Executa comandos em paralelo com threads."""

    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()

    def run_command(self, name: str, command: list, cwd: str = None):
        """Executa comando e armazena resultado."""
        print(f"\n🔹 [{name}] INICIANDO: {' '.join(command)}")
        start = time.time()

        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=False,
                text=True
            )

            elapsed = time.time() - start
            success = result.returncode == 0

            with self.lock:
                self.results[name] = {
                    'success': success,
                    'elapsed': elapsed,
                    'returncode': result.returncode
                }

            status = "✅ SUCESSO" if success else "❌ FALHOU"
            print(f"\n{status} [{name}] - {elapsed:.1f}s")

        except Exception as e:
            elapsed = time.time() - start
            with self.lock:
                self.results[name] = {
                    'success': False,
                    'elapsed': elapsed,
                    'error': str(e)
                }
            print(f"\n❌ ERRO [{name}]: {e}")

    def run_parallel(self, tasks: list):
        """Executa múltiplas tarefas em paralelo."""
        threads = []

        for name, command, cwd in tasks:
            thread = threading.Thread(
                target=self.run_command,
                args=(name, command, cwd)
            )
            thread.start()
            threads.append(thread)

        # Aguarda todos terminarem
        for thread in threads:
            thread.join()

        return all(r['success'] for r in self.results.values())

# ============================================================================
# MAIN
# ============================================================================

def main():
    # Fix Windows encoding
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description="Executa Hunter + Translator em PARALELO",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--languages', '-l', nargs='+', default=['en', 'es'],
                       help='Idiomas para baixar e traduzir (en, es, ru, fr, de)')
    parser.add_argument('--limit', '-n', type=int, default=20,
                       help='Limite de livros por idioma')
    parser.add_argument('--model', '-m', default='qwen2.5:7b',
                       help='Modelo Ollama (padrão: qwen2.5:7b)')
    parser.add_argument('--skip-download', action='store_true',
                       help='Pula download de livros (só traduz)')
    parser.add_argument('--skip-translate', action='store_true',
                       help='Pula tradução (só baixa livros)')

    args = parser.parse_args()

    base_dir = Path(__file__).parent

    print("="*70)
    print("🚀 GOOGOLPLEX-BOOKS - EXECUÇÃO PARALELA")
    print("="*70)
    print(f"Idiomas: {', '.join(args.languages)}")
    print(f"Limite: {args.limit} livros por idioma")
    print(f"Modelo: {args.model}")
    print("="*70)

    # ========================================================================
    # FASE 1: PREPARAÇÃO (Ollama)
    # ========================================================================

    print("\n" + "="*70)
    print("📋 FASE 1: PREPARAÇÃO")
    print("="*70)

    # Inicia Ollama
    ollama_process = start_ollama_background()

    if not check_ollama_running():
        print("\n❌ ERRO: Ollama não está rodando!")
        print("💡 Inicie manualmente: ollama serve")
        return 1

    # ========================================================================
    # FASE 2: DOWNLOAD PARALELO (Modelo + Livros)
    # ========================================================================

    print("\n" + "="*70)
    print("📥 FASE 2: DOWNLOADS EM PARALELO")
    print("="*70)

    runner = ParallelRunner()
    tasks = []

    # Task 1: Baixar modelo (se necessário)
    if not check_model_exists(args.model):
        print(f"📥 Modelo {args.model} não encontrado, será baixado...")
        tasks.append((
            "Download Modelo",
            ['ollama', 'pull', args.model],
            None
        ))
    else:
        print(f"✅ Modelo {args.model} já existe")

    # Task 2: Baixar livros (Hunter)
    if not args.skip_download:
        hunter_cmd = [
            sys.executable,
            'run_hunter.py',
            '--languages'] + args.languages + [
            '--limit', str(args.limit)
        ]
        tasks.append((
            "Hunter (Baixar Livros)",
            hunter_cmd,
            str(base_dir)
        ))
    else:
        print("⏭️ Download de livros PULADO")

    # Executa tarefas em paralelo
    if tasks:
        print(f"\n🔄 Executando {len(tasks)} tarefas em PARALELO...\n")
        success = runner.run_parallel(tasks)

        if not success:
            print("\n❌ Algumas tarefas falharam!")
            for name, result in runner.results.items():
                if not result['success']:
                    print(f"  ❌ {name}: {result.get('error', 'Falhou')}")
            return 1
    else:
        print("✅ Nenhum download necessário")

    # ========================================================================
    # FASE 3: TRADUÇÃO (Após downloads)
    # ========================================================================

    if args.skip_translate:
        print("\n⏭️ Tradução PULADA")
        print("\n✅ PROCESSO CONCLUÍDO!")
        return 0

    print("\n" + "="*70)
    print("🌍 FASE 3: TRADUÇÃO")
    print("="*70)

    # Aguarda um pouco para garantir que modelo está pronto
    time.sleep(2)

    translator_cmd = [
        sys.executable,
        'run_translator.py',
        '--languages'] + args.languages + [
        '--model', args.model
    ]

    print(f"\n🔄 Executando tradutor: {' '.join(translator_cmd)}\n")

    try:
        result = subprocess.run(
            translator_cmd,
            cwd=str(base_dir)
        )

        if result.returncode != 0:
            print(f"\n❌ Tradutor falhou com código: {result.returncode}")
            return 1

    except Exception as e:
        print(f"\n❌ Erro ao executar tradutor: {e}")
        return 1

    # ========================================================================
    # RESUMO FINAL
    # ========================================================================

    print("\n" + "="*70)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("="*70)

    # Estatísticas
    txt_dir = base_dir / "txt"
    translated_dir = base_dir / "translated"

    if txt_dir.exists():
        txt_count = len(list(txt_dir.rglob("*.txt")))
        print(f"📚 Livros baixados: {txt_count}")

    if translated_dir.exists():
        trans_count = len(list(translated_dir.rglob("*_pt.txt")))
        print(f"🌍 Livros traduzidos: {trans_count}")

    print(f"\n📁 Livros: {txt_dir}")
    print(f"📁 Traduções: {translated_dir}")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido pelo usuário")
        sys.exit(1)
