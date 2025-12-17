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
- **Tipo**: Google Sheets (planilha compartilhada)
- **ID da Planilha**: `1f655JLEQiOxSB0uKFRv9Ds9-00rAVNP2qTfeXRbSgq4`
- **Estrutura mínima obrigatória**:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| ID | Número | Identificador único | 1, 2, 3 |
| Nome | Texto | Nome completo do cliente | João Silva |
| Nascimento | Data | Data de nascimento (DD/MM/YYYY) | 15/03/1990 |

### Colunas Adicionais (Opcional)
Se a planilha contiver mais colunas, elas serão ignoradas. Para usá-las, modifique o SQL em `mart_clientes.sql`.

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

### Passo 3: Atualizar ID da Planilha

No arquivo `src/extract.py`, procure:

```python
SHEET_ID = "1f655JLEQiOxSB0uKFRv9Ds9-00rAVNP2qTfeXRbSgq4"
```

Substitua pelo novo:

```python
SHEET_ID = "seu-novo-id-aqui"
```

---

### Passo 4: Validar Modelo DBT (Se Necessário)

Se o novo cliente tiver **estrutura de dados diferente**, modifique `dbt_project/models/mart_clientes.sql`:

#### Exemplo: Cliente com coluna diferente
```sql
-- ANTES (padrão):
TRIM(INITCAP(COALESCE(Nome, 'Cliente Desconhecido'))) as nome_cliente

-- DEPOIS (se a coluna chama "Client_Name"):
TRIM(INITCAP(COALESCE(Client_Name, 'Cliente Desconhecido'))) as nome_cliente
```

#### Exemplo: Formato de data diferente
```sql
-- ANTES (DD/MM/YYYY):
TRY_CAST(strptime(Nascimento, '%d/%m/%Y') AS DATE)

-- DEPOIS (YYYY-MM-DD):
TRY_CAST(strptime(Nascimento, '%Y-%m-%d') AS DATE)
```

---

### Passo 5: Rodar Pipeline

```bash
# 1. Extrair
python src/extract.py

# 2. Transformar
dbt run --project-dir dbt_project

# 3. Enviar
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
- [ ] Criar planilha Google Sheets com dados
- [ ] Copiar ID da planilha
- [ ] Atualizar `SHEET_ID` em `extract.py`
- [ ] Validar estrutura de dados (executar `python src/extract.py`)
- [ ] Ajustar SQL em `mart_clientes.sql` se colunas forem diferentes
- [ ] Testar DBT: `dbt run --project-dir dbt_project`
- [ ] Customizar prompt da IA (opcional)
- [ ] Executar pipeline completo
- [ ] Validar email recebido

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
- Verifique se os nomes em `mart_clientes.sql` correspondem ao CSV
- Execute: `head -1 data/raw_customers.csv` para ver nomes reais

### Erro: "Data inválida"
- Valide o formato esperado em `strptime()`
- Execute: `dbt test --project-dir dbt_project`

### Erro: "Nenhum cliente para analisar"
- Verifique se a planilha tem dados
- Confirm que as 3 colunas obrigatórias existem

---

## 📞 Suporte

Para novos clientes ou dúvidas:
1. Consulte o [README.md](README.md) para aspectos técnicos
2. Revise este arquivo para customizações
3. Verifique exemplos em `CONFIG_CLIENTE.json` e `src/extract.py`
