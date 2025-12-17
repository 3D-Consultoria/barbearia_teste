{{ config(materialized='view') }}

SELECT
    TRY_CAST(id AS INTEGER) as cliente_id,
    UPPER(TRIM(nome)) as nome,
    -- Trata data de nascimento DD/MM/YYYY
    try_strptime(data_nascimento, '%d/%m/%Y')::DATE as data_nascimento,
    UPPER(TRIM(bairro)) as bairro,
    UPPER(TRIM(cidade)) as cidade,
    UPPER(TRIM(sexo)) as sexo
FROM read_csv_auto('../data/raw_clientes.csv', all_varchar=True)