import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from backend.data.repositorio_vetorial import CDCVectorRepository

load_dotenv()

class AssistenteJuridicoService:
    def __init__(self, repository: CDCVectorRepository):
        self.retriever = repository.obter_retriever(k=4)
        
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.0, 
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Configuração do Prompt (vamos ajustando esse trem depois, tem que testar!)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Você é um assistente jurídico especializado exclusivamente no Código de Defesa do Consumidor (CDC - Lei 8.078/1990).\n"
                "Sua tarefa é responder à dúvida do usuário utilizando APENAS os trechos da lei fornecidos abaixo no contexto.\n\n"
                "Regras estritas de conduta:\n"
                "1. Fundamente sua resposta citando explicitamente os números dos Artigos (e parágrafos/incisos) presentes no contexto.\n"
                "2. Não invente interpretações, não utilize conhecimentos externos ao contexto e não faça suposições.\n"
                "3. Se os trechos fornecidos no contexto não contiverem informação suficiente para responder à pergunta com segurança, "
                "diga exatamente: 'Com base nos artigos recuperados do Código de Defesa do Consumidor, não há informações suficientes para responder a esta dúvida.'\n\n"
                "Contexto Legal Recuperado:\n{contexto}"
            )),
            ("human", "Dúvida do usuário: {pergunta}")
        ])

        # Constroi a cadeia (Chain) de execução usando LCEL (LangChain Expression Language)
        self.chain = (
            {
                "contexto": self.retriever | self._formatar_documentos,
                "pergunta": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    @staticmethod
    def _formatar_documentos(docs) -> str:
        #Junta os textos dos múltiplos artigos recuperados pelo Qdrant em uma única string para o Prompt
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    def responder_duvida(self, pergunta: str) -> str:
        #Executa o fluxo completo do RAG e retorna a resposta final formatada
        return self.chain.invoke(pergunta)