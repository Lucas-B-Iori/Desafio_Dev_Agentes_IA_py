"""
Ferramenta de consulta de câmbio.

Consulta cotações de moedas em tempo real usando a AwesomeAPI.
"""

import requests

from banco_agil.config import AWESOMEAPI_URL


# Moedas mais comuns para referência rápida
MOEDAS_DISPONIVEIS = {
    "dólar": "USD",
    "dolar": "USD",
    "usd": "USD",
    "euro": "EUR",
    "eur": "EUR",
    "libra": "GBP",
    "gbp": "GBP",
    "iene": "JPY",
    "yen": "JPY",
    "jpy": "JPY",
    "bitcoin": "BTC",
    "btc": "BTC",
    "peso argentino": "ARS",
    "ars": "ARS",
    "franco suíço": "CHF",
    "chf": "CHF",
    "dólar canadense": "CAD",
    "cad": "CAD",
    "yuan": "CNY",
    "cny": "CNY",
}


def consultar_cotacao(moeda: str) -> dict:
    """
    Consulta a cotação de uma moeda em relação ao Real (BRL).

    Args:
        moeda: Nome ou código da moeda (ex: 'dólar', 'USD', 'EUR', 'euro').

    Returns:
        Dicionário com valores de compra, venda e data da cotação.
    """
    # Resolve o código da moeda
    moeda_norm = moeda.strip().lower()
    codigo = MOEDAS_DISPONIVEIS.get(moeda_norm, moeda.strip().upper())

    # O destino é sempre BRL
    par = f"{codigo}-BRL"
    url = f"{AWESOMEAPI_URL}/{par}"

    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
    except requests.ConnectionError:
        return {
            "sucesso": False,
            "mensagem": "Não foi possível conectar ao serviço de cotações. Verifique sua conexão.",
        }
    except requests.Timeout:
        return {
            "sucesso": False,
            "mensagem": "O serviço de cotações demorou demais para responder. Tente novamente.",
        }
    except requests.HTTPError as e:
        if resposta.status_code == 404:
            return {
                "sucesso": False,
                "mensagem": f"Moeda '{moeda}' não encontrada. Tente 'dólar', 'euro', 'libra', etc.",
            }
        return {
            "sucesso": False,
            "mensagem": f"Erro ao consultar cotação: {str(e)}",
        }

    try:
        dados = resposta.json()
        chave = f"{codigo}BRL"

        if chave not in dados:
            return {
                "sucesso": False,
                "mensagem": f"Cotação para '{moeda}' não disponível no momento.",
            }

        cotacao = dados[chave]
        return {
            "sucesso": True,
            "moeda": cotacao.get("name", par),
            "codigo": codigo,
            "compra": float(cotacao["bid"]),
            "venda": float(cotacao["ask"]),
            "variacao": float(cotacao.get("pctChange", 0)),
            "maximo_dia": float(cotacao.get("high", 0)),
            "minimo_dia": float(cotacao.get("low", 0)),
            "data_cotacao": cotacao.get("create_date", "N/A"),
            "mensagem": (
                f"Cotação do {cotacao.get('name', codigo)}: "
                f"Compra: R$ {float(cotacao['bid']):.4f} | "
                f"Venda: R$ {float(cotacao['ask']):.4f} | "
                f"Variação: {cotacao.get('pctChange', 'N/A')}%"
            ),
        }
    except (ValueError, KeyError) as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao processar dados da cotação: {str(e)}",
        }
