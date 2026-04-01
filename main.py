"""
Ponto de entrada CLI para o Banco Ágil.

Permite interagir com o sistema multi-agentes diretamente pelo terminal.
Útil para testes rápidos durante o desenvolvimento.
"""

import asyncio
import os

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from banco_agil.agentes.triagem import root_agent

load_dotenv()


async def main():
    """Loop principal do atendimento via terminal."""
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="banco_agil",
    )

    user_id = "cliente_cli"
    session_id = "sessao_terminal"

    # Garante que a sessão exista
    session = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if not session:
        await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )

    print("=" * 60)
    print("  Banco Ágil — Atendimento ao Cliente")
    print("=" * 60)
    print("  Digite 'sair' para encerrar.\n")

    while True:
        try:
            entrada = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAtendimento encerrado. Até logo!")
            break

        if not entrada:
            continue

        if entrada.lower() in ("sair", "exit", "quit"):
            print("\nAtendimento encerrado. Até logo! 👋")
            break

        conteudo = types.Content(
            role="user",
            parts=[types.Part.from_text(text=entrada)],
        )

        resposta_completa = []

        async for evento in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=conteudo,
        ):
            if evento.content and evento.content.parts:
                for parte in evento.content.parts:
                    if parte.text and parte.text.strip():
                        resposta_completa.append(parte.text)

        if resposta_completa:
            print(f"\nBanco Ágil: {' '.join(resposta_completa)}\n")
        else:
            print(f"\nBanco Ágil: No momento, não consegui processar sua solicitação. Poderia reformular?\n")


if __name__ == "__main__":
    asyncio.run(main())
