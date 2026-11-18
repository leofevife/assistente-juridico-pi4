import pytest

from backend.tests.fakes import criar_settings


def test_cors_aceita_lista_separada_por_virgula():
    settings = criar_settings(CORS_ORIGENS="http://a.com, http://b.com")
    assert settings.cors_origens == ["http://a.com", "http://b.com"]


def test_cors_aceita_formato_json():
    settings = criar_settings(CORS_ORIGENS='["http://a.com"]')
    assert settings.cors_origens == ["http://a.com"]


def test_chaves_nao_vazam_na_representacao():
    settings = criar_settings(
        GROQ_API_KEY="segredo-groq",
        QDRANT_API_KEY="segredo-qdrant",
        HF_API_TOKEN="segredo-hf",
    )
    representacao = repr(settings)
    assert "segredo-groq" not in representacao
    assert "segredo-qdrant" not in representacao
    assert "segredo-hf" not in representacao
    assert settings.groq_api_key.get_secret_value() == "segredo-groq"
    assert settings.hf_api_token is not None
    assert settings.hf_api_token.get_secret_value() == "segredo-hf"


def test_identifica_ambiente_de_producao():
    assert criar_settings(AMBIENTE="producao").em_producao is True
    assert criar_settings(AMBIENTE="desenvolvimento").em_producao is False


def test_aceita_alias_hf_token():
    settings = criar_settings(HF_TOKEN="hf-alias")
    assert settings.hf_api_token is not None
    assert settings.hf_api_token.get_secret_value() == "hf-alias"


def test_usar_embedding_remoto_por_provedor(monkeypatch):
    for var in ("HF_API_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "HF_TOKEN"):
        monkeypatch.delenv(var, raising=False)

    assert criar_settings(EMBEDDING_PROVEDOR="auto").usar_embedding_remoto is False
    assert criar_settings(EMBEDDING_PROVEDOR="auto", HF_API_TOKEN="").usar_embedding_remoto is False
    assert criar_settings(EMBEDDING_PROVEDOR="auto", HF_API_TOKEN="hf-123").usar_embedding_remoto is True
    assert criar_settings(EMBEDDING_PROVEDOR="api").usar_embedding_remoto is True
    assert criar_settings(EMBEDDING_PROVEDOR="huggingface_api").embedding_provedor == "api"
    assert criar_settings(EMBEDDING_PROVEDOR="local", HF_API_TOKEN="hf-123").usar_embedding_remoto is False


def test_rejeita_embedding_provedor_invalido():
    with pytest.raises(ValueError):
        criar_settings(EMBEDDING_PROVEDOR="invalido")
