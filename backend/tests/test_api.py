import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.main import create_app
from backend.services.rag_service import AssistenteJuridicoService
from backend.tests.fakes import RepositorioFalso, criar_settings, documento_artigo

URL_CHAT = "/api/v1/chat"
PERGUNTA_VALIDA = {"pergunta": "Qual o prazo para desistir de uma compra feita pela internet?"}


class ServicoComFalha:
    async def responder_com_fontes(self, pergunta: str):
        raise RuntimeError("chave-secreta-interna vazou")


def _montar_cliente(settings=None, servico=None, repositorio=None) -> TestClient:
    app = create_app(settings=settings or criar_settings(), inicializar_servicos=False)
    app.state.servico = servico
    app.state.repositorio = repositorio
    return TestClient(app)


@pytest.fixture
def repositorio():
    return RepositorioFalso([documento_artigo("49", "O consumidor pode desistir do contrato, no prazo de 7 dias.")])


@pytest.fixture
def cliente(settings, repositorio):
    servico = AssistenteJuridicoService(
        repositorio, settings=settings, llm=FakeListChatModel(responses=["Segundo o Art. 49, são 7 dias."])
    )
    with _montar_cliente(settings, servico, repositorio) as cliente:
        yield cliente


def test_health_retorna_ok_e_cabecalhos_de_seguranca(cliente):
    resposta = cliente.get("/api/v1/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"


def test_ready_quando_servico_e_banco_disponiveis(cliente):
    resposta = cliente.get("/api/v1/ready")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "pronto", "banco_vetorial": True}


def test_ready_indisponivel_quando_banco_falha():
    repositorio = RepositorioFalso(conectado=ConnectionError("offline"))
    with _montar_cliente(servico=object(), repositorio=repositorio) as cliente:
        resposta = cliente.get("/api/v1/ready")
    assert resposta.status_code == 503
    assert resposta.json()["banco_vetorial"] is False


def test_chat_retorna_resposta_e_fontes(cliente):
    resposta = cliente.post(URL_CHAT, json=PERGUNTA_VALIDA)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["resposta"] == "Segundo o Art. 49, são 7 dias."
    assert corpo["fontes"][0]["artigo"] == "49"
    assert corpo["fontes"][0]["lei"] == "Lei 8.078/1990 (CDC)"
    assert "Art. 49" in corpo["fontes"][0]["trecho"]


def test_chat_normaliza_espacos_da_pergunta(cliente, repositorio):
    cliente.post(URL_CHAT, json={"pergunta": "  prazo   de   devolução  "})
    assert repositorio.retriever.consultas[-1] == "prazo de devolução"


@pytest.mark.parametrize("corpo", [
    {},
    {"pergunta": ""},
    {"pergunta": "   oi   "},
    {"pergunta": "x" * 1001},
    {"pergunta": 123},
    {"pergunta": "Pergunta válida?", "campo_extra": "nao permitido"},
])
def test_chat_rejeita_payload_invalido(cliente, corpo):
    resposta = cliente.post(URL_CHAT, json=corpo)
    assert resposta.status_code == 422


def test_chat_indisponivel_sem_servico():
    with _montar_cliente(servico=None) as cliente:
        resposta = cliente.post(URL_CHAT, json=PERGUNTA_VALIDA)
    assert resposta.status_code == 503


def test_chat_nao_expoe_detalhes_internos_em_falha():
    with _montar_cliente(servico=ServicoComFalha()) as cliente:
        resposta = cliente.post(URL_CHAT, json=PERGUNTA_VALIDA)

    assert resposta.status_code == 503
    assert "chave-secreta-interna" not in resposta.text


def test_chat_aplica_rate_limit(settings, repositorio):
    settings_limitado = criar_settings(RATE_LIMIT_REQUISICOES=2, RATE_LIMIT_JANELA_SEGUNDOS=60)
    servico = AssistenteJuridicoService(
        repositorio, settings=settings, llm=FakeListChatModel(responses=["ok"])
    )
    with _montar_cliente(settings_limitado, servico, repositorio) as cliente:
        codigos = [cliente.post(URL_CHAT, json=PERGUNTA_VALIDA).status_code for _ in range(3)]
        bloqueada = cliente.post(URL_CHAT, json=PERGUNTA_VALIDA)

    assert codigos == [200, 200, 429]
    assert "Retry-After" in bloqueada.headers


def test_cors_permite_apenas_origens_configuradas():
    settings = criar_settings(CORS_ORIGENS="http://frontend.permitido")
    with _montar_cliente(settings) as cliente:
        permitida = cliente.options(URL_CHAT, headers={
            "Origin": "http://frontend.permitido",
            "Access-Control-Request-Method": "POST",
        })
        bloqueada = cliente.options(URL_CHAT, headers={
            "Origin": "http://site.malicioso",
            "Access-Control-Request-Method": "POST",
        })

    assert permitida.headers.get("access-control-allow-origin") == "http://frontend.permitido"
    assert "access-control-allow-origin" not in bloqueada.headers


def test_documentacao_desabilitada_em_producao():
    with _montar_cliente(criar_settings(AMBIENTE="producao")) as cliente:
        assert cliente.get("/docs").status_code == 404
        assert cliente.get("/openapi.json").status_code == 404


def test_documentacao_disponivel_fora_de_producao(cliente):
    assert cliente.get("/docs").status_code == 200

