"""
Ferramentas de crédito.

Consulta de limite e processamento de solicitações de aumento de crédito.
"""

import csv
import os
from datetime import datetime, timezone

from banco_agil.config import CLIENTES_CSV, SCORE_LIMITE_CSV, SOLICITACOES_CSV


def consultar_limite(cpf: str) -> dict:
    """
    Consulta o limite de crédito atual de um cliente.

    Args:
        cpf: CPF do cliente (apenas números).

    Returns:
        Dicionário com limite atual e informações do cliente.
    """
    cpf_limpo = cpf.replace(".", "").replace("-", "").replace(" ", "")

    try:
        cliente = _buscar_cliente(cpf_limpo)
    except FileNotFoundError:
        return {"sucesso": False, "mensagem": "Erro interno: base de dados não encontrada."}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao consultar dados: {str(e)}"}

    if cliente is None:
        return {"sucesso": False, "mensagem": "Cliente não encontrado."}

    limite = float(cliente["limite_credito"])
    return {
        "sucesso": True,
        "nome": cliente["nome"],
        "cpf": cpf_limpo,
        "limite_atual": limite,
        "limite_formatado": _formatar_moeda(limite),
        "score": int(cliente["score"]),
    }


def solicitar_aumento_limite(cpf: str, novo_limite: float) -> dict:
    """
    Processa uma solicitação de aumento de limite de crédito.

    O fluxo é:
    1. Registra a solicitação no CSV com status 'pendente'
    2. Verifica se o score do cliente permite o novo limite
    3. Atualiza o status para 'aprovado' ou 'rejeitado'
    4. Se aprovado, atualiza o limite no cadastro do cliente

    Args:
        cpf: CPF do cliente (apenas números).
        novo_limite: Valor do novo limite desejado.

    Returns:
        Dicionário com resultado da solicitação.
    """
    cpf_limpo = cpf.replace(".", "").replace("-", "").replace(" ", "")

    if novo_limite <= 0:
        return {
            "sucesso": False,
            "mensagem": "O valor do novo limite deve ser maior que zero.",
        }

    # Busca dados do cliente
    try:
        cliente = _buscar_cliente(cpf_limpo)
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao acessar dados do cliente: {str(e)}"}

    if cliente is None:
        return {"sucesso": False, "mensagem": "Cliente não encontrado."}

    limite_atual = float(cliente["limite_credito"])
    score_cliente = int(cliente["score"])

    if novo_limite <= limite_atual:
        return {
            "sucesso": False,
            "mensagem": (
                f"O novo limite solicitado (R$ {novo_limite:.2f}) deve ser "
                f"maior que o limite atual (R$ {limite_atual:.2f})."
            ),
        }

    # Registra a solicitação como 'pendente'
    timestamp = datetime.now(timezone.utc).isoformat()
    solicitacao = {
        "cpf_cliente": cpf_limpo,
        "data_hora_solicitacao": timestamp,
        "limite_atual": limite_atual,
        "novo_limite_solicitado": novo_limite,
        "status_pedido": "pendente",
    }
    _registrar_solicitacao(solicitacao)

    # Verifica se o score permite o novo limite
    try:
        limite_permitido = _consultar_limite_por_score(score_cliente)
    except Exception as e:
        # Atualiza o status para 'rejeitado' por erro
        _atualizar_status_solicitacao(cpf_limpo, timestamp, "rejeitado")
        return {"sucesso": False, "mensagem": f"Erro ao verificar score: {str(e)}"}

    if novo_limite <= limite_permitido:
        # Aprovado
        _atualizar_status_solicitacao(cpf_limpo, timestamp, "aprovado")
        _atualizar_limite_cliente(cpf_limpo, novo_limite)
        return {
            "sucesso": True,
            "status": "aprovado",
            "mensagem": (
                f"Solicitação aprovada! Seu novo limite de crédito é de "
                f"{_formatar_moeda(novo_limite)}. (Limite anterior: {_formatar_moeda(limite_atual)})"
            ),
            "limite_anterior": limite_atual,
            "novo_limite": novo_limite,
            "score": score_cliente,
        }
    else:
        # Rejeitado
        _atualizar_status_solicitacao(cpf_limpo, timestamp, "rejeitado")
        return {
            "sucesso": True,
            "status": "rejeitado",
            "mensagem": (
                f"Solicitação rejeitada. Seu score atual ({score_cliente}) permite "
                f"um limite máximo de {_formatar_moeda(limite_permitido)}, mas você solicitou "
                f"{_formatar_moeda(novo_limite)}."
            ),
            "limite_atual_da_conta": limite_atual,
            "teto_para_o_score_atual_nao_confunda_com_o_limite": limite_permitido,
            "score": score_cliente,
        }


# ---------------------------------------------------------------------------
# Funções auxiliares (privadas)
# ---------------------------------------------------------------------------

def _buscar_cliente(cpf: str) -> dict | None:
    """Busca um cliente pelo CPF no CSV. Retorna None se não encontrado."""
    with open(CLIENTES_CSV, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            if linha["cpf"] == cpf:
                return linha
    return None


def _consultar_limite_por_score(score: int) -> float:
    """Retorna o limite máximo permitido para um dado score, com base no score_limite.csv."""
    with open(SCORE_LIMITE_CSV, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for faixa in leitor:
            minimo = int(faixa["score_minimo"])
            maximo = int(faixa["score_maximo"])
            if minimo <= score <= maximo:
                return float(faixa["limite_maximo"])

    # Se o score não se encaixa em nenhuma faixa, retorna o menor limite
    return 1000.0


def _formatar_moeda(valor: float) -> str:
    """Formata um valor float para o padrão monetário brasileiro (R$ X.XXX,XX)."""
    # Python f-string usa , para milhar e . para decimal (padrão US)
    # Brasileiro usa . para milhar e , para decimal
    texto = f"{valor:,.2f}"  # ex: "8,000.00"
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")  # ex: "8.000,00"
    return f"R$ {texto}"


def _registrar_solicitacao(solicitacao: dict):
    """Grava uma nova solicitação no CSV de solicitações."""
    arquivo_existe = os.path.exists(SOLICITACOES_CSV)
    colunas = [
        "cpf_cliente",
        "data_hora_solicitacao",
        "limite_atual",
        "novo_limite_solicitado",
        "status_pedido",
    ]

    with open(SOLICITACOES_CSV, mode="a", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        if not arquivo_existe:
            escritor.writeheader()
        escritor.writerow(solicitacao)


def _atualizar_status_solicitacao(cpf: str, timestamp: str, novo_status: str):
    """Atualiza o status de uma solicitação específica no CSV."""
    if not os.path.exists(SOLICITACOES_CSV):
        return

    with open(SOLICITACOES_CSV, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        linhas = list(leitor)
        colunas = leitor.fieldnames

    for linha in linhas:
        if linha["cpf_cliente"] == cpf and linha["data_hora_solicitacao"] == timestamp:
            linha["status_pedido"] = novo_status
            break

    with open(SOLICITACOES_CSV, mode="w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def _atualizar_limite_cliente(cpf: str, novo_limite: float):
    """Atualiza o limite de crédito do cliente no clientes.csv."""
    with open(CLIENTES_CSV, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        linhas = list(leitor)
        colunas = leitor.fieldnames

    for linha in linhas:
        if linha["cpf"] == cpf:
            linha["limite_credito"] = f"{novo_limite:.2f}"
            break

    with open(CLIENTES_CSV, mode="w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)
