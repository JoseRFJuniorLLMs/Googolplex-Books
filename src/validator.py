# -*- coding: utf-8 -*-
"""
VALIDATOR.PY - Validação de Arquivos
=====================================
Valida se arquivos TXT estão completos antes de processar.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

# Configurações
MIN_FILE_SIZE = 5000  # 5KB (configurável via .env)
MIN_CONTENT_LENGTH = 500  # 500 caracteres mínimo

class FileValidator:
    """Valida arquivos e registra inválidos."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Cria tabela de arquivos inválidos."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS invalid_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_path ON invalid_files(file_path)')

    def validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Valida arquivo TXT.

        Returns:
            (is_valid, reason_if_invalid)
        """
        # 1. Verifica se existe
        if not file_path.exists():
            return False, "Arquivo não existe"

        # 2. Verifica tamanho mínimo
        file_size = file_path.stat().st_size
        if file_size < MIN_FILE_SIZE:
            return False, f"Arquivo muito pequeno ({file_size} bytes < {MIN_FILE_SIZE} bytes)"

        # 3. Verifica conteúdo
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Remove espaços e conta caracteres
            content_clean = content.strip()

            if len(content_clean) < MIN_CONTENT_LENGTH:
                return False, f"Conteúdo muito curto ({len(content_clean)} chars < {MIN_CONTENT_LENGTH} chars)"

            # Verifica se não é só lixo (caracteres não ASCII demais)
            ascii_ratio = sum(1 for c in content_clean if ord(c) < 128) / len(content_clean)
            if ascii_ratio < 0.5:  # Menos de 50% ASCII pode ser lixo
                return False, f"Conteúdo suspeito (apenas {ascii_ratio*100:.1f}% ASCII)"

            return True, None

        except Exception as e:
            return False, f"Erro ao ler arquivo: {e}"

    def register_invalid(self, file_path: Path, reason: str):
        """Registra arquivo inválido no banco."""
        file_size = file_path.stat().st_size if file_path.exists() else 0

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO invalid_files (file_path, file_size, reason)
                VALUES (?, ?, ?)
            ''', (str(file_path), file_size, reason))

    def is_registered_invalid(self, file_path: Path) -> bool:
        """Verifica se arquivo já foi marcado como inválido."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                'SELECT COUNT(*) FROM invalid_files WHERE file_path = ?',
                (str(file_path),)
            )
            count = cur.fetchone()[0]
            return count > 0

    def get_invalid_count(self) -> int:
        """Retorna total de arquivos inválidos."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute('SELECT COUNT(*) FROM invalid_files')
            return cur.fetchone()[0]

    def get_invalid_stats(self) -> dict:
        """Retorna estatísticas de arquivos inválidos."""
        with sqlite3.connect(self.db_path) as conn:
            # Total
            cur = conn.execute('SELECT COUNT(*) FROM invalid_files')
            total = cur.fetchone()[0]

            # Por motivo
            cur = conn.execute('''
                SELECT reason, COUNT(*) as count
                FROM invalid_files
                GROUP BY reason
                ORDER BY count DESC
            ''')
            reasons = dict(cur.fetchall())

            return {
                'total': total,
                'by_reason': reasons
            }
