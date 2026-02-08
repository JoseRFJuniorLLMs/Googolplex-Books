# 📚 GOOGOLPLEX-BOOKS - Documentação Completa

**Sistema automatizado de download, tradução e formatação de livros para Amazon KDP**

---

## 🎯 VISÃO GERAL

Sistema com **2 pipelines** independentes que produzem **2 tipos de DOCX**:

1. **Pipeline 1:** Tradução completa em português + notas de rodapé explicativas
2. **Pipeline 2:** Versão bilíngue (PT + 100 palavras-chave em inglês) + exemplos

---

## 📊 PIPELINE 1: Tradução Completa

### Fluxo:

```
1. DOWNLOAD → txt/
   • Gutenberg (70k livros)
   • Archive.org (40M livros)
   • Identifica idioma automaticamente
   • Salva como: [Titulo]_[lang].txt (ex: Book_en.txt)

2. VALIDAÇÃO
   • Verifica arquivo completo (tamanho mínimo)
   • Se incompleto → deleta + registra no SQLite

3. TRADUÇÃO → translated/[Autor]/[Titulo]_pt.txt
   • Modelo: Ollama (qwen2.5:32b)
   • Divide em chunks (2000 chars)
   • Traduz para português
   • Cache SQLite (evita retradução)

4. CORREÇÃO + NOTAS → docx/pipeline1/[Autor]/[Titulo]_pt.docx
   • Corrige gramática e OCR
   • IA identifica termos importantes:
     - Palavras estrangeiras
     - Nomes próprios
     - Termos técnicos
     - Citações
   • Adiciona notas de rodapé explicativas
   • Aplica template KDP (Estrutura.docx)
```

### Exemplo de Nota de Rodapé (Pipeline 1):
```
Texto: "o conceito de Übermensch mudou a filosofia"
           ↓
Nota: [1] Übermensch - Super-homem, conceito de Nietzsche sobre o homem ideal.
```

---

## 📊 PIPELINE 2: Versão Bilíngue (NOVO)

### Fluxo:

```
1. ENTRADA
   • Pega DOCX do Pipeline 1
   • Lê texto traduzido em português

2. ANÁLISE DE FREQUÊNCIA
   • Identifica 100 palavras mais frequentes:
     - Verbos importantes
     - Substantivos-chave
     - Adjetivos relevantes
     - Exclui: artigos, preposições, conjunções

3. SUBSTITUIÇÃO INTELIGENTE
   • Mantém as 100 palavras em INGLÊS
   • Adiciona nota de rodapé para cada uma:
     - Tradução PT
     - 3 frases exemplo em inglês

4. GERAÇÃO DOCX → docx/pipeline2/[Autor]/[Titulo]_pt_bilingual.docx
   • Aplica template KDP
   • Salva versão bilíngue
```

### Exemplo de Nota de Rodapé (Pipeline 2):
```
Texto: "The king tomou uma importante decision sobre o futuro"
              ↑                              ↑
             [1]                            [2]

Notas:
[1] king (PT: rei)
    • The king ruled for 40 years.
    • He became king at age 21.
    • A wise king makes good decisions.

[2] decision (PT: decisão)
    • That was a difficult decision.
    • We need to make a decision soon.
    • Her decision changed everything.
```

---

## 📂 ESTRUTURA DO PROJETO

```
Googolplex-Books/
├── txt/                              # Livros originais (com sufixo de idioma)
│   ├── [Titulo]_en.txt              # Inglês
│   ├── [Titulo]_es.txt              # Espanhol
│   ├── [Titulo]_pt.txt              # Português
│   └── [Titulo]_ru.txt              # Russo
│
├── translated/[Autor]/               # Livros traduzidos
│   └── [Titulo]_pt.txt              # Português (sem correção)
│
├── docx/
│   ├── pipeline1/[Autor]/           # DOCX Pipeline 1
│   │   └── [Titulo]_pt.docx         # Português completo + notas explicativas
│   │
│   └── pipeline2/[Autor]/           # DOCX Pipeline 2
│       └── [Titulo]_pt_bilingual.docx  # PT + 100 palavras EN + exemplos
│
├── data/
│   ├── books.db                     # Registro de livros
│   ├── translation_cache.db         # Cache de traduções
│   ├── cache.db                     # Cache de correções
│   └── invalid_files.db             # Arquivos inválidos
│
├── logs/                            # Logs de execução
│
├── src/                             # Código fonte
│   ├── hunter.py                    # Download Gutenberg
│   ├── hunter2.py                   # Download Archive.org
│   ├── processor.py                 # Pipeline 1 (tradução + notas)
│   ├── processor_bilingual.py       # Pipeline 2 (bilíngue + exemplos) [NOVO]
│   └── database.py                  # Gerenciamento SQLite
│
├── config/
│   └── settings.py                  # Configurações centralizadas
│
└── Estrutura.docx                   # Template KDP
```

