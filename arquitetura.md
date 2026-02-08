# 🏗️ ARQUITETURA GOOGOLPLEX-BOOKS

**Sistema com 2 Pipelines Independentes para Processamento de Livros**

---

## 📐 VISÃO GERAL

```
FONTES → DOWNLOAD → VALIDAÇÃO → TRADUÇÃO → PIPELINE 1 (Completo PT)
                                          ↓
                                     PIPELINE 2 (Bilíngue PT+EN)
```

### Outputs Finais:
1. **Pipeline 1:** `docx/pipeline1/[Autor]/[Titulo]_pt.docx` - 100% português + notas explicativas
2. **Pipeline 2:** `docx/pipeline2/[Autor]/[Titulo]_pt_bilingual.docx` - PT + 100 palavras EN + exemplos

---

## 🔄 FLUXO COMPLETO - PIPELINE 1

### ETAPA 1: DOWNLOAD
**Script:** `run_dual_hunter.py` (usa `hunter.py` + `hunter2.py`)

```
FONTES:
├─ Project Gutenberg (70k livros)
└─ Archive.org (40M livros)

ENTRADA: Query por idioma (en, es, ru, fr, de, it)
SAÍDA: txt/[idioma]/[Titulo]_[lang].txt
```

**Processo:**
1. Busca livros por idioma na fonte
2. Download do arquivo TXT
3. **Detecção automática de idioma** (langdetect ou fallback)
4. **Adiciona sufixo:** `_en`, `_es`, `_pt`, `_ru`
5. Salva em `txt/[idioma]/[Titulo]_[lang].txt`

**Comando:**
```bash
python run_dual_hunter.py --languages en es --limit 50
```

---

### ETAPA 2: VALIDAÇÃO
**Script:** `run_dual_hunter.py` (validação integrada)

```
ENTRADA: txt/[idioma]/[Titulo]_[lang].txt
SAÍDA: Válido → continua | Inválido → deleta + registra SQLite
```

**Critérios de Validação:**
- Tamanho mínimo: **5KB** (configurável em `.env`)
- Encoding válido: UTF-8, Latin-1, CP1252
- Conteúdo mínimo: 500 caracteres

**Se Inválido:**
1. Arquivo é deletado de `txt/`
2. Registro salvo em `data/invalid_files.db`:
   - Path original
   - Tamanho (bytes)
   - Motivo da invalidação
   - Timestamp

**Comando para verificar inválidos:**
```bash
sqlite3 data/invalid_files.db "SELECT * FROM invalid_files ORDER BY timestamp DESC"
```

---

### ETAPA 3: TRADUÇÃO
**Script:** `run_translator.py`

```
ENTRADA: txt/[idioma]/[Titulo]_[lang].txt (EN, ES, RU)
SAÍDA: translated/[Autor]/[Titulo]_pt.txt
```

**Processo:**
1. Lê arquivo original em `txt/[idioma]/`
2. Divide em **chunks de 2000 caracteres**
3. Traduz para português usando **Ollama LOCAL**
   - Modelo: `qwen2.5:32b` (configurável)
   - Cache SQLite: `translation_cache.db`
   - Evita retradução de chunks já processados
4. Reconstrói texto completo traduzido
5. Salva em `translated/[Autor]/[Titulo]_pt.txt`

**Configuração (.env):**
```env
OLLAMA_MODEL=qwen2.5:32b
OLLAMA_BASE_URL=http://localhost:11434
MAX_CHUNK_TOKENS=2000
TEMPERATURE=0.2
```

**Comando:**
```bash
python run_translator.py --languages en es --limit 10
```

---

### ETAPA 4: CORREÇÃO + IDENTIFICAÇÃO DE NOTAS
**Script:** `run_processor.py` (usa `src/processor.py`)

```
ENTRADA: translated/[Autor]/[Titulo]_pt.txt
SAÍDA: docx/pipeline1/[Autor]/[Titulo]_pt.docx
```

**Processo:**

