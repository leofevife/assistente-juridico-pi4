# Relatório de avaliação: baseline

- **Data da execução:** 15/11/2026 14:51
- **Ground Truth:** versão 1.0.0 (32 casos)
- **Relatório gerado em:** 15/11/2026 15:27

## Configuração

| Parâmetro | Valor |
|---|---|
| modelo_geracao | `openai/gpt-oss-120b` |
| modelo_juiz | `openai/gpt-oss-120b` |
| modelo_embedding | `BAAI/bge-m3` |
| colecao_qdrant | `cdc_vetores` |
| documentos_recuperados_k | `4` |
| temperatura_geracao | `0.0` |
| prompt_sha256 | `6f2c3140915a` |
| ragas | `0.4.4` |
| langchain_core | `1.8.1` |
| python | `3.14.0` |

## Indicadores do projeto

| Indicador | Média | Limite | Casos válidos | Situação |
|---|---|---|---|---|
| Faithfulness | 0,911 | > 0,850 | 32/32 | Atingido |
| Answer Relevance | 0,773 | > 0,800 | 32/32 | Não atingido |

## Distribuição dos resultados

| Métrica | Mínimo | 1º quartil | Mediana | 3º quartil | Máximo |
|---|---|---|---|---|---|
| Faithfulness | 0,500 | 0,818 | 1,000 | 1,000 | 1,000 |
| Answer Relevance | 0,469 | 0,709 | 0,764 | 0,869 | 0,984 |
| Recall dos artigos de referência | 0,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| Citação dos artigos de referência | 0,000 | 1,000 | 1,000 | 1,000 | 1,000 |

## Casos abaixo do esperado

| Caso | Pergunta | Faith. | Relev. | Recall | Causa provável |
|---|---|---|---|---|---|
| gt-001 | Comprei uma geladeira pela internet e me arrependi. Qual o prazo para devolver? | 0,818 | 0,669 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-002 | Desisti de uma compra online dentro do prazo de arrependimento. A loja precisa devolver o dinheiro? | 0,818 | 0,881 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-003 | Meu celular apresentou defeito e a assistência não resolveu em 30 dias. O que posso exigir? | 0,941 | 0,669 | 1,000 | resposta pouco aderente à pergunta |
| gt-004 | Posso exigir a troca ou o dinheiro de volta na hora, sem esperar os 30 dias, se o produto com defeito for essencial? | 0,909 | 0,793 | 1,000 | resposta pouco aderente à pergunta |
| gt-007 | O defeito do produto só apareceu meses depois da compra. Ainda posso reclamar? | 0,700 | 0,679 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-008 | Reclamar diretamente com a loja interrompe o prazo para exigir meus direitos por causa do defeito? | 0,500 | 0,753 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-009 | A loja disse que a garantia do fabricante acabou e que não tenho mais direitos. Isso está correto? | 1,000 | 0,741 | 0,500 | artigo de referência não foi recuperado |
| gt-010 | O que é a garantia contratual e como ela deve ser entregue ao consumidor? | 1,000 | 0,784 | 1,000 | resposta pouco aderente à pergunta |
| gt-011 | Qual o prazo que o fornecedor tem para consertar um produto com defeito? | 1,000 | 0,788 | 1,000 | resposta pouco aderente à pergunta |
| gt-012 | Contratei um serviço que foi mal executado. Quais são os meus direitos? | 1,000 | 0,672 | 1,000 | resposta pouco aderente à pergunta |
| gt-014 | Um produto defeituoso me causou uma lesão. O fabricante responde mesmo sem ter agido com culpa? | 0,778 | 0,722 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-015 | Em quais situações o comerciante responde pelos danos causados por um produto defeituoso? | 0,800 | 0,855 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-020 | Encontrei uma informação errada no meu cadastro de crédito. O que posso exigir? | 0,769 | 0,856 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-021 | O que caracteriza uma publicidade enganosa? | 1,000 | 0,729 | 1,000 | resposta pouco aderente à pergunta |
| gt-022 | A loja anunciou um preço e, na hora da compra, se recusou a vender por esse valor. O que posso fazer? | 0,900 | 0,657 | 0,500 | artigo de referência não foi recuperado |
| gt-023 | O que é a inversão do ônus da prova em uma ação de consumo? | 1,000 | 0,649 | 0,000 | artigo de referência não foi recuperado |
| gt-024 | Uma cláusula do contrato diz que a empresa não responde por defeitos. Ela é válida? | 1,000 | 0,765 | 1,000 | resposta pouco aderente à pergunta |
| gt-025 | O contrato permite que a empresa altere o preço unilateralmente. Isso é legal? | 1,000 | 0,762 | 1,000 | resposta pouco aderente à pergunta |
| gt-026 | Como devem ser redigidos os contratos de adesão? | 1,000 | 0,736 | 1,000 | resposta pouco aderente à pergunta |
| gt-027 | Se houver dúvida sobre o sentido de uma cláusula do contrato, qual interpretação prevalece? | 1,000 | 0,710 | 1,000 | resposta pouco aderente à pergunta |
| gt-028 | O prestador de serviço pode fazer o conserto sem me entregar um orçamento antes? | 0,800 | 0,469 | 0,500 | artigo de referência não foi recuperado |
| gt-029 | Recebi em casa um produto que eu não pedi. Preciso pagar por ele? | 0,667 | 0,876 | 1,000 | resposta traz afirmações que o contexto recuperado não sustenta |
| gt-031 | Parei de pagar um bem comprado em prestações. O vendedor pode ficar com tudo o que já paguei? | 0,875 | 0,727 | 1,000 | resposta pouco aderente à pergunta |
| gt-032 | Os produtos vendidos no Brasil precisam trazer as informações em português? | 1,000 | 0,707 | 1,000 | resposta pouco aderente à pergunta |

