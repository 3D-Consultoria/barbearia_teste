# Guia de Cliente & Customização

Este arquivo documenta informações específicas de cada cliente, regras de negócio e como adaptar o sistema para novos clientes.

---

## 📌 Informações do Cliente Atual

### Configuração Base (CONFIG_CLIENTE.json)

```json
{
    "nome_empresa": "Barbearia Teste",
    "tipo_negocio": "Barbearia Clássica",
    "foco_estrategico": "Fidelização e recorrência mensal.",
    "tom_de_voz": "Profissional e motivador."
}
```

**Descrição**: 
- Cliente de serviços de barbearia
- Objetivo: Aumentar cliente recorrente (mensal)
- Comunicação: Tom motivador e profissional

---

## 📊 Dados do Cliente

### Fonte de Dados
- **Tipo**: Google Sheets (múltiplas abas - Clientes e Vendas)
- **ID da Planilha**: `1f655JLEQiOxSB0uKFRv9Ds9-00rAVNP2qTfeXRbSgq4`
- **Database**: MotherDuck (serverless DuckDB)

### Estrutura - Aba Clientes (gid=0)

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| ID | Número | Identificador único | 1, 2, 3 |
| Nome | Texto | Nome completo do cliente | João Silva |
| Data_Nascimento | Data | Data de nascimento (DD/MM/YYYY) | 15/03/1990 |
| Bairro | Texto | Bairro do cliente | Centro |
| Cidade | Texto | Cidade | São Paulo |
| Sexo | Texto | Sexo (M/F) | M |

### Estrutura - Aba Vendas (gid=48884415)

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| ID | Número | ID da venda | 1, 2, 3 |
| ID_Cliente | Número | Referência ao cliente | 1 |
| Data_Venda | Data | Data da venda (DD/MM/YYYY) | 15/12/2025 |
| Tipo_Venda | Texto | Tipo de serviço | Corte Clássico |
| Valor | Decimal | Valor da venda | 50.00 |

---

## 🎯 Regras de Negócio

### Segmentação de Clientes
```sql
Jovem (<18)              → Marketing focado em trends, promoções
Jovem Adulto (18-25)    → Primeira vez, experiência/testes
Adulto (26-40)          → Cliente recorrente principal
Senior (40+)            → Serviços premium, conforto
```

### Eventos Especiais
- **Aniversariantes do mês**: Prioridade máxima
  - Ação sugerida: Cupom desconto/brinde
  - Segue campo: `is_aniversariante_mes`

---

## 🔄 Como Adaptar para Novo Cliente

### Passo 1: Atualizar CONFIG_CLIENTE.json

```json
{
    "nome_empresa": "Nova Clínica Odontológica",
    "tipo_negocio": "Odontologia",
    "foco_estrategico": "Retorno de pacientes com manutenção preventiva.",
    "tom_de_voz": "Empático e informativo."
}
```

**O quê mudar**:
- `nome_empresa`: Nome exato do negócio
- `tipo_negocio`: Segmento/vertical
- `foco_estrategico`: Objetivo de negócio (para o prompt da IA)
- `tom_de_voz`: Como a IA deve se comunicar

---

### Passo 2: Preparar Dados do Novo Cliente

1. Crie uma **nova planilha Google Sheets** (ou use existente)
2. Garanta as 3 colunas obrigatórias:
   - `ID` (número único)
   - `Nome` (texto)
   - `Nascimento` (formato DD/MM/YYYY)
3. Compartilhe a planilha como **"Qualquer pessoa com o link pode visualizar"**
4. Copie o ID da planilha da URL:
   ```
   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
                                           ^^^^^^^^^
   ```

---

### Passo 3: Atualizar IDs das Planilhas

No arquivo `src/extract.py`, procure:

```python
SHEET_ID = "1f655JLEQiOxSB0uKFRv9Ds9-00rAVNP2qTfeXRbSgq4"

# Aba Clientes (Geralmente gid=0 se for a primeira)
URL_CLIENTES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# Aba Vendas (Pegue o número do GID na URL: #gid=987654321)
GID_VENDAS = "48884415" 
URL_VENDAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_VENDAS}"
```

Substitua pelo novo:

```python
SHEET_ID = "novo-sheet-id-aqui"
URL_CLIENTES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
GID_VENDAS = "novo-gid-vendas" 
URL_VENDAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_VENDAS}"
```

---

### Passo 4: Validar Modelo DBT (Se Necessário)

Se o novo cliente tiver **estrutura de dados diferente**, modifique `dbt_project/models/stg_clientes.sql` e `dbt_project/models/stg_vendas.sql`:

#### Exemplo: Colunas diferentes em stg_clientes.sql
```sql
-- ANTES (padrão):
SELECT
    TRY_CAST(id AS INTEGER) as cliente_id,
    UPPER(TRIM(nome)) as nome,
    try_strptime(data_nascimento, '%d/%m/%Y')::DATE as data_nascimento,
    UPPER(TRIM(bairro)) as bairro
FROM raw_clientes

-- DEPOIS (se coluna chama "Nome_Cliente"):
SELECT
    TRY_CAST(id AS INTEGER) as cliente_id,
    UPPER(TRIM(Nome_Cliente)) as nome,
    try_strptime(Data_Nasc, '%d/%m/%Y')::DATE as data_nascimento,
    UPPER(TRIM(bairro)) as bairro
FROM raw_clientes
```

#### Validar Staging após mudanças
```bash
dbt run --project-dir dbt_project --select stg_clientes,stg_vendas
```

---

### Passo 5: Rodar Pipeline

```bash
# Configurar variáveis
export MOTHERDUCK_TOKEN="seu-token"
export OPENAI_API_KEY="sk-..."
export EMAIL_USER="seu-email@gmail.com"
export EMAIL_PASS="senha-app"

# 1. Extrair
python src/extract.py

# 2. Transformar (DBT)
cd dbt_project
dbt run --profiles-dir .
cd ..

# 3. Enviar relatório
python src/send_email.py
```

---

## 📧 Customizar Análise de IA

O prompt que a IA recebe está em `src/send_email.py`. Para adaptar:

```python
system_prompt = f"""
Você é um Consultor Estratégico da 3D Consultoria para a {CONFIG_CLIENTE['nome_empresa']}.
Foco: {CONFIG_CLIENTE['foco_estrategico']}

Analise os KPIs abaixo e dê 1 (UM) insight curto (máx 3 linhas) para o dono agir hoje.
"""

user_prompt = f"""
MÉTRICAS DO DIA ({datetime.now().strftime('%d/%m/%Y')}):
- Total Clientes: {metricas['total']}
- Idade Média: {metricas['idade_media']} (Público principal: {metricas['faixa_principal']})
- Aniversariantes Mês: {metricas['aniversariantes']}

REGRA:
- Se houver aniversariantes, sugira ação para eles.
- Senão, foque na faixa etária predominante.
"""
```

**Customizações comuns**:

1. **Adicionar métrica**: Calcule em DBT → Passe para `metricas` → Inclua no `user_prompt`
2. **Mudar regra**: Edite a seção `REGRA:`
3. **Mudar modelo IA**: Altere `model="gpt-4o-mini"` para `gpt-4` ou `gpt-3.5-turbo`

---

## 📋 Checklist: Migração para Novo Cliente

- [ ] Atualizar `CONFIG_CLIENTE.json`
- [ ] Criar planilha Google Sheets com 2 abas (Clientes + Vendas)
- [ ] Preencher abas com estrutura correta (ID, Nome, Data_Nascimento, etc.)
- [ ] Copiar SHEET_ID da URL
- [ ] Encontrar GID de cada aba (Clientes=0, Vendas=XXXX)
- [ ] Atualizar `SHEET_ID` e `GID_VENDAS` em `extract.py`
- [ ] Testar extração: `python src/extract.py`
- [ ] Ajustar SQL em `stg_clientes.sql` e `stg_vendas.sql` se colunas forem diferentes
- [ ] Testar DBT: `cd dbt_project && dbt run --profiles-dir .`
- [ ] Customizar prompt da IA em `send_email.py` (opcional)
- [ ] Executar pipeline completa
- [ ] Validar email recebido com relatório
- [ ] Configurar secrets no GitHub Actions (se usar CI/CD)
- [ ] Agendar pipeline automática em GitHub Actions

---

## 💾 Backup & Versionamento

Ao trabalhar com múltiplos clientes:

```bash
# Criar branch por cliente
git checkout -b cliente/nova-clinica

# Commits separados
git add CONFIG_CLIENTE.json
git commit -m "Configuração: Nova Clínica Odontológica"

git add src/extract.py
git commit -m "Update: SHEET_ID para Nova Clínica"

git push origin cliente/nova-clinica
```

---

## 🆘 Troubleshooting

### Erro: "Coluna não encontrada"
- Verifique se os nomes em `stg_clientes.sql` e `stg_vendas.sql` correspondem ao CSV do Google Sheets
- Execute e verifique se `raw_clientes` e `raw_vendas` foram criadas corretamente
- Dica: Veja os nomes exatos digitando na Query: `SELECT * FROM raw_clientes LIMIT 1`

### Erro: "Data inválida"
- Valide o formato esperado em `try_strptime()`
- Comum: DD/MM/YYYY vs YYYY-MM-DD
- Execute: `dbt run --project-dir dbt_project --profiles-dir . --select stg_clientes`

### Erro: "Token MotherDuck inválido"
- Confirme que `MOTHERDUCK_TOKEN` está configurado corretamente
- Regenere o token em https://motherduck.com/

### Erro: "Nenhum cliente/venda para analisar"
- Verifique se as abas tem dados no Google Sheets
- Confirme que GID (gid=0 para clientes, gid=XXXX para vendas) estão corretos

---

## 📞 Suporte

Para novos clientes ou dúvidas:
1. Consulte o [README.md](README.md) para aspectos técnicos
2. Revise este arquivo para customizações
3. Verifique exemplos em `CONFIG_CLIENTE.json` e `src/extract.py`
