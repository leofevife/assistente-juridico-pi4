import asyncio

from backend.core.rate_limit import LimitadorRequisicoes


def test_permite_ate_o_limite_e_depois_bloqueia():
    limitador = LimitadorRequisicoes(max_requisicoes=2, janela_segundos=60)

    async def cenario():
        return [await limitador.permitir("1.1.1.1") for _ in range(3)]

    resultados = asyncio.run(cenario())

    assert resultados[0] == (True, 0)
    assert resultados[1] == (True, 0)
    permitido, tentar_em = resultados[2]
    assert permitido is False
    assert 1 <= tentar_em <= 60


def test_clientes_sao_contabilizados_separadamente():
    limitador = LimitadorRequisicoes(max_requisicoes=1, janela_segundos=60)

    async def cenario():
        return await limitador.permitir("a"), await limitador.permitir("b")

    (permitido_a, _), (permitido_b, _) = asyncio.run(cenario())
    assert permitido_a and permitido_b


def test_libera_apos_a_janela(monkeypatch):
    relogio = [1000.0]
    monkeypatch.setattr("backend.core.rate_limit.time.monotonic", lambda: relogio[0])
    limitador = LimitadorRequisicoes(max_requisicoes=1, janela_segundos=10)

    async def cenario():
        primeiro = await limitador.permitir("ip")
        bloqueado = await limitador.permitir("ip")
        relogio[0] += 11
        liberado = await limitador.permitir("ip")
        return primeiro, bloqueado, liberado

    primeiro, bloqueado, liberado = asyncio.run(cenario())
    assert primeiro[0] is True
    assert bloqueado[0] is False
    assert liberado[0] is True