#### 4.1 CORREÇÃO DE TEXTO
- Corrige gramática e ortografia
- Corrige erros de OCR comuns:
  - `rn` → `m`
  - `cl` → `d`
  - `l` → `i`
  - Espaços incorretos
- Mantém estrutura de parágrafos
- Cache: `cache.db`

#### 4.2 IDENTIFICAÇÃO DE TERMOS IMPORTANTES
**IA identifica automaticamente:**
- ✅ Palavras estrangeiras (Übermensch, carpe diem, etc.)
- ✅ Nomes próprios pouco conhecidos
- ✅ Termos técnicos complexos
- ✅ Citações e referências

**Formato de marcação:**
```
[NOTA:termo|explicação breve]
```

**Exemplo:**
```
Texto: "o conceito de Übermensch mudou a filosofia"
       ↓
Marcado: "o conceito de [NOTA:Übermensch|Super-homem, conceito de Nietzsche sobre o homem ideal] mudou a filosofia"
```

#### 4.3 EXTRAÇÃO DE NOTAS
- Extrai marcadores `[NOTA:...|...]`
- Gera referências `[1]`, `[2]`, etc.
- Cria lista de notas de rodapé

#### 4.4 GERAÇÃO DOCX
- Aplica template KDP (`Estrutura.docx`)
- Formata parágrafos (justificado, espaçamento)
- Detecta capítulos (maiúsculas, centralizado)
- Adiciona notas de rodapé ao final
- Numeração de páginas

**Comando:**
```bash
# Arquivo específico
python run_processor.py --input translated/Autor/Livro_pt.txt --author "Nome Autor"

# Batch (todos arquivos em translated/)
python run_processor.py --batch
```

---

## 🔄 FLUXO COMPLETO - PIPELINE 2

### OBJETIVO
Gerar versão **bilíngue** para **aprendizado de inglês** usando **semantic priming**.

```
ENTRADA: translated/[Autor]/[Titulo]_pt.txt
SAÍDA: docx/pipeline2/[Autor]/[Titulo]_pt_bilingual.docx
```

---

### ETAPA 1: ANÁLISE DE FREQUÊNCIA
**Script:** `processor_bilingual.py` (a ser criado)

**Processo:**
1. Lê texto traduzido em português
2. Tokenização (palavras)
3. Remove stop words (artigos, preposições, conjunções)
4. Aplica **TF-IDF** (Term Frequency-Inverse Document Frequency)
5. Identifica palavras mais relevantes:
   - Verbos importantes
   - Substantivos-chave
   - Adjetivos significativos

**Exemplo de stop words removidas:**
```
PT: o, a, de, e, que, do, da, em, um, para, é, com, não, por, mais...
```

---

### ETAPA 2: SEMANTIC CLUSTERING
**Objetivo:** Agrupar palavras semanticamente relacionadas.

**Técnica:**
1. **Word Embeddings:** Usa modelo pré-treinado
   - Opção 1: Word2Vec
   - Opção 2: BERT/sentence-transformers
   - Opção 3: spaCy
2. **Cálculo de similaridade:** Cosine similarity entre vetores
3. **Clustering:** K-means (~10-15 clusters)

**Exemplo de Cluster Semântico:**
```
CLUSTER "REALEZA":
├─ king (rei)
├─ kingdom (reino)
├─ queen (rainha)
├─ throne (trono)
├─ crown (coroa)
└─ palace (palácio)
```

**Priorização:**
- Palavras em clusters densos (alta co-ocorrência)
- Palavras centrais (mais conexões semânticas)
- Alta frequência no texto

---

### ETAPA 3: SELEÇÃO DE 100 PALAVRAS
**Critérios:**
1. Alta relevância (TF-IDF score)
2. **Prioridade para palavras com priming semântico**
3. Exclusão de:
   - Stop words
   - Palavras muito simples (1-2 letras)
   - Números isolados
4. Balanceamento:
   - ~40-50% substantivos
   - ~30-40% verbos
   - ~10-20% adjetivos
   - ~5-10% advérbios

**Seleção com Semantic Priming:**
```
Exemplo: Se "king" está na lista:
  → Aumenta score de: kingdom, queen, throne, royal
  → Se alguma dessas já tem TF-IDF alto → entra na lista
```

---

### ETAPA 4: TRADUÇÃO DAS 100 PALAVRAS
**Processo:**
1. Pega as 100 palavras selecionadas (em PT)
2. Traduz para inglês (dicionário ou API)
3. Cria mapeamento: `{palavra_pt: palavra_en}`

**Exemplo:**
```python
{
  "rei": "king",
  "reino": "kingdom",
  "rainha": "queen",
  "decisão": "decision",
  "importante": "important"
}
```

---

### ETAPA 5: SUBSTITUIÇÃO NO TEXTO
**Processo:**
1. Varre texto em português
2. Substitui as 100 palavras selecionadas por suas versões em inglês
3. Adiciona marcador de nota: `[1]`, `[2]`, etc.

**IMPORTANTE - Preservação de Contexto:**
- Mantém conjugações e concordâncias em português
- Só substitui a palavra-raiz
- Não quebra estrutura de frases

**Exemplo de Substituição:**
```
ANTES:
"O rei vivia em seu grande reino com a rainha"

DEPOIS:
"O king[1] vivia em seu grande kingdom[2] com a queen[3]"
```

---

### ETAPA 6: GERAÇÃO DE 3 FRASES EXEMPLO
**Para cada uma das 100 palavras:**

**Processo:**
1. Gera 3 frases em **inglês** usando a palavra
2. Frases devem ser:
   - Simples e claras
   - Contextualizadas (não genéricas)
   - Variadas (diferentes contextos)
   - 8-15 palavras cada

**Exemplo para "king":**
```
[1] king (PT: rei)
    • The king ruled for 40 years.
    • He became king at age 21.
    • A wise king makes good decisions.
```

**Geração via IA:**
- Prompt ao Ollama: "Generate 3 simple English example sentences using the word 'king'"
- Validação: tamanho, clareza, variação

---

### ETAPA 7: GERAÇÃO DOCX BILÍNGUE
**Formato Final:**

```
TEXTO BILÍNGUE:
"O king[1] tomou uma importante decision[2] sobre o futuro do kingdom[3].
A queen[4] apoiou a escolha do king[1]."

NOTAS DE RODAPÉ:

[1] king (PT: rei)
    • The king ruled for 40 years.
    • He became king at age 21.
    • A wise king makes good decisions.

[2] decision (PT: decisão)
    • That was a difficult decision.
    • We need to make a decision soon.
    • Her decision changed everything.

[3] kingdom (PT: reino)
    • The kingdom was very large.
    • He inherited the kingdom from his father.
    • A prosperous kingdom needs good governance.

[4] queen (PT: rainha)
    • The queen addressed her people.
    • She became queen in 1952.
    • The queen and king ruled together.
```

**Formatação:**
- Template KDP (`Estrutura.docx`)
- Texto bilíngue justificado
- Referências sobrescritas `[N]`
- Seção de notas ao final
- Numeração de páginas

**Comando:**
```bash
# Arquivo específico
python run_processor_bilingual.py --input docx/pipeline1/Autor/Livro_pt.docx

# Batch (todos DOCX do Pipeline 1)
python run_processor_bilingual.py --batch
```

---

## 📊 COMPARAÇÃO DOS PIPELINES

| **Aspecto** | **Pipeline 1** | **Pipeline 2** |
|-------------|----------------|----------------|
| **Entrada** | `translated/[Autor]/[Titulo]_pt.txt` | `translated/[Autor]/[Titulo]_pt.txt` |
| **Idioma do texto** | 100% Português | PT + 100 palavras EN |
| **Notas de rodapé** | Termos técnicos explicados | 100 palavras EN + 3 frases exemplo |
| **Objetivo** | Leitura fluida em PT | Aprendizado de inglês |
| **Público-alvo** | Leitores gerais | Estudantes de inglês |
| **Técnica especial** | Identificação automática de termos | **Semantic Priming** |
| **Arquivo de saída** | `[Titulo]_pt.docx` | `[Titulo]_pt_bilingual.docx` |
| **Pasta de saída** | `docx/pipeline1/[Autor]/` | `docx/pipeline2/[Autor]/` |
| **Template** | `Estrutura.docx` | `Estrutura.docx` |

---

## 🎯 SEMANTIC PRIMING - DETALHES

### O que é?
Técnica de aprendizado onde palavras **semanticamente relacionadas** são agrupadas para facilitar memorização.

### Exemplo Prático:
```
Cluster ANIMAIS:
"O gato[1] viu o cachorro[2] e subiu na árvore"

Notas:
[1] cat (PT: gato)
    • The cat is sleeping.
    • I have a black cat.
    • Cats love to climb trees.

[2] dog (PT: cachorro)
    • The dog barks loudly.
    • My dog is very friendly.
    • Dogs are loyal animals.
```

### Por que funciona?
- **Ativação cruzada:** Aprender "king" ativa neurônios de "kingdom", "queen"
- **Contexto compartilhado:** Palavras aparecem próximas no texto
- **Reforço mútuo:** Revisar uma palavra reforça palavras relacionadas

---

## 📂 ESTRUTURA DE ARQUIVOS

```
Googolplex-Books/
├── txt/                                    # Livros originais
│   ├── en/                                 # 1.722 livros inglês
│   │   └── [Titulo]_en.txt
│   ├── es/                                 # 214 livros espanhol
│   │   └── [Titulo]_es.txt
│   ├── pt/                                 # 236 livros português
│   │   └── [Titulo]_pt.txt
│   ├── ru/                                 # 1.294 livros russo
│   │   └── [Titulo]_ru.txt
│   └── unknown/                            # 12 livros (idioma não detectado)
│
├── translated/[Autor]/                     # Livros traduzidos
│   └── [Titulo]_pt.txt                     # Português (sem correção)
│
├── docx/
│   ├── pipeline1/[Autor]/                  # DOCX Pipeline 1
│   │   └── [Titulo]_pt.docx                # PT completo + notas explicativas
│   │
│   └── pipeline2/[Autor]/                  # DOCX Pipeline 2
│       └── [Titulo]_pt_bilingual.docx      # PT + 100 palavras EN + exemplos
│
├── data/
│   ├── books.db                            # Registro de livros
│   ├── translation_cache.db                # Cache de traduções
│   ├── cache.db                            # Cache de correções
│   └── invalid_files.db                    # Arquivos inválidos
│
├── logs/                                   # Logs de execução
│
├── src/                                    # Código fonte
│   ├── hunter.py                           # Download Gutenberg
│   ├── hunter2.py                          # Download Archive.org
│   ├── processor.py                        # Pipeline 1
│   ├── processor_bilingual.py              # Pipeline 2 (A CRIAR)
│   └── database.py                         # Gerenciamento SQLite
│
├── config/
│   └── settings.py                         # Configurações centralizadas
│
├── run_daemon.py                           # Daemon 24/7 (orquestra tudo)
├── run_dual_hunter.py                      # Download + validação
├── run_translator.py                       # Tradução EN/ES/RU → PT
├── run_processor.py                        # Pipeline 1
├── run_processor_bilingual.py              # Pipeline 2 (A CRIAR)
│
├── Estrutura.docx                          # Template KDP
└── .env                                    # Configurações
```

---

## ⚙️ CONFIGURAÇÃO (.env)

```env
# ============================================================================
# OLLAMA (IA LOCAL)
# ============================================================================
MODEL_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b

# ============================================================================
# PROCESSAMENTO
# ============================================================================
MAX_CHUNK_TOKENS=2000          # Tamanho de chunk para tradução
MAX_OUTPUT_TOKENS=8192         # Máximo de tokens na resposta
TEMPERATURE=0.2                # Criatividade (0.0-1.0)
PARALLEL_CHUNKS=4              # Chunks processados em paralelo

# ============================================================================
# VALIDAÇÃO
# ============================================================================
MIN_FILE_SIZE=5000             # Tamanho mínimo em bytes (5KB)

# ============================================================================
# SEMANTIC CLUSTERING (Pipeline 2)
# ============================================================================
NUM_KEYWORDS=100               # Número de palavras-chave
NUM_CLUSTERS=12                # Número de clusters semânticos
NUM_EXAMPLES=3                 # Frases exemplo por palavra
```

