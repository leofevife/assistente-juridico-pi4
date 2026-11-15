import json
import os
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

Modelo = TypeVar("Modelo", bound=BaseModel)


def salvar_json(caminho: Path, conteudo: BaseModel | list[BaseModel]) -> None:
    itens = [item.model_dump(mode="json") for item in conteudo] if isinstance(conteudo, list) else conteudo.model_dump(mode="json")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    # Escrita atômica: uma interrupção no meio da avaliação não corrompe o checkpoint
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporario, caminho)


def carregar_lista(caminho: Path, modelo: type[Modelo]) -> list[Modelo]:
    if not caminho.exists():
        return []
    return [modelo.model_validate(item) for item in json.loads(caminho.read_text(encoding="utf-8"))]


def carregar_objeto(caminho: Path, modelo: type[Modelo]) -> Modelo:
    return modelo.model_validate(json.loads(caminho.read_text(encoding="utf-8")))