## Resultados por caso

| Caso | Tema | Faith. | Relev. | Recall | Citação | Duração (s) |
|---|---|---|---|---|---|---|
| gt-001 | arrependimento | 0,818 | 0,669 | 1,000 | 1,000 | 1,790 |
| gt-002 | arrependimento | 0,818 | 0,881 | 1,000 | 1,000 | 1,480 |
| gt-003 | vicio do produto | 0,941 | 0,669 | 1,000 | 1,000 | 2,210 |
| gt-004 | vicio do produto | 0,909 | 0,793 | 1,000 | 1,000 | 1,650 |
| gt-005 | prazo para reclamar | 1,000 | 0,888 | 1,000 | 1,000 | 5,440 |
| gt-006 | prazo para reclamar | 1,000 | 0,868 | 1,000 | 1,000 | 9,100 |
| gt-007 | vicio oculto | 0,700 | 0,679 | 1,000 | 1,000 | 17,450 |
| gt-008 | prazo para reclamar | 0,500 | 0,753 | 1,000 | 1,000 | 6,000 |
| gt-009 | garantia | 1,000 | 0,741 | 0,500 | 0,500 | 7,300 |
| gt-010 | garantia | 1,000 | 0,784 | 1,000 | 1,000 | 7,100 |
| gt-011 | vicio do produto | 1,000 | 0,788 | 1,000 | 1,000 | 14,430 |
| gt-012 | vicio do servico | 1,000 | 0,672 | 1,000 | 1,000 | 12,260 |
| gt-013 | responsabilidade solidaria | 1,000 | 0,871 | 1,000 | 1,000 | 15,300 |
| gt-014 | fato do produto | 0,778 | 0,722 | 1,000 | 1,000 | 14,200 |
| gt-015 | fato do produto | 0,800 | 0,855 | 1,000 | 1,000 | 14,260 |
| gt-016 | prescricao | 1,000 | 0,900 | 1,000 | 1,000 | 12,980 |
| gt-017 | cobranca indevida | 0,875 | 0,875 | 1,000 | 1,000 | 13,570 |
| gt-018 | cobranca | 1,000 | 0,810 | 1,000 | 1,000 | 13,330 |
| gt-019 | cadastro de inadimplentes | 1,000 | 0,882 | 1,000 | 1,000 | 11,840 |
| gt-020 | cadastro de inadimplentes | 0,769 | 0,856 | 1,000 | 1,000 | 8,840 |
| gt-021 | publicidade | 1,000 | 0,729 | 1,000 | 1,000 | 13,520 |
| gt-022 | oferta | 0,900 | 0,657 | 0,500 | 0,500 | 11,500 |
| gt-023 | processo de consumo | 1,000 | 0,649 | 0,000 | 0,000 | 2,200 |
| gt-024 | clausulas abusivas | 1,000 | 0,765 | 1,000 | 1,000 | 1,570 |
| gt-025 | clausulas abusivas | 1,000 | 0,762 | 1,000 | 1,000 | 9,390 |
| gt-026 | contrato de adesao | 1,000 | 0,736 | 1,000 | 1,000 | 10,860 |
| gt-027 | interpretacao contratual | 1,000 | 0,710 | 1,000 | 1,000 | 11,090 |
| gt-028 | orcamento | 0,800 | 0,469 | 0,500 | 0,500 | 6,460 |
| gt-029 | praticas abusivas | 0,667 | 0,876 | 1,000 | 1,000 | 12,480 |
| gt-030 | credito e financiamento | 1,000 | 0,984 | 1,000 | 1,000 | 1,610 |
| gt-031 | credito e financiamento | 0,875 | 0,727 | 1,000 | 1,000 | 9,880 |
| gt-032 | informacao | 1,000 | 0,707 | 1,000 | 1,000 | 9,840 |
