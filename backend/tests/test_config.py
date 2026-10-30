from backend.tests.fakes import criar_settings


def test_cors_aceita_lista_separada_por_virgula():
    settings = criar_settings(CORS_ORIGENS="http://a.com, http://b.com")
    assert settings.cors_origens == ["http://a.com", "http://b.com"]


def test_cors_aceita_formato_json():
    settings = criar_settings(CORS_ORIGENS='["http://a.com"]')
    assert settings.cors_origens == ["http://a.com"]


def test_chaves_nao_vazam_na_representacao():
    settings = criar_settings(GROQ_API_KEY="segredo-groq", QDRANT_API_KEY="segredo-qdrant")
    representacao = repr(settings)
    assert "segredo-groq" not in representacao
    assert "segredo-qdrant" not in representacao
    assert settings.groq_api_key.get_secret_value() == "segredo-groq"


def test_identifica_ambiente_de_producao():
    assert criar_settings(AMBIENTE="producao").em_producao is True
    assert criar_settings(AMBIENTE="desenvolvimento").em_producao is False
