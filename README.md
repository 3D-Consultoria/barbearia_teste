# Sistema de Análise de Clientes - Arquitetura Técnica

Um pipeline automatizado de análise de dados que extrai informações de clientes, processa com DBT e entrega insights por email usando IA. Desenvolvido como template reutilizável para diferentes clientes.

---

## 🏗️ Arquitetura

```
Google Sheets (Fonte) 
    ↓
Extract (Python) 
    ↓
CSV Raw (data/raw_customers.csv)
    ↓
DBT Transformations (DuckDB)
    ↓
Data Mart (mart_clientes)
    ↓
OpenAI + Email (Distribuição)
```

---

## 📦 Stack Técnico

| Camada | Ferramenta | Função |
|--------|-----------|--------|
| **Ingestão** | Python + Pandas | Extração de dados |
| **Transformação** | DBT + DuckDB | Limpeza e cálculo de métricas |
| **Armazenamento** | DuckDB | Banco de dados em memória/arquivo |
| **IA/Análise** | OpenAI (GPT-4o-mini) | Geração de insights |
| **Distribuição** | Yagmail | Envio de emails |

---

## 🗂️ Estrutura do Projeto

```
.
├── CONFIG_CLIENTE.json              # Configuração do cliente (não versione dados sensíveis)
├── CLIENTE.md                        # Guia de cliente e customização
├── README.md                         # Este arquivo (arquitetura técnica)
├── requirements.txt                 # Dependências Python
│
├── dbt_project/                      # Transformação de dados (DBT)
│   ├── dbt_project.yml               # Configuração DBT
│   ├── profiles.yml                  # Credenciais e conexões
│   └── models/
│       └── mart_clientes.sql         # Model principal - transformações
│
├── src/                              # Scripts Python
│   ├── extract.py                    # Extração Google Sheets → CSV
│   └── send_email.py                 # Análise IA + Distribuição
│
└── data/                             # Diretório de dados (gitignored)
    └── raw_customers.csv             # Dados brutos extraídos
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

### Extract (extract.py)
- Conecta ao Google Sheets via `read_csv(URL)`
- Valida dados básicos
- Salva em `data/raw_customers.csv`
- Sem transformações (raw data)

### Transform (DBT)
- **Leitura**: `read_csv_auto()` do DuckDB
- **Limpeza**: Padronização de nomes e datas
- **Enriquecimento**: Cálculo de idade, faixa etária, aniversariantes
- **Saída**: Tabela `mart_clientes` (view ou table)

### Load (send_email.py)
- Consulta dados em DuckDB
- Calcula métricas (total, média, faixa principal)
- Envia para OpenAI com contexto do cliente
- Recebe insight e distribui por email

---

## 🗄️ Banco de Dados

### DuckDB
- **Tipo**: SQLite-like em memória/arquivo
- **Vantagem**: Sem setup, suporta Parquet/CSV nativo
- **Alternativas**: PostgreSQL, BigQuery, Snowflake (alterar `profiles.yml`)

### Modelo: mart_clientes

```sql
cliente_id          (INTEGER)
nome_cliente        (VARCHAR)
data_nascimento_dt  (DATE)
idade               (INTEGER)
faixa_etaria        (VARCHAR)
is_aniversariante_mes (BOOLEAN)
data_ref_carga      (DATE)
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
python src/extract.py && dbt run --project-dir dbt_project && python src/send_email.py
```

### Automatizado (Cron)
```bash
# Executar todos os dias às 8:00 AM
0 8 * * * cd /path/to/project && /usr/bin/python3 src/extract.py && dbt run --project-dir dbt_project && python3 src/send_email.py
```

### Docker (Opcional)
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD python src/extract.py && dbt run --project-dir dbt_project && python src/send_email.py
```

---

## 🔐 Segurança & Boas Práticas

- ✅ Não commite `CONFIG_CLIENTE.json` se contiver dados sensíveis
- ✅ Use `.env` para variáveis de ambiente
- ✅ Gitignore: `data/`, `.env`, `logs/`
- ✅ Valide dados de entrada (CSV)
- ✅ Rate limit da API OpenAI

---

## 🧪 Testes & Debugging

### Testar Extração
```bash
python -c "from src.extract import run_extraction; run_extraction()"
```

### Testar DBT
```bash
dbt run --project-dir dbt_project --select mart_clientes
dbt test --project-dir dbt_project
```

### Testar IA
```python
from src.send_email import get_ai_analysis
metricas = {"total": 100, "idade_media": 35, "faixa_principal": "Adulto", "aniversariantes": 5}
print(get_ai_analysis(metricas))
```

---

## 📚 Referências

- [DBT Docs](https://docs.getdbt.com/)
- [DuckDB Docs](https://duckdb.org/docs/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Yagmail](https://github.com/kootenpush/yagmail)

---