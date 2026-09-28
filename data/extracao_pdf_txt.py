from pathlib import Path
import pdfplumber
import re

diretorio_atual = Path(__file__).resolve().parent

# nao sei onde vou fazer o deploy! aí com o pathlib consigo pegar o caminho do arquivo atual e montar o caminho do pdf e do txt de saída
caminho_pdf = (
    diretorio_atual
    / "resources"
    / "CDC.pdf"
)
caminho_saida = diretorio_atual / "resources" / "cdc_limpo.txt"

texto_completo = ""

with pdfplumber.open(caminho_pdf) as pdf:
  for pagina in pdf.pages:
    texto_pagina = pagina.extract_text()

    if texto_pagina:
      texto_completo += texto_pagina + "\n"

# 1. Remove números de página isolados em uma linha
texto_completo = re.sub(r"^\d+$\n", "", texto_completo, flags=re.MULTILINE)

# 2. Arruma quebras de linha no meio das frases.
# Se a linha termina com uma letra minúscula ou vírgula e a próxima
# começa com letra minúscula, junta as duas.
texto_completo = re.sub(
    r"([a-záéíóúãõç,])\n([a-záéíóúãõç])", r"\1 \2", texto_completo
)

caminho_saida.write_text(texto_completo, encoding="utf-8")