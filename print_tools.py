import asyncio
from banco_agil.agentes.triagem import root_agent
from banco_agil.agentes.cambio import agente_cambio

def main():
    print(f"Agent Name: {agente_cambio.name}")
    print(f"Parent: {agente_cambio.parent.name if hasattr(agente_cambio, 'parent') and agente_cambio.parent else 'None'}")
    
    # tools inside default agent
    print("Tools directly on agente_cambio:")
    for t in agente_cambio.tools:
        print(getattr(t, "name", t.__name__ if hasattr(t, '__name__') else t))

if __name__ == "__main__":
    main()
