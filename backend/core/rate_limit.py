import asyncio
import time
from collections import defaultdict, deque


class LimitadorRequisicoes:
    # Janela deslizante em memória: atende uma única instância da API.
    # Para escalar horizontalmente, trocar o armazenamento por um backend compartilhado (ex: Redis).
    def __init__(self, max_requisicoes: int, janela_segundos: int):
        self.max_requisicoes = max_requisicoes
        self.janela_segundos = janela_segundos
        self._historico: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def permitir(self, chave: str) -> tuple[bool, int]:
        agora = time.monotonic()
        limite_inferior = agora - self.janela_segundos

        async with self._lock:
            registros = self._historico[chave]
            while registros and registros[0] <= limite_inferior:
                registros.popleft()

            if len(registros) >= self.max_requisicoes:
                tentar_novamente = int(registros[0] + self.janela_segundos - agora) + 1
                return False, max(tentar_novamente, 1)

            registros.append(agora)

            # Evita crescimento indefinido do dicionário com IPs que não voltaram mais
            if len(self._historico) > 10_000:
                self._limpar_expirados(limite_inferior)

            return True, 0

    def _limpar_expirados(self, limite_inferior: float) -> None:
        expirados = [
            chave for chave, registros in self._historico.items()
            if not registros or registros[-1] <= limite_inferior
        ]
        for chave in expirados:
            del self._historico[chave]

