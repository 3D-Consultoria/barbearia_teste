# Sistema de Análise de Clientes - Arquitetura Técnica

Um pipeline automatizado de análise de dados que extrai informações de clientes, processa com DBT e entrega insights por email usando IA. Desenvolvido como template reutilizável para diferentes clientes.

---

## 🏗️ Arquitetura

```
Google Sheets (Clientes + Vendas)
    ↓
Extract (Python + DuckDB)
    ↓
MotherDuck Database (raw_clientes, raw_vendas)
    ↓
DBT Transformations (stg_* → mart_*)
    ↓
Data Marts (Clientes, Vendas, Financeiro, Dashboard)
    ↓
OpenAI + Email (Relatório + Distribuição)
    ↓
GitHub Actions (Daily Pipeline)
```

---

## 📦 Stack Técnico

| Camada | Ferramenta | Função |
|--------|-----------|--------|
| **Ingestão** | Python + Pandas + DuckDB | Extração e load de dados |
| **Cloud Data** | MotherDuck | Data warehouse serverless |
| **Transformação** | DBT | Limpeza, staging e data marts |
| **IA/Análise** | OpenAI (GPT-4o-mini) | Geração de insights |
| **Distribuição** | Yagmail | Envio de emails |
| **Orquestração** | GitHub Actions | Pipeline automatizada (daily) |

---

## 🗂️ Estrutura do Projeto

```
.
├── CONFIG_CLIENTE.json              # Configuração do cliente
├── CLIENTE.md                        # Guia de cliente e customização
├── README.md                         # Este arquivo (arquitetura técnica)
├── requirements.txt                 # Dependências Python
│
├── .github/
│   └── workflows/
│       └── daily_pipeline.yml        # CI/CD - Pipeline automatizado (GitHub Actions)
│
├── dbt_project/                      # Transformação de dados (DBT)
│   ├── dbt_project.yml               # Configuração DBT
│   ├── profiles.yml                  # Credenciais MotherDuck
│   └── models/
│       ├── stg_clientes.sql          # Staging: Limpeza clientes
│       ├── stg_vendas.sql            # Staging: Limpeza vendas
│       ├── mart_dashboard.sql        # Data Mart: Dashboard cliente
│       └── mart_financeiro.sql       # Data Mart: Relatório financeiro
│
└── src/                              # Scripts Python
    ├── extract.py                    # Ingestão Google Sheets → MotherDuck
    ├── send_email.py                 # Análise IA + Distribuição
    └── notifications.py              # Alertas Telegram (opcional)
```

---

## 🔧 Instalação & Setup

### 1. Clonar e Instalar Dependências
```bash
git clone <repo>
cd barbearia_teste
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
export OPENAI_API_KEY="sk-..."
export YAGMAIL_EMAIL="seu-email@gmail.com"
export YAGMAIL_PASSWORD="senha-app-google"
```

### 3. Validar DBT
```bash
dbt debug --project-dir dbt_project
```

---

## ▶️ Executar Pipeline

```bash
# 1. Extrair dados
python src/extract.py

# 2. Transformar (DBT)
dbt run --project-dir dbt_project

# 3. Enviar análise
python src/send_email.py
```

Ou tudo de uma vez:
```bash
python src/extract.py && dbt run --project-dir dbt_project && python src/send_email.py
```

---

## 📊 Fluxo de Dados

### 1. Extract (extract.py)
- Conecta a Google Sheets (2 abas: Clientes + Vendas)
- Autentica no MotherDuck com token
- Cria banco `barbearia_db` (caso não exista)
- Faz load das abas em tabelas raw:
  - `raw_clientes`: ID, Nome, Data_Nascimento, Bairro, Cidade, Sexo
  - `raw_vendas`: ID, ID_Cliente, Data_Venda, Tipo_Venda, Valor
- Envia alertas Telegram (opcional)

### 2. Transform (DBT)
Executa em 2 camadas:

**Staging (stg_*)**:
- `stg_clientes`: Limpeza e tipagem (nomes em UPPER, datas parseadas)
- `stg_vendas`: Limpeza de vendas (valores decimal, datas parseadas)

**Marts (mart_*)**:
- `mart_dashboard`: Join clientes + vendas, cálculo de LTV, frequência, recência
- `mart_financeiro`: Agregado de faturamento, ticket médio, serviço mais vendido

### 3. Load (send_email.py)
- Consulta `mart_dashboard` e `mart_financeiro` no MotherDuck
- Calcula métricas de aniversariantes do mês
- Envia para OpenAI com contexto do cliente
- Distribui relatório por email

---

## 🗄️ Banco de Dados

### MotherDuck
- **Tipo**: Data warehouse serverless (DuckDB on cloud)
- **Autenticação**: Token via `MOTHERDUCK_TOKEN`
- **Vantagem**: Sem infraestrutura, escalável, grátis para pequenos volumes
- **Conexão**: `duckdb.connect('md:?token=...')`

### Tabelas Raw (Ingestão)
```
raw_clientes: ID, Nome, Data_Nascimento, Bairro, Cidade, Sexo
raw_vendas:   ID, ID_Cliente, Data_Venda, Tipo_Venda, Valor
```

### Tabelas Staging (Transformação DBT)
```
stg_clientes: cliente_id, nome, data_nascimento, bairro, cidade, sexo
stg_vendas:   venda_id, cliente_id, data_venda, servico, valor_faturamento
```

### Data Marts (Análise)
```
mart_dashboard:
  - cliente_id, nome, bairro
  - frequencia_visitas, total_gasto_ltv, ultima_visita
  - dias_desde_ultima_visita, idade

mart_financeiro:
  - faturamento_total, ticket_medio
  - servico_mais_vendido, total_vendas
```

---

## 🤖 Integração OpenAI

**Modelo**: `gpt-4o-mini`

**Contexto enviado**:
- Configuração do cliente (tom de voz, objetivo)
- Métricas do dia (total, idade média, faixa etária)
- Regras (priorizar aniversariantes)

**Resposta esperada**: 1 insight acionável em 3 linhas

---

## 📧 Distribuição

**Ferramenta**: Yagmail (SMTP Gmail)

**Requerimentos**:
- Gmail com 2FA ativo
- Gerar App Password (não use senha do Gmail diretamente)

**Variáveis necessárias**:
```
YAGMAIL_EMAIL=seu-email@gmail.com
YAGMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

---

## 🚀 Deploy

### Local (Desenvolvimento)
```bash
# Sem CI/CD, rodar manual
export MOTHERDUCK_TOKEN="seu-token"
export OPENAI_API_KEY="sk-..."
export TELEGRAM_TOKEN="..."
export EMAIL_USER="..."
export EMAIL_PASS="..."

python src/extract.py && dbt run --project-dir dbt_project && python src/send_email.py
```

### GitHub Actions (Produção)
Configurado em `.github/workflows/daily_pipeline.yml`

**Triggers**:
- Manual: `workflow_dispatch` (rodar na aba Actions)
- Automático: Diariamente às 11:00 UTC (`cron: '0 11 * * *'`)

**Secrets Necessários**:
- `MOTHERDUCK_TOKEN`: Token MotherDuck
- `OPENAI_API_KEY`: Chave OpenAI
- `EMAIL_USER`: Email para enviar relatórios
- `EMAIL_PASS`: Senha app do Gmail
- `TELEGRAM_TOKEN`: Token bot Telegram (opcional)
- `TELEGRAM_CHAT_ID`: ID chat Telegram (opcional)

**Etapas**:
1. Checkout do código
2. Setup Python 3.9
3. Install dependências
4. Extract (Python + MotherDuck)
5. Transform (dbt run)
6. Load & Notify (Email + Telegram)

---

## 🔐 Segurança & Boas Práticas

- ✅ Nunca commite `MOTHERDUCK_TOKEN`, `OPENAI_API_KEY`, credenciais de email
- ✅ Use GitHub Secrets para credenciais em CI/CD
- ✅ Use `.env` local para desenvolvimento (não commite)
- ✅ Gitignore: `.env`, `data/`, `logs/`, `*.duckdb`
- ✅ Valide dados de entrada (ID, datas, valores)
- ✅ Implementar rate limit da API OpenAI
- ✅ Logs sensíveis não devem conter tokens

---

## 🧪 Testes & Debugging

### Testar Conexão MotherDuck
```bash
export MOTHERDUCK_TOKEN="seu-token"
python -c "import duckdb; con = duckdb.connect('md:?token=$MOTHERDUCK_TOKEN'); print(con.sql('SELECT 1'))"
```

### Testar Extração
```bash
export MOTHERDUCK_TOKEN="..."
export TELEGRAM_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python src/extract.py
```

### Testar DBT
```bash
cd dbt_project
dbt debug --profiles-dir .
dbt run --profiles-dir . --select stg_clientes
dbt run --profiles-dir . --select mart_dashboard
```

### Testar Pipeline Completa
```bash
export MOTHERDUCK_TOKEN="..."
export OPENAI_API_KEY="sk-..."
export EMAIL_USER="..."
export EMAIL_PASS="..."
python src/extract.py && cd dbt_project && dbt run --profiles-dir . && cd .. && python src/send_email.py
```

---

## 📚 Referências

- [MotherDuck Docs](https://motherduck.com/docs/)
- [DBT Docs](https://docs.getdbt.com/)
- [DuckDB Docs](https://duckdb.org/docs/)
- [OpenAI API](https://platform.openai.com/docs/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Yagmail](https://github.com/kootenpush/yagmail)

---