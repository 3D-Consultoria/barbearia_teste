{{ config(materialized='table') }}

SELECT
    SUM(valor_faturamento) as faturamento_total,
    AVG(valor_faturamento) as ticket_medio,
    MODE(servico) as servico_mais_vendido,
    COUNT(*) as total_vendas
FROM {{ ref('stg_vendas') }}