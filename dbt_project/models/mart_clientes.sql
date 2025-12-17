{{ config(materialized='table') }}

WITH source_data AS (
    -- Lê o CSV cru. O DuckDB é inteligente para inferir tipos, mas forçamos strings para segurança
    SELECT * FROM read_csv_auto('../data/raw_customers.csv', all_varchar=True)
),

cleaned_data AS (
    SELECT
        -- Tenta converter ID, se falhar usa nulo
        TRY_CAST(ID AS INTEGER) as cliente_id,
        
        -- Limpeza de Nome: Remove espaços extras e coloca em Title Case (Ex: "JOAO SILVA" -> "Joao Silva")
        -- Obs: Assumindo que a coluna chama 'Nome' ou 'Cliente'. Ajuste o coalesce se necessário.
        TRIM(INITCAP(COALESCE(Nome, 'Cliente Desconhecido'))) as nome_cliente,
        
        -- Tratamento de Data: Tenta converter DD/MM/YYYY ou YYYY-MM-DD
        TRY_CAST(strptime(Nascimento, '%d/%m/%Y') AS DATE) as data_nascimento_dt
    FROM source_data
)

SELECT
    cliente_id,
    nome_cliente,
    data_nascimento_dt,
    
    -- --- CÁLCULO DE MÉTRICAS (Regra de Negócio no Banco) ---
    
    -- 1. Idade Atual (DuckDB date functions)
    DATE_DIFF('year', data_nascimento_dt, CURRENT_DATE) as idade,
    
    -- 2. Faixa Etária (Para segmentação de marketing)
    CASE 
        WHEN idade < 18 THEN 'Jovem (<18)'
        WHEN idade BETWEEN 18 AND 25 THEN 'Jovem Adulto (18-25)'
        WHEN idade BETWEEN 26 AND 40 THEN 'Adulto (26-40)'
        WHEN idade > 40 THEN 'Senior (40+)'
        ELSE 'Não Identificado'
    END as faixa_etaria,
    
    -- 3. É aniversariante do mês atual? (True/False)
    (MONTH(data_nascimento_dt) = MONTH(CURRENT_DATE)) as is_aniversariante_mes,
    
    -- 4. Data de Cadastro (Simulada para métrica de "Novos Clientes")
    -- Num banco real, isso viria da coluna 'created_at'
    CURRENT_DATE as data_ref_carga

FROM cleaned_data
WHERE nome_cliente IS NOT NULL