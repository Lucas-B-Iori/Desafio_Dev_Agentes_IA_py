import os

from google.adk.models.lite_llm import LiteLlm

# Diretório base do pacote banco_agil
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")

# Caminhos dos arquivos CSV
CLIENTES_CSV = os.path.join(DADOS_DIR, "clientes.csv")
SCORE_LIMITE_CSV = os.path.join(DADOS_DIR, "score_limite.csv")
SOLICITACOES_CSV = os.path.join(DADOS_DIR, "solicitacoes_aumento_limite.csv")

# Modelo LLM via OpenRouter
# Usa o LiteLlm como bridge entre o ADK e o OpenRouter
MODELO_LLM = LiteLlm(model="openrouter/google/gemini-3-flash-preview")

# AwesomeAPI
AWESOMEAPI_URL = "https://economia.awesomeapi.com.br/json/last"

# Pesos para cálculo do score de crédito
PESO_RENDA = 80

PESO_EMPREGO = {
    "formal": 300,
    "autônomo": 250,
    "autonomo": 250,
    "desempregado": 0,
}

PESO_DEPENDENTES = {
    0: 100,
    1: 80,
    2: 60,
}
PESO_DEPENDENTES_3_MAIS = 30

PESO_DIVIDAS = {
    "sim": -100,
    "não": 100,
    "nao": 100,
}

# Score
SCORE_MINIMO = 0
SCORE_MAXIMO = 1000
