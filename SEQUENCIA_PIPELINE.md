# 🔄 SEQUÊNCIA COMPLETA DOS PIPELINES

**Data:** 2026-02-08
**Status:** Pronto para começar (aguardando qwen2.5:32b)

---

## 📋 O QUE ESTÁ FEITO

### ✅ INFRAESTRUTURA
- [x] Estrutura de pastas organizada: `txt/[idioma]/`
- [x] Hunters atualizados (Gutenberg + Archive.org)
- [x] Detecção automática de idioma
- [x] **VALIDAÇÃO OBRIGATÓRIA (LEI 01)** ✨
- [x] Registro de arquivos inválidos (SQLite)
- [x] Sistema de cache (translation_cache.db, cache.db)
- [x] Template KDP (Estrutura.docx)

### ✅ SCRIPTS PRONTOS
- [x] `run_dual_hunter.py` - Download
- [x] `run_translator.py` - Tradução (COM VALIDAÇÃO)
- [x] `run_processor.py` - Pipeline 1
- [x] `src/validator.py` - **Validador (LEI 01)** ✨

### ❌ FALTANDO
- [ ] `run_processor_bilingual.py` - Pipeline 2
- [ ] `src/processor_bilingual.py` - Lógica Pipeline 2

---

## 🚀 SEQUÊNCIA DE EXECUÇÃO

### **ETAPA 0: PRÉ-REQUISITO**
```bash
# Aguardar modelo terminar
ollama list

# Deve aparecer:
# qwen2.5:32b
```

---

### **ETAPA 1: DOWNLOAD** (Opcional - já temos 3.466 livros)
```bash
# Baixar mais livros se quiser
python run_dual_hunter.py --languages en --limit 10
```

**O que faz:**
1. Busca livros no Gutenberg + Archive.org
2. Download do TXT
3. Detecta idioma automaticamente
4. **VALIDA se está completo (LEI 01)**
5. Se válido → salva em `txt/[idioma]/[Titulo]_[lang].txt`
6. Se inválido → descarta + registra em `invalid_files.db`

**Saída:**
- `txt/en/Book_en.txt`
- `txt/es/Book_es.txt`

---

### **ETAPA 2: TRADUÇÃO** (EN/ES/RU → PT)
```bash
# Traduzir 5 livros para testar
python run_translator.py --languages en --limit 5

# Ou traduzir todos
python run_translator.py --languages en es ru
```

**O que faz:**
1. Varre `txt/[idioma]/` procurando arquivos
2. **VALIDA cada arquivo (LEI 01):**
   - Tamanho mínimo: 5KB
   - Conteúdo mínimo: 500 caracteres
   - Verifica se não é lixo
3. Se **INVÁLIDO** → pula + registra em `invalid_files.db`
4. Se **VÁLIDO** → traduz:
   - Divide em chunks (2000 chars)
   - Traduz com Ollama (qwen2.5:32b)
   - Cache para evitar retradução
5. Salva em `translated/[Autor]/[Titulo]_pt.txt`

**Saída:**
- `translated/Autor/Book_pt.txt`

**Tempo estimado:**
- Arquivo pequeno (10KB): ~5-10 min
- Arquivo médio (50KB): ~20-30 min
- Arquivo grande (200KB): ~1-2 horas

---

### **ETAPA 3: PIPELINE 1** (Correção + Notas Explicativas)
```bash
# Processar arquivo específico
python run_processor.py --input translated/Autor/Book_pt.txt --author "Autor"

# Processar TODOS os traduzidos
python run_processor.py --batch
```

**O que faz:**
1. Lê `translated/Autor/Book_pt.txt`
2. **CORREÇÃO:**
   - Corrige gramática, ortografia
   - Corrige erros de OCR (rn→m, cl→d)
   - Mantém estrutura de parágrafos
3. **IDENTIFICAÇÃO DE NOTAS:**
   - IA identifica termos importantes:
     * Palavras estrangeiras (Übermensch, carpe diem)
     * Nomes próprios raros
     * Termos técnicos
     * Citações
   - Marca como: `[NOTA:termo|explicação]`
4. **EXTRAÇÃO:**
   - Converte `[NOTA:...]` em `[1]`, `[2]`
   - Cria lista de notas de rodapé
5. **GERA DOCX:**
   - Aplica template KDP
   - Texto corrigido
   - Notas ao final
   - Numeração de páginas

**Saída:**
- `docx/pipeline1/Autor/Book_pt.docx`

**Tempo estimado:**
- Arquivo pequeno: ~10-15 min
- Arquivo médio: ~30-45 min
- Arquivo grande: ~2-3 horas

---

### **ETAPA 4: PIPELINE 2** (Bilíngue + Semantic Priming) - **FALTANDO**
```bash
# AINDA NÃO EXISTE - PRECISA CRIAR
python run_processor_bilingual.py --input translated/Autor/Book_pt.txt

# Ou processar todos
python run_processor_bilingual.py --batch
```

**O que vai fazer:**
1. Lê `translated/Autor/Book_pt.txt`
2. **ANÁLISE TF-IDF:**
   - Identifica 100 palavras mais importantes
   - Remove stop words
   - Prioriza verbos, substantivos, adjetivos
3. **SEMANTIC CLUSTERING:**
   - Agrupa palavras relacionadas (king → kingdom → queen)
   - K-means (~10-15 clusters)
   - Prioriza palavras com priming semântico
4. **SUBSTITUIÇÃO:**
   - Substitui 100 palavras PT → EN no texto
   - Marca: `king[1]`, `decision[2]`
5. **GERA EXEMPLOS:**
   - 3 frases em inglês para cada palavra
   - Contextualizadas, simples, variadas
6. **GERA DOCX:**
   - Texto bilíngue
   - Notas com tradução + 3 exemplos

**Saída:**
- `docx/pipeline2/Autor/Book_pt_bilingual.docx`

**Tempo estimado:**
- TBD (ainda não implementado)

---

## 📊 RESUMO DA SEQUÊNCIA

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO COMPLETO                           │
└─────────────────────────────────────────────────────────────┘

1. DOWNLOAD (opcional)
   ↓
   txt/[idioma]/[Titulo]_[lang].txt
   ↓
2. TRADUÇÃO (EN/ES/RU → PT) ✅ COM VALIDAÇÃO (LEI 01)
   ↓
   translated/[Autor]/[Titulo]_pt.txt
   ↓
   ├─→ 3. PIPELINE 1 (Correção + Notas Explicativas)
   │   ↓
   │   docx/pipeline1/[Autor]/[Titulo]_pt.docx
   │   (100% PT + notas técnicas)
   │
   └─→ 4. PIPELINE 2 (Bilíngue + Semantic Priming) ❌ FALTANDO
       ↓
       docx/pipeline2/[Autor]/[Titulo]_pt_bilingual.docx
       (PT + 100 palavras EN + 3 exemplos cada)
```

---

## 🎯 PRÓXIMOS PASSOS

1. **Aguardar modelo qwen2.5:32b terminar**
2. **Testar tradução:**
   ```bash
   python run_translator.py --languages en --limit 1
   ```
3. **Testar Pipeline 1:**
   ```bash
   python run_processor.py --batch
   ```
4. **Criar Pipeline 2:**
   - `src/processor_bilingual.py`
   - `run_processor_bilingual.py`

---

## 🔒 LEI 01: VALIDAÇÃO OBRIGATÓRIA

**Regra:** Arquivo incompleto NÃO PODE ser traduzido.

**Validação:**
- ✅ Tamanho mínimo: 5KB (5000 bytes)
- ✅ Conteúdo mínimo: 500 caracteres
- ✅ Verifica se não é lixo (mínimo 50% ASCII)

**Se INVÁLIDO:**
- ❌ Não traduz
- 📝 Registra em `data/invalid_files.db`
- 🗑️ Pode ser deletado (opcional)

**Verificar inválidos:**
```bash
sqlite3 data/invalid_files.db "SELECT * FROM invalid_files"
```

---

## 📈 ESTIMATIVA DE TEMPO (50 livros médios)

| Etapa | Tempo |
|-------|-------|
| Download | 5-10 min |
| Tradução (50 livros) | ~7 dias |
| Pipeline 1 (50 livros) | ~25 horas |
| Pipeline 2 (50 livros) | ~30 horas (estimado) |
| **TOTAL** | ~9-10 dias |

**Hardware:** 32GB RAM, CPU 8+ cores

---

**Última atualização:** 2026-02-08 01:15
**Status:** Aguardando qwen2.5:32b
