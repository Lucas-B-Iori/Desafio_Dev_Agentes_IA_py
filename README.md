# 🏦 Banco Ágil — Sistema Multi-Agentes de Atendimento Bancário

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![Google ADK](https://img.shields.io/badge/Google%20ADK-1.0%2B-4285F4?logo=google&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?logo=streamlit&logoColor=white)
![LiteLLM](https://img.shields.io/badge/LiteLLM-1.40%2B-8A2BE2)
![OpenRouter](https://img.shields.io/badge/OpenRouter-Gemini%203%20Flash-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

[![Acesse o sistema online](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://desafioagenteia.streamlit.app/)

---

##  Visão Geral

O **Banco Ágil** é um sistema de atendimento ao cliente bancário totalmente orientado a Inteligência Artificial, construído com uma arquitetura **multi-agentes**. O projeto simula o atendimento de um banco digital fictício, onde o cliente interage com uma única interface de chat — sem perceber que, por baixo dos panos, múltiplos agentes especializados colaboram para resolver sua demanda.

O sistema oferece quatro serviços principais:

-  **Autenticação segura** por CPF e data de nascimento
-  **Consulta e aumento de limite de crédito** com análise de score
-  **Reavaliação do perfil financeiro** via entrevista conversacional
-  **Cotação de moedas em tempo real** via API externa

A experiência é desenhada para que o cliente se sinta atendido por **uma única entidade inteligente**, sem perceber as transições entre agentes especializados.

---

##  Estrutura do Projeto

```
Desafio_Dev_Agentes_IA_py/
│
├── app.py                          # Interface Streamlit (UI principal)
├── main.py                         # Interface CLI para testes via terminal
├── print_tools.py                  # Utilitários de formatação para o terminal
├── requirements.txt                # Dependências do projeto
├── .env.example                    # Exemplo de variáveis de ambiente
│
└── banco_agil/                     # Pacote principal
    ├── config.py                   # Configurações globais (caminhos, pesos, modelo LLM)
    │
    ├── agentes/                    # Definição dos agentes de IA
    │   ├── triagem.py              # Agente raiz — autenticação e orquestração
    │   ├── credito.py              # Agente de crédito
    │   ├── entrevista.py           # Agente de entrevista de reavaliação
    │   └── cambio.py               # Agente de câmbio
    │
    ├── ferramentas/                # Ferramentas (functions) chamadas pelos agentes
    │   ├── autenticacao.py         # Validação de CPF e data de nascimento
    │   ├── credito_tools.py        # Consulta de limite e processamento de aumento
    │   ├── score_tools.py          # Cálculo e atualização de score de crédito
    │   ├── cambio_tools.py         # Consulta de cotação via AwesomeAPI
    │   └── sistema_tools.py        # Ferramenta de encerramento de atendimento
    │
    └── dados/                      # Base de dados em CSV
        ├── clientes.csv            # Cadastro de clientes (CPF, score, limite)
        ├── score_limite.csv        # Tabela de faixas de score × limite máximo
        └── solicitacoes_aumento_limite.csv  # Registro de solicitações (gerado em runtime)
```

---

## 🏛️ Arquitetura do Sistema

### Visão Geral

O sistema utiliza o padrão **Orquestrador + Sub-agentes** com o framework **Google ADK (Agent Development Kit)**. O `agente_triagem` atua como **root agent** — ele recebe toda mensagem do usuário, decide quem deve responder e delega silenciosamente ao especialista correto.

```
┌─────────────────────────────────────────────────────┐
│                    Usuário (Chat)                   │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Agente de Triagem (root)               │
│  • Autentica via CPF + data de nascimento           │
│  • Interpreta a intenção do cliente                 │
│  • Delega para o sub-agente correto                 │
│  • Gerencia encerramento de sessão                  │
└──────────┬──────────────┬───────────────────────────┘
           │              │                   │
           ▼              ▼                   ▼
┌──────────────┐ ┌─────────────────┐ ┌──────────────┐
│   Agente de  │ │  Agente de      │ │  Agente de   │
│   Crédito    │ │  Entrevista     │ │  Câmbio      │
│              │ │  de Crédito     │ │              │
│ • Consulta   │ │                 │ │ • Cotação    │
│   de limite  │ │ • 5 perguntas   │ │   em tempo   │
│ • Solicitação│ │   financeiras   │ │   real via   │
│   de aumento │ │ • Cálculo de    │ │   AwesomeAPI │
│ • Análise    │ │   score         │ │              │
│   de score   │ │ • Atualização   │ │              │
│              │ │   do cadastro   │ │              │
└──────────────┘ └─────────────────┘ └──────────────┘
```

### Como os Dados Fluem

1. O usuário digita uma mensagem na interface Streamlit ou no terminal.
2. O `InMemoryRunner` do ADK encaminha a mensagem ao `agente_triagem`.
3. Se não autenticado, a triagem solicita CPF e data de nascimento e chama `autenticar_cliente` — que valida contra o `clientes.csv`.
4. Após autenticação, o agente interpreta a intenção e delega ao sub-agente adequado usando `transfer_to_agent` internamente.
5. O sub-agente executa suas ferramentas (leitura/escrita em CSV, chamada de API) e gera a resposta.
6. O controle retorna ao `agente_triagem`, que permanece em silêncio enquanto houver contexto suficiente ou redireciona novamente conforme necessário.
7. A interface exibe a resposta consolidada ao usuário.

### Persistência de Dados

| Arquivo | Descrição | Operações |
|---|---|---|
| `clientes.csv` | Cadastro de clientes com CPF, score e limite | Leitura na autenticação e consulta; escrita na atualização de score e limite |
| `score_limite.csv` | Tabela de faixas de score × limite máximo permitido | Somente leitura |
| `solicitacoes_aumento_limite.csv` | Registro de cada solicitação de aumento | Criado automaticamente; escrita a cada solicitação com status `pendente` → `aprovado`/`rejeitado` |

---

##  Funcionalidades Implementadas

###  Autenticação (Agente de Triagem)
- Coleta CPF e data de nascimento (na mesma mensagem ou separadamente)
- Valida contra `clientes.csv` com normalização de formatos de data (`DD/MM/AAAA`, `AAAA-MM-DD`, etc.)
- Bloqueia o CPF após **3 tentativas consecutivas falhas**, encerrando o atendimento automaticamente
- Interpreta linguagem natural (ex: "vinte e seis de dezembro de dois mil e três" → `2003-12-26`)

###  Crédito (Agente de Crédito)
- Consulta o limite de crédito atual do cliente sem pedir o CPF novamente (extrai do histórico)
- Processa solicitações de aumento de limite com o seguinte fluxo:
  1. Registra a solicitação em `solicitacoes_aumento_limite.csv` com status `pendente`
  2. Compara o novo limite solicitado com o teto permitido para o score atual (via `score_limite.csv`)
  3. Atualiza o status para `aprovado` ou `rejeitado` e, se aprovado, persiste o novo limite no cadastro
- Se rejeitado, oferece redirecionamento para a entrevista de reavaliação de perfil

###  Entrevista de Crédito (Agente de Entrevista)
- Conduz 5 perguntas financeiras em sequência, uma por vez
- Traduz respostas informais (ex: "CLT", "faço bico", "tô na rua", "5k") para os tipos esperados pela fórmula
- Calcula o novo score com a fórmula ponderada:
  ```
  score = (renda / (despesas + 1)) × 80
        + peso_emprego[tipo]        # formal=300, autônomo=250, desempregado=0
        + peso_dependentes[n]       # 0=100, 1=80, 2=60, 3+=30
        + peso_dividas[tem_dividas] # não=+100, sim=-100
  ```
  O resultado é limitado ao intervalo **[0, 1000]**.
- Atualiza o score no `clientes.csv` e imediatamente tenta novamente a solicitação de aumento
- Respeita desistência do cliente a qualquer momento da entrevista
- Nunca revela a fórmula, os pesos ou o score ao cliente (segredo de negócio)

###  Câmbio (Agente de Câmbio)
- Consulta cotações em tempo real via **AwesomeAPI** (`economia.awesomeapi.com.br`)
- Suporta dólar, euro, libra, iene, bitcoin, peso argentino, franco suíço, dólar canadense e yuan
- Interpreta abreviações e gírias ("dol", "euri", "btc") antes de chamar a API
- Retorna valores de compra, venda, variação percentual, máximo e mínimo do dia
- Trata erros de conexão, timeout e moeda não encontrada sem interromper o atendimento

###  Comportamentos Transversais (todos os agentes)
- **Identidade única:** nenhum agente revela ao cliente que é um agente ou que foi transferido
- **Encerramento controlado:** qualquer agente pode chamar `encerrar_atendimento`, que bloqueia o input na UI e impede novas mensagens
- **Fallback anti-vazio:** o `app.py` detecta respostas vazias do ADK (bug conhecido de reentrada) e dispara um retry forçado com injeção de contexto
- **Sanitização de respostas:** expressões regulares limpam eventuais vazamentos de código ou chamadas de função antes de exibir ao usuário
- **Tratamento de erros:** todas as ferramentas retornam dicionários estruturados com `sucesso: bool` e `mensagem`, permitindo que os agentes informem o cliente de forma clara sem lançar exceções

---

##  Escolhas Técnicas e Justificativas

### Google ADK (Agent Development Kit)
O ADK foi escolhido por oferecer suporte nativo ao padrão **orquestrador + sub-agentes** com `transfer_to_agent`, histórico de conversa automático via `InMemoryRunner`, e integração direta com a Google GenAI. Isso eliminou a necessidade de construir um roteador de agentes do zero, permitindo foco na lógica de negócio.

### LiteLLM + OpenRouter como bridge
O ADK, por padrão, opera com modelos do Google diretamente. Para manter flexibilidade de modelo e evitar lock-in, o projeto usa **LiteLLM** como camada de abstração, apontando para o **OpenRouter** com o modelo `google/gemini-3-flash-preview`. Isso permite trocar de modelo (ex: para GPT-4o ou Claude) com uma única linha de código em `config.py`.

### Prompts com Chain-of-Thought e Few-Shot
Cada agente recebe instruções detalhadas com raciocínio passo a passo explícito e exemplos few-shot cobrindo casos normais, casos limítrofes e situações de erro. Essa abordagem aumentou significativamente a consistência do comportamento — especialmente para as regras de identidade única e roteamento correto entre agentes.

### CSV como base de dados
Optou-se por CSV para máxima portabilidade e facilidade de inspeção. Todas as operações de leitura e escrita são feitas com o módulo `csv` da biblioteca padrão do Python, sem dependências externas de banco de dados. Para um ambiente de produção, a migração para SQLite ou PostgreSQL seria trivial, pois toda a lógica de persistência está isolada em funções auxiliares privadas dentro de cada `_tools.py`.

### Streamlit como interface
O Streamlit foi a escolha natural para a interface por permitir criar um chat funcional com pouquíssimo código, suporte a estado de sessão (`st.session_state`) e execução assíncrona via `asyncio.run`. A interface inclui CSS customizado para uma experiência mais próxima de um produto real, com suporte a dark mode, header bancário e sidebar com status do cliente.

### AwesomeAPI para câmbio
API pública, gratuita, sem necessidade de chave de acesso, com cobertura das principais moedas e retorno em JSON simples. Ideal para um desafio técnico onde a disponibilidade e facilidade de integração são prioritárias.

---

##  Desafios Enfrentados e Como Foram Resolvidos

### 1. Respostas vazias do ADK (bug de reentrada)
**Problema:** Em certos fluxos de transferência entre agentes, o ADK retornava eventos sem conteúdo de texto — especialmente após o agente de entrevista devolver o controle ao root agent.

**Solução:** Implementação de um **fallback anti-vazio** no `app.py`: se a lista de partes de texto coletadas estiver vazia após o run completo, um segundo `run_async` é disparado com uma mensagem de sistema solicitando que o agente reconsidere a solicitação anterior com base no histórico. Isso resolve o loop sem expor o comportamento ao usuário.

### 2. Vazamento de código nas respostas
**Problema:** Ocasionalmente, o modelo gerava respostas que incluíam fragmentos de código Python, chamadas de função ou blocos markdown junto com o texto ao usuário.

**Solução:** A função `_sanitizar_resposta` no `app.py` aplica um conjunto de expressões regulares que remove esses fragmentos antes da exibição, preservando apenas o texto conversacional.

### 3. Manter a identidade única entre agentes
**Problema:** Por padrão, cada sub-agente do ADK pode gerar saudações duplicadas ou revelar que é um "agente diferente", quebrando a experiência de atendimento unificado.

**Solução:** Cada agente recebe instruções explícitas com a regra de **IDENTIDADE ÚNICA** e exemplos few-shot de comportamento correto e incorreto. Além disso, regras de silêncio foram definidas: o `agente_triagem` não gera texto ao devolver o controle após um sub-agente já ter respondido.

### 4. Interpretação de linguagem natural para parâmetros tipados
**Problema:** A ferramenta `calcular_score` exige tipos estritos (`"formal"`, `"autônomo"`, `"desempregado"`, `"sim"`, `"não"`). Usuários reais respondem com "CLT", "faço bico", "tô lascado de dívida", etc.

**Solução:** Dois níveis de normalização: (a) o prompt do agente de entrevista inclui uma tabela detalhada de tradução com exemplos de gírias e regionalismos, instruindo o modelo a converter antes de chamar a ferramenta; (b) a própria função `calcular_score` em `score_tools.py` possui um dicionário de sinônimos como segunda linha de defesa.

### 5. Encerramento de sessão persistente na UI
**Problema:** Após o encerramento do atendimento, o campo de input do Streamlit continuava ativo, permitindo que o usuário enviasse mensagens para uma sessão já finalizada.

**Solução:** O `app.py` monitora a flag `atendimento_encerrado` no `st.session_state`. Quando ativada (detectada pela chamada à ferramenta `encerrar_atendimento` nos logs de eventos do ADK), o input é substituído por um banner informativo e um `st.rerun()` é disparado para atualizar a interface imediatamente.

---

##  Tutorial de Execução

### Pré-requisitos

- Python 3.11 ou superior
- Conta no [OpenRouter](https://openrouter.ai/) com créditos disponíveis (o modelo `google/gemini-3-flash-preview` possui tier gratuito)

### 1. Clone o repositório

```bash
git clone https://github.com/Lucas-B-Iori/Desafio_Dev_Agentes_IA_py.git
cd Desafio_Dev_Agentes_IA_py
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Abra o arquivo `.env` e preencha com sua chave do OpenRouter:

```env
OPENROUTER_API_KEY=sua_chave_openrouter_aqui
```

### 5. Execute a aplicação

**Interface Streamlit (recomendado):**
```bash
streamlit run app.py
```
Acesse `http://localhost:8501` no navegador.

**Interface CLI (para testes rápidos):**
```bash
python main.py
```

---

##  Testando o Sistema

### Clientes disponíveis na base de dados

| Nome | CPF | Data de Nascimento | Score | Limite Atual |
|---|---|---|---|---|
| Maria Silva | 12345678901 | 15/05/1990 | 549 | R$ 20.000,00 |
| João Santos | 98765432100 | 20/11/1985 | 400 | R$ 2.000,00 |
| Ana Oliveira | 11122233344 | 10/03/2000 | 600 | R$ 3.500,00 |
| Carlos Pereira | 55566677788 | 25/08/1978 | 850 | R$ 15.000,00 |
| Fernanda Lima | 99988877766 | 30/01/1995 | 200 | R$ 1.000,00 |
| Lucas Iori | 49568404899 | 26/12/2003 | 1000 | R$ 20.000,00 |

### Roteiros de teste sugeridos

**Fluxo completo de aumento de limite com entrevista:**
1. Informe CPF e data de nascimento de João Santos
2. Solicite um aumento de limite para R$ 10.000
3. Quando rejeitado, aceite a reavaliação de perfil
4. Responda as 5 perguntas financeiras
5. Verifique o novo resultado

**Fluxo de câmbio:**
1. Autentique-se com qualquer cliente
2. Pergunte: "quanto tá o dólar hoje?"
3. Em seguida: "e o euro?"
4. Mude de assunto: "qual meu limite de crédito?"

**Teste de bloqueio de segurança:**
1. Informe um CPF válido com data errada 3 vezes consecutivas
2. Verifique o bloqueio e o encerramento automático

**Teste de encerramento:**
1. Em qualquer momento após a autenticação, diga "tchau" ou "encerrar"
2. Verifique que o input some e o banner de sessão encerrada aparece

---

##  Dependências

| Pacote | Versão | Uso |
|---|---|---|
| `google-adk` | ≥ 1.0.0 | Framework principal de agentes |
| `google-genai` | ≥ 1.0.0 | SDK Google GenAI |
| `litellm` | ≥ 1.40.0 | Bridge entre ADK e OpenRouter |
| `streamlit` | ≥ 1.30.0 | Interface web de chat |
| `requests` | ≥ 2.31.0 | Chamadas HTTP para a AwesomeAPI |
| `python-dotenv` | ≥ 1.0.0 | Carregamento de variáveis de ambiente |

---

##  Autor

**Lucas B. Iori**  
Desafio Técnico — Desenvolvedor de Agentes de IA (Python) 
