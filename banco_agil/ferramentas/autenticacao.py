"""
Ferramenta de autenticação de clientes.

Valida CPF e data de nascimento contra a base de dados (clientes.csv).
"""

import csv
from datetime import datetime

from banco_agil.config import CLIENTES_CSV

_tentativas_falhas = {}

def autenticar_cliente(cpf: str, data_nascimento: str) -> dict:
    """
    Autentica um cliente verificando CPF e data de nascimento na base de dados.

    Args:
        cpf: CPF do cliente (apenas números, 11 dígitos).
        data_nascimento: Data de nascimento no formato DD/MM/AAAA ou AAAA-MM-DD.

    Returns:
        Dicionário com 'sucesso' (bool), 'mensagem' (str), e 'cliente' (dict) se autenticado.
    """
    # Limpa o CPF removendo pontos e traços
    cpf_limpo = cpf.replace(".", "").replace("-", "").replace(" ", "")

    # Checa bloqueio de segurança
    if _tentativas_falhas.get(cpf_limpo, 0) >= 3:
        return {
            "sucesso": False,
            "mensagem": "BLOQUEIO_SEGURANCA: Este CPF errou os dados 3 vezes. A operação está bloqueada temporariamente. Avise o cliente com empatia que, por segurança, ele não poderá acessar agora.",
        }

    if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
        _tentativas_falhas[cpf_limpo] = _tentativas_falhas.get(cpf_limpo, 0) + 1
        return {
            "sucesso": False,
            "mensagem": "CPF inválido. O CPF deve conter exatamente 11 dígitos numéricos.",
        }

    # Normaliza a data de nascimento para o formato AAAA-MM-DD
    data_normalizada = _normalizar_data(data_nascimento)
    if data_normalizada is None:
        return {
            "sucesso": False,
            "mensagem": "Data de nascimento em formato inválido. Use DD/MM/AAAA ou AAAA-MM-DD.",
        }

    # Busca o cliente na base de dados
    try:
        clientes = _ler_clientes()
    except FileNotFoundError:
        return {
            "sucesso": False,
            "mensagem": "Erro interno: base de dados de clientes não encontrada.",
        }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao acessar a base de dados: {str(e)}",
        }

    for cliente in clientes:
        if cliente["cpf"] == cpf_limpo:
            if cliente["data_nascimento"] == data_normalizada:
                # Sucesso: zera as tentativas
                _tentativas_falhas[cpf_limpo] = 0
                return {
                    "sucesso": True,
                    "mensagem": f"Cliente {cliente['nome']} autenticado com sucesso.",
                    "cliente": {
                        "cpf": cliente["cpf"],
                        "nome": cliente["nome"],
                        "score": int(cliente["score"]),
                        "limite_credito": float(cliente["limite_credito"]),
                    },
                }
            else:
                _tentativas_falhas[cpf_limpo] = _tentativas_falhas.get(cpf_limpo, 0) + 1
                return {
                    "sucesso": False,
                    "mensagem": "ERRO_DADOS: Data de nascimento não confere com o CPF informado.",
                }

    _tentativas_falhas[cpf_limpo] = _tentativas_falhas.get(cpf_limpo, 0) + 1
    return {
        "sucesso": False,
        "mensagem": "ERRO_DADOS: CPF não encontrado na base de dados.",
    }


def _normalizar_data(data_str: str) -> str | None:
    """Converte data para o formato AAAA-MM-DD. Aceita DD/MM/AAAA e AAAA-MM-DD."""
    data_str = data_str.strip()

    formatos = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]
    for fmt in formatos:
        try:
            data = datetime.strptime(data_str, fmt)
            return data.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _ler_clientes() -> list[dict]:
    """Lê o CSV de clientes e retorna como lista de dicionários."""
    with open(CLIENTES_CSV, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)
