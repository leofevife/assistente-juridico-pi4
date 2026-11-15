# Relatório de avaliação: pos-ajuste

- **Data da execução:** 15/11/2026 16:52
- **Ground Truth:** versão 1.0.0 (32 casos)
- **Relatório gerado em:** 15/11/2026 18:56

## Configuração

| Parâmetro | Valor |
|---|---|
| modelo_geracao | `openai/gpt-oss-120b` |
| modelo_juiz | `openai/gpt-oss-20b` |
| modelo_embedding | `BAAI/bge-m3` |
| colecao_qdrant | `cdc_vetores` |
| documentos_recuperados_k | `4` |
| temperatura_geracao | `0.0` |
| prompt_sha256 | `53f23fcf73f7` |
| ragas | `0.4.4` |
| langchain_core | `1.8.1` |
| python | `3.14.0` |

## Indicadores do projeto

| Indicador | Média | Limite | Casos válidos | Situação |
|---|---|---|---|---|
| Faithfulness | 0,884 | > 0,850 | 32/32 | Atingido |
| Answer Relevance | 0,807 | > 0,800 | 32/32 | Atingido |

## Distribuição dos resultados

| Métrica | Mínimo | 1º quartil | Mediana | 3º quartil | Máximo |
|---|---|---|---|---|---|
| Faithfulness | 0,000 | 0,950 | 1,000 | 1,000 | 1,000 |
| Answer Relevance | 0,517 | 0,761 | 0,815 | 0,850 | 0,940 |
| Recall dos artigos de referência | 0,500 | 1,000 | 1,000 | 1,000 | 1,000 |
| Citação dos artigos de referência | 0,000 | 1,000 | 1,000 | 1,000 | 1,000 |

## Casos abaixo do esperado

| Caso | Pergunta | Faith. | Relev. | Recall | Causa provável |
|---|---|---|---|---|---|
| gt-001 | Comprei uma geladeira pela internet e me arrependi. Qual o prazo para devolver? | 1,000 | 0,717 | 1,000 | resposta pouco aderente à pergunta |
| gt-002 | Desisti de uma compra online dentro do prazo de arrependimento. A loja precisa devolver o dinheiro? | 0,750 | 0,816 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-007 | O defeito do produto só apareceu meses depois da compra. Ainda posso reclamar? | 0,750 | 0,733 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-008 | Reclamar diretamente com a loja interrompe o prazo para exigir meus direitos por causa do defeito? | 1,000 | 0,754 | 1,000 | resposta pouco aderente à pergunta |
| gt-009 | A loja disse que a garantia do fabricante acabou e que não tenho mais direitos. Isso está correto? | 0,000 | 0,679 | 0,500 | artigo de referência não foi recuperado |
| gt-013 | Posso reclamar contra a loja ou apenas contra o fabricante quando o produto vem com defeito? | 0,800 | 0,832 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-017 | Fui cobrado por um valor que não devia e acabei pagando. Tenho direito à devolução em dobro? | 1,000 | 0,757 | 1,000 | resposta pouco aderente à pergunta |
| gt-019 | Por quanto tempo meu nome pode ficar negativado em cadastros de proteção ao crédito? | 0,500 | 0,833 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-022 | A loja anunciou um preço e, na hora da compra, se recusou a vender por esse valor. O que posso fazer? | 1,000 | 0,696 | 0,500 | artigo de referência não foi recuperado |
| gt-023 | O que é a inversão do ônus da prova em uma ação de consumo? | 0,500 | 0,517 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-024 | Uma cláusula do contrato diz que a empresa não responde por defeitos. Ela é válida? | 0,500 | 0,790 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-027 | Se houver dúvida sobre o sentido de uma cláusula do contrato, qual interpretação prevalece? | 1,000 | 0,785 | 1,000 | resposta pouco aderente à pergunta |
| gt-028 | O prestador de serviço pode fazer o conserto sem me entregar um orçamento antes? | 0,500 | 0,784 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-029 | Recebi em casa um produto que eu não pedi. Preciso pagar por ele? | 1,000 | 0,796 | 1,000 | resposta pouco aderente à pergunta |
| gt-030 | Qual o limite da multa por atraso no pagamento de uma prestação? | 1,000 | 0,762 | 1,000 | resposta pouco aderente à pergunta |
| gt-032 | Os produtos vendidos no Brasil precisam trazer as informações em português? | 1,000 | 0,729 | 1,000 | resposta pouco aderente à pergunta |

## Resultados por caso

| Caso | Tema | Faith. | Relev. | Recall | Citação | Duração (s) |
|---|---|---|---|---|---|---|
| gt-001 | arrependimento | 1,000 | 0,717 | 1,000 | 1,000 | 1,280 |
| gt-002 | arrependimento | 0,750 | 0,816 | 1,000 | 1,000 | 0,970 |
| gt-003 | vicio do produto | 1,000 | 0,815 | 1,000 | 1,000 | 1,010 |
| gt-004 | vicio do produto | 1,000 | 0,822 | 1,000 | 1,000 | 0,890 |
| gt-005 | prazo para reclamar | 1,000 | 0,907 | 1,000 | 1,000 | 3,960 |
| gt-006 | prazo para reclamar | 1,000 | 0,929 | 1,000 | 1,000 | 12,770 |
| gt-007 | vicio oculto | 0,750 | 0,733 | 1,000 | 1,000 | 12,860 |
| gt-008 | prazo para reclamar | 1,000 | 0,754 | 1,000 | 1,000 | 16,890 |
| gt-009 | garantia | 0,000 | 0,679 | 0,500 | 0,500 | 11,450 |
| gt-010 | garantia | 1,000 | 0,864 | 1,000 | 1,000 | 8,640 |
| gt-011 | vicio do produto | 1,000 | 0,940 | 1,000 | 1,000 | 17,730 |
| gt-012 | vicio do servico | 1,000 | 0,840 | 1,000 | 1,000 | 15,720 |
| gt-013 | responsabilidade solidaria | 0,800 | 0,832 | 1,000 | 0,000 | 17,680 |
| gt-014 | fato do produto | 1,000 | 0,806 | 1,000 | 1,000 | 8,790 |
| gt-015 | fato do produto | 1,000 | 0,914 | 1,000 | 1,000 | 12,590 |
| gt-016 | prescricao | 1,000 | 0,887 | 1,000 | 1,000 | 13,500 |
| gt-017 | cobranca indevida | 1,000 | 0,757 | 1,000 | 1,000 | 14,720 |
| gt-018 | cobranca | 1,000 | 0,845 | 1,000 | 1,000 | 15,230 |
| gt-019 | cadastro de inadimplentes | 0,500 | 0,833 | 1,000 | 1,000 | 6,500 |
| gt-020 | cadastro de inadimplentes | 1,000 | 0,803 | 1,000 | 1,000 | 11,830 |
| gt-021 | publicidade | 1,000 | 0,919 | 1,000 | 1,000 | 7,600 |
| gt-022 | oferta | 1,000 | 0,696 | 0,500 | 0,500 | 12,570 |
| gt-023 | processo de consumo | 0,500 | 0,517 | 1,000 | 1,000 | 13,710 |
| gt-024 | clausulas abusivas | 0,500 | 0,790 | 1,000 | 1,000 | 17,940 |
| gt-025 | clausulas abusivas | 1,000 | 0,839 | 1,000 | 1,000 | 51,250 |
| gt-026 | contrato de adesao | 1,000 | 0,897 | 1,000 | 1,000 | 1,650 |
| gt-027 | interpretacao contratual | 1,000 | 0,785 | 1,000 | 1,000 | 8,880 |
| gt-028 | orcamento | 0,500 | 0,784 | 1,000 | 1,000 | 12,580 |
| gt-029 | praticas abusivas | 1,000 | 0,796 | 1,000 | 1,000 | 16,590 |
| gt-030 | credito e financiamento | 1,000 | 0,762 | 1,000 | 1,000 | 11,550 |
| gt-031 | credito e financiamento | 1,000 | 0,821 | 1,000 | 1,000 | 15,960 |
| gt-032 | informacao | 1,000 | 0,729 | 1,000 | 1,000 | 6,910 |
