#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRANSLATOR_NPU.PY - Tradutor usando ONNX Runtime + DirectML (NPU)
==================================================================
Substitui Ollama por ONNX Runtime com DirectML para usar NPU.

Modelo: Qwen2.5-32B-Instruct (ONNX otimizado para NPU)
"""

import os
from pathlib import Path
from typing import Optional
from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer
import logging

logger = logging.getLogger(__name__)

class NPUTranslator:
    """Tradutor usando NPU via ONNX Runtime + DirectML."""

    def __init__(self, model_path: str):
        """
        Args:
            model_path: Caminho para o modelo ONNX
        """
        self.model_path = model_path
        logger.info(f"Carregando modelo ONNX de: {model_path}")

        # Carregar modelo ONNX com DirectML (NPU)
        self.model = ORTModelForCausalLM.from_pretrained(
            model_path,
            provider="DmlExecutionProvider",  # DirectML = NPU
            use_cache=True,
        )

        # Carregar tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        logger.info("Modelo carregado NA NPU com DirectML!")

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "pt") -> str:
        """
        Traduz texto usando NPU.

        Args:
            text: Texto para traduzir
            source_lang: Idioma de origem (en, es, ru, etc.)
            target_lang: Idioma de destino (pt)

        Returns:
            Texto traduzido
        """
        # Criar prompt de tradução
        lang_names = {
            'en': 'English',
            'es': 'Spanish',
            'ru': 'Russian',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese'
        }

        source = lang_names.get(source_lang, source_lang)
        target = lang_names.get(target_lang, target_lang)

        prompt = f"""<|im_start|>system
You are a professional translator. Translate the following text from {source} to {target}.
Only output the translation, nothing else.<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""

        # Tokenizar
        inputs = self.tokenizer(prompt, return_tensors="pt")

        # Gerar tradução NA NPU
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=2048,
            temperature=0.3,
            do_sample=True,
            top_p=0.9,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        # Decodificar
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extrair apenas a tradução (remover prompt)
        if "<|im_start|>assistant" in result:
            result = result.split("<|im_start|>assistant")[-1].strip()

        return result

# Instância global
_translator = None

def get_translator(model_path: Optional[str] = None) -> NPUTranslator:
    """Retorna instância singleton do tradutor."""
    global _translator

    if _translator is None:
        if model_path is None:
            model_path = "d:/modelos/qwen2.5-32b-instruct-onnx"

        _translator = NPUTranslator(model_path)

    return _translator

def translate_chunk(text: str, source_lang: str = "en") -> str:
    """
    Função helper para traduzir um chunk de texto.
    Compatível com a API antiga do Ollama.
    """
    translator = get_translator()
    return translator.translate(text, source_lang=source_lang, target_lang="pt")
