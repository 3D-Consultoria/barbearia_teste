{{ config(materialized='view') }}

SELECT
    TRY_CAST(id AS INTEGER) as cliente_id,
    UPPER(TRIM(nome)) as nome,
    try_strptime(data_nascimento, '%d/%m/%Y')::DATE as data_nascimento,
    UPPER(TRIM(bairro)) as bairro,
    UPPER(TRIM(cidade)) as cidade,
    UPPER(TRIM(sexo)) as sexo
-- MUDANÇA AQUI: Lendo direto da tabela raw carregada pelo Python
FROM raw_clientes