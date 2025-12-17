{{ config(materialized='table') }}

WITH source_data AS (
    -- Lê o CSV garantindo que tudo seja texto inicialmente para evitar erros de leitura
    SELECT * FROM read_csv_auto('../data/raw_customers.csv', all_varchar=True)
),

cleaned_data AS (
    SELECT
        -- Tenta converter ID, se falhar usa nulo
        TRY_CAST(ID AS INTEGER) as cliente_id,
        
        -- CORREÇÃO AQUI: Usamos UPPER (Maiúsculo) pois DuckDB não tem INITCAP nativo
        TRIM(UPPER(COALESCE(Nome, 'Cliente Desconhecido'))) as nome_cliente,
        
        -- Tratamento de Data: Tenta converter DD/MM/YYYY
        -- O try_strptime retorna NULL se falhar, não quebrando o pipeline
        try_strptime(Nascimento, '%d/%m/%Y')::DATE as data_nascimento_dt
    FROM source_data
)

SELECT
    cliente_id,
    nome_cliente,
    data_nascimento_dt,
    
    -- Cálculos de Negócio
    DATE_DIFF('year', data_nascimento_dt, CURRENT_DATE) as idade,
    
    CASE 
        WHEN idade < 18 THEN 'JOVEM (<18)'
        WHEN idade BETWEEN 18 AND 25 THEN 'JOVEM ADULTO (18-25)'
        WHEN idade BETWEEN 26 AND 40 THEN 'ADULTO (26-40)'
        WHEN idade > 40 THEN 'SENIOR (40+)'
        ELSE 'NAO IDENTIFICADO'
    END as faixa_etaria,
    
    -- Flag de Aniversariante (True/False)
    (MONTH(data_nascimento_dt) = MONTH(CURRENT_DATE)) as is_aniversariante_mes,
    
    CURRENT_DATE as data_ref_carga

FROM cleaned_data
WHERE nome_cliente IS NOT NULL