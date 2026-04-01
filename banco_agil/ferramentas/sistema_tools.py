"""
Ferramentas de sistema (ações transversais).

Fornece funções que são comuns a múltiplos agentes para
controle de fluxo principal, como o encerramento de sessão.
"""

def encerrar_atendimento() -> dict:
    """
    Encerra o atendimento atual a pedido do cliente ou por bloqueio de segurança.
    DEVE ser chamada obrigatoriamente quando o cliente disser que deseja terminar a conversa,
    despedir-se dizendo 'tchau', ou caso o sistema exija por bloqueios (ex: 3 falhas de login).
    """
    return {
        "sucesso": True,
        "mensagem": (
            "Comando de ENCERRAMENTO SISTÊMICO disparado com sucesso. "
            "A interface do usuário será bloqueada agora. "
            "Gere OBRIGATORIAMENTE um texto final para se despedir formalmente do cliente "
            "e comunique que o atendimento foi encerrado encerrado."
        ),
    }