---

## 🚀 EXECUÇÃO

### Daemon Completo (24/7)
```bash
python run_daemon.py --languages en es --batch-size 50
```

### Executar Pipelines Individualmente

#### Pipeline 1 (Tradução Completa)
```bash
# Download
python run_dual_hunter.py --languages en es --limit 50

# Tradução
python run_translator.py --languages en es

# Processamento (correção + notas)
python run_processor.py --batch
```

#### Pipeline 2 (Bilíngue)
```bash
# Processa todos DOCX do Pipeline 1
python run_processor_bilingual.py --batch

# Ou arquivo específico
python run_processor_bilingual.py --input "docx/pipeline1/Autor/Livro_pt.docx"
```

---

## ⚙️ CONFIGURAÇÃO

### .env
```env
# Modelo de IA
MODEL_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b

# Processamento
MAX_CHUNK_TOKENS=2000
MAX_OUTPUT_TOKENS=8192
TEMPERATURE=0.2
PARALLEL_CHUNKS=4

# Validação de arquivos
MIN_FILE_SIZE=5000          # Tamanho mínimo em bytes
```

---

## 📈 VALIDAÇÃO DE ARQUIVOS

### Critérios:
- **Tamanho mínimo:** 5KB (configurável)
- **Encoding válido:** UTF-8, Latin-1, CP1252
- **Conteúdo mínimo:** 500 caracteres de texto

### Ação se inválido:
1. Arquivo é deletado
2. Registro salvo em `data/invalid_files.db`:
   - Path original
   - Tamanho
   - Motivo da invalidação
   - Timestamp

---

## 🎨 NOTAS DE RODAPÉ

### Pipeline 1 - Notas Explicativas
**IA identifica:**
- Termos em idioma estrangeiro
- Nomes próprios pouco conhecidos
- Termos técnicos
- Citações e referências

**Formato:** Explicação breve (máx 20 palavras)

### Pipeline 2 - Palavras-Chave + Exemplos
**Processo:**
1. Análise de frequência (TF-IDF ou similar)
2. Seleção de 100 palavras mais relevantes
3. Exclusão de stop words
4. Manutenção em inglês no texto
5. 3 frases exemplo para cada

**Formato:** Tradução + 3 exemplos contextualizados

---

## 📊 ESTATÍSTICAS

### Biblioteca Atual:
- **3.478 livros** originais
- **1.722 em inglês** (49.5%)
- **1.294 em russo** (37.2%)
- **236 em português** (6.8%)
- **214 em espanhol** (6.2%)

### Performance Estimada:
- **Download:** ~100 livros/ciclo (10 min)
- **Tradução:** ~6-8 livros/dia
- **Processamento:** ~10-15 DOCX/hora
- **Pipeline completo:** ~24h para 50 livros

---

## 🔧 COMANDOS ÚTEIS

### Ver estatísticas
```bash
python -c "import json; print(json.dumps(json.load(open('data/daemon_stats.json')), indent=2))"
```

### Limpar cache
```bash
rm data/translation_cache.db data/cache.db
```

### Ver logs
```bash
tail -f logs/daemon_$(date +%Y%m%d).log
```

### Verificar arquivos inválidos
```bash
sqlite3 data/invalid_files.db "SELECT * FROM invalid_files ORDER BY timestamp DESC LIMIT 10"
```

---

## 📝 DIFERENÇAS ENTRE PIPELINES

| Aspecto | Pipeline 1 | Pipeline 2 |
|---------|-----------|-----------|
| **Idioma** | 100% Português | PT + 100 palavras EN |
| **Notas** | Termos técnicos | Palavras-chave + exemplos |
| **Objetivo** | Leitura fluida | Aprendizado de inglês |
| **Público** | Leitores gerais | Estudantes de inglês |
| **Arquivo** | `_pt.docx` | `_pt_bilingual.docx` |
| **Pasta** | `docx/pipeline1/` | `docx/pipeline2/` |

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ Organizar todos TXT com sufixo de idioma
2. ✅ Implementar validação de arquivos
3. ⏳ Criar `processor_bilingual.py` (Pipeline 2)
4. ⏳ Adicionar análise TF-IDF para palavras-chave
5. ⏳ Implementar geração de 3 frases exemplo
6. ⏳ Testar Pipeline 2 com livros pequenos
7. ⏳ Otimizar para processamento em lote

---

## 📞 INFORMAÇÕES TÉCNICAS

### Requisitos:
- Python 3.10+
- Ollama com modelo qwen2.5:32b
- 32GB RAM (recomendado)
- 50GB espaço livre em disco

### Dependências principais:
- `python-docx` - Geração de DOCX
- `requests` - HTTP requests
- `langdetect` - Detecção de idioma
- `sqlite3` - Cache e registros

---

**Última atualização:** 2026-02-08
**Versão:** 3.0 (2 Pipelines)