---

## 🚀 COMANDOS DE EXECUÇÃO

### 1. Download + Validação
```bash
# Baixar 50 livros em EN e ES de ambas as fontes
python run_dual_hunter.py --languages en es --limit 50

# Apenas Gutenberg
python run_dual_hunter.py --languages en --limit 100 --skip-archive

# Apenas Archive.org
python run_dual_hunter.py --languages en --limit 100 --skip-gutenberg
```

### 2. Tradução
```bash
# Traduzir livros em EN e ES para PT
python run_translator.py --languages en es --limit 10

# Traduzir TODOS os livros não traduzidos
python run_translator.py --languages en es ru
```

### 3. Pipeline 1 (Tradução Completa)
```bash
# Processar arquivo específico
python run_processor.py --input translated/Autor/Livro_pt.txt --author "Nome"

# Processar todos arquivos em translated/
python run_processor.py --batch
```

### 4. Pipeline 2 (Bilíngue + Semantic Priming)
```bash
# Processar arquivo específico
python run_processor_bilingual.py --input translated/Autor/Livro_pt.txt

# Processar todos DOCX do Pipeline 1
python run_processor_bilingual.py --batch
```

### 5. Daemon Completo (24/7)
```bash
# Executa tudo automaticamente
python run_daemon.py --languages en es --batch-size 50
```

---

## 📈 PERFORMANCE ESTIMADA

| **Etapa** | **Velocidade** | **Tempo para 50 livros** |
|-----------|----------------|--------------------------|
| Download | ~100 livros/10min | 5 minutos |
| Tradução | ~6-8 livros/dia | ~7 dias |
| Pipeline 1 | ~10-15 DOCX/hora | 3-5 horas |
| Pipeline 2 | ~8-12 DOCX/hora | 4-6 horas |
| **TOTAL** | - | **~8-9 dias** |

**Hardware recomendado:**
- CPU: 8+ cores
- RAM: 32GB+
- GPU: Não necessária (Ollama usa CPU)
- Disco: 50GB+ livre

---

## 🔍 VALIDAÇÃO E QUALIDADE

### Validação de Arquivos
```bash
# Ver arquivos inválidos
sqlite3 data/invalid_files.db "SELECT * FROM invalid_files ORDER BY timestamp DESC LIMIT 10"

# Estatísticas
sqlite3 data/invalid_files.db "SELECT COUNT(*) FROM invalid_files"
```

### Cache
```bash
# Ver traduções em cache
sqlite3 data/translation_cache.db "SELECT COUNT(*) FROM translations"

# Ver correções em cache
sqlite3 data/cache.db "SELECT COUNT(*) FROM corrections"
```

### Logs
```bash
# Ver logs em tempo real
tail -f logs/daemon_20260207.log

# Buscar erros
grep ERROR logs/*.log
```

---

## 📝 PRÓXIMOS PASSOS

- [x] 1. Organizar todos TXT com sufixo de idioma
- [x] 2. Organizar TXT em subpastas por idioma (txt/en/, txt/es/, etc.)
- [x] 3. Implementar validação de arquivos + SQLite
- [ ] 4. Criar `processor_bilingual.py` (Pipeline 2)
- [ ] 5. Implementar análise TF-IDF para palavras-chave
- [ ] 6. Implementar semantic clustering (Word2Vec/BERT)
- [ ] 7. Implementar geração de 3 frases exemplo
- [ ] 8. Testar Pipeline 2 com livros pequenos
- [ ] 9. Otimizar para processamento em lote
- [ ] 10. Aguardar download modelo `qwen2.5:32b`

---

**Última atualização:** 2026-02-07
**Versão:** 4.0 (2 Pipelines + Semantic Priming)
**Status:** Aguardando modelo Ollama
