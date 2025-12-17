{{ config(materialized='table') }}

WITH clientes as ( select * from {{ ref('stg_clientes') }} ),
vendas as ( select * from {{ ref('stg_vendas') }} )

SELECT
    c.cliente_id,
    c.nome,
    c.bairro,
    
    -- Métricas de Negócio
    COUNT(v.venda_id) as frequencia_visitas,
    SUM(v.valor_faturamento) as total_gasto_ltv,
    MAX(v.data_venda) as ultima_visita,
    
    -- Dias sem aparecer (Recência)
    DATE_DIFF('day', MAX(v.data_venda), CURRENT_DATE) as dias_desde_ultima_visita,
    
    -- Idade do Cliente
    DATE_DIFF('year', c.data_nascimento, CURRENT_DATE) as idade

FROM clientes c
LEFT JOIN vendas v ON c.cliente_id = v.cliente_id
GROUP BY c.cliente_id, c.nome, c.bairro, c.data_nascimento