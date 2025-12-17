{{ config(materialized='table') }}

SELECT
    -- Seleciona tudo do CSV cru
    *
FROM read_csv_auto('../data/raw_customers.csv')