"""
Ferramentas de cálculo e atualização do score de crédito.

Implementa a fórmula ponderada definida no desafio e atualiza o score
do cliente na base de dados.
"""

import csv

from banco_agil.config import (
    CLIENTES_CSV,
    PESO_RENDA,
    PESO_EMPREGO,
    PESO_DEPENDENTES,
    PESO_DEPENDENTES_3_MAIS,
    PESO_DIVIDAS,
    SCORE_MINIMO,
    SCORE_MAXIMO,
)


def calcular_score(
    renda_mensal: float,
    tipo_emprego: str,
    despesas_fixas: float,
    num_dependentes: int,
    tem_dividas: str,
) -> dict:
    """
    Calcula o score de crédito com base nos dados financeiros do cliente.

    Fórmula:
        score = (renda / (despesas + 1)) * peso_renda
                + peso_emprego[tipo]
                + peso_dependentes[n]
                + peso_dividas[tem_dividas]

    Args:
        renda_mensal: Renda mensal bruta do cliente.
        tipo_emprego: 'formal', 'autônomo' ou 'desempregado'.
        despesas_fixas: Total de despesas fixas mensais.
        num_dependentes: Número de dependentes (0, 1, 2, 3+).
        tem_dividas: 'sim' ou 'não'.

    Returns:
        Dicionário com o score calculado e o detalhamento de cada componente.
    """
    # Validações básicas
    if renda_mensal < 0:
        return {"sucesso": False, "mensagem": "A renda mensal não pode ser negativa."}
    if despesas_fixas < 0:
        return {"sucesso": False, "mensagem": "As despesas não podem ser negativas."}
    if num_dependentes < 0:
        return {"sucesso": False, "mensagem": "O número de dependentes não pode ser negativo."}

    # Normaliza inputs
    tipo_emprego_norm = tipo_emprego.strip().lower()
    tem_dividas_norm = tem_dividas.strip().lower()

    # Mapeamento de sinônimos para tipo de emprego
    SINONIMOS_EMPREGO = {
        "clt": "formal",
        "registrado": "formal",
        "carteira assinada": "formal",
        "empregado": "formal",
        "empregada": "formal",
        "funcionário": "formal",
        "funcionario": "formal",
        "funcionaria": "formal",
        "pj": "autônomo",
        "freelancer": "autônomo",
        "freelance": "autônomo",
        "empresário": "autônomo",
        "empresario": "autônomo",
        "empresaria": "autônomo",
        "empreendedor": "autônomo",
        "empreendedora": "autônomo",
        "mei": "autônomo",
        "liberal": "autônomo",
        "profissional liberal": "autônomo",
        "conta própria": "autônomo",
        "sem emprego": "desempregado",
        "desempregada": "desempregado",
    }
    tipo_emprego_norm = SINONIMOS_EMPREGO.get(tipo_emprego_norm, tipo_emprego_norm)

    # Mapeamento de sinônimos para dívidas
    SINONIMOS_DIVIDAS = {
        "nada": "não",
        "zero": "não",
        "nenhuma": "não",
        "nenhum": "não",
        "0": "não",
        "não tenho": "não",
        "nao tenho": "não",
        "nao": "não",
        "n": "não",
        "nop": "não",
        "no": "não",
        "tenho": "sim",
        "s": "sim",
        "possuo": "sim",
        "tenho sim": "sim",
    }
    tem_dividas_norm = SINONIMOS_DIVIDAS.get(tem_dividas_norm, tem_dividas_norm)

    # Componente de renda
    componente_renda = (renda_mensal / (despesas_fixas + 1)) * PESO_RENDA

    # Componente de emprego
    componente_emprego = PESO_EMPREGO.get(tipo_emprego_norm, None)
    if componente_emprego is None:
        return {
            "sucesso": False,
            "mensagem": (
                f"Tipo de emprego '{tipo_emprego}' não reconhecido. "
                "Use: formal/CLT, autônomo/PJ, ou desempregado."
            ),
        }

    # Componente de dependentes
    if num_dependentes >= 3:
        componente_dependentes = PESO_DEPENDENTES_3_MAIS
    else:
        componente_dependentes = PESO_DEPENDENTES.get(num_dependentes, PESO_DEPENDENTES_3_MAIS)

    # Componente de dívidas
    componente_dividas = PESO_DIVIDAS.get(tem_dividas_norm, None)
    if componente_dividas is None:
        return {
            "sucesso": False,
            "mensagem": (
                f"Valor '{tem_dividas}' não reconhecido para dívidas. "
                "Responda com 'sim' ou 'não'."
            ),
        }

    # Calcula score bruto e limita ao intervalo [0, 1000]
    score_bruto = (
        componente_renda
        + componente_emprego
        + componente_dependentes
        + componente_dividas
    )
    score_final = int(max(SCORE_MINIMO, min(SCORE_MAXIMO, score_bruto)))

    return {
        "sucesso": True,
        "score": score_final,
        "detalhamento": {
            "componente_renda": round(componente_renda, 2),
            "componente_emprego": componente_emprego,
            "componente_dependentes": componente_dependentes,
            "componente_dividas": componente_dividas,
        },
        "mensagem": f"Score calculado: {score_final} pontos (de 0 a 1000).",
    }


def atualizar_score_cliente(cpf: str, novo_score: int) -> dict:
    """
    Atualiza o score de crédito de um cliente no clientes.csv.

    Args:
        cpf: CPF do cliente.
        novo_score: Novo valor de score (0-1000).

    Returns:
        Dicionário confirmando a atualização.
    """
    cpf_limpo = cpf.replace(".", "").replace("-", "").replace(" ", "")

    if not (SCORE_MINIMO <= novo_score <= SCORE_MAXIMO):
        return {
            "sucesso": False,
            "mensagem": f"Score deve estar entre {SCORE_MINIMO} e {SCORE_MAXIMO}.",
        }

    try:
        with open(CLIENTES_CSV, mode="r", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            linhas = list(leitor)
            colunas = leitor.fieldnames

        cliente_encontrado = False
        score_anterior = None

        for linha in linhas:
            if linha["cpf"] == cpf_limpo:
                score_anterior = int(linha["score"])
                linha["score"] = str(novo_score)
                cliente_encontrado = True
                break

        if not cliente_encontrado:
            return {"sucesso": False, "mensagem": "Cliente não encontrado na base de dados."}

        with open(CLIENTES_CSV, mode="w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=colunas)
            escritor.writeheader()
            escritor.writerows(linhas)

        return {
            "sucesso": True,
            "mensagem": (
                f"Score atualizado com sucesso! "
                f"Score anterior: {score_anterior} → Novo score: {novo_score}."
            ),
            "score_anterior": score_anterior,
            "novo_score": novo_score,
        }

    except FileNotFoundError:
        return {"sucesso": False, "mensagem": "Erro interno: base de dados não encontrada."}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao atualizar score: {str(e)}"}
