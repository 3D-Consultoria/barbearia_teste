{{ config(materialized='view') }}

SELECT
    TRY_CAST(id AS INTEGER) as venda_id,
    TRY_CAST(id_cliente AS INTEGER) as cliente_id,
    -- Trata data de venda DD/MM/YYYY
    try_strptime(data_venda, '%d/%m/%Y')::DATE as data_venda,
    LOWER(TRIM(tipo_venda)) as servico, 
    TRY_CAST(valor AS DECIMAL(10,2)) as valor_faturamento
FROM read_csv_auto('../data/raw_vendas.csv', all_varchar=True)