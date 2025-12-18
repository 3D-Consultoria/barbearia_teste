import pandas as pd
import duckdb
import os
from notifications import send_telegram_alert

# --- CONFIGURAÇÃO ---
# O ID GERAL DA PLANILHA
SHEET_ID = "1f655JLEQiOxSB0uKFRv9Ds9-00rAVNP2qTfeXRbSgq4"

# Aba Clientes (Geralmente gid=0 se for a primeira, mas confira!)
URL_CLIENTES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# Aba Vendas (VOCÊ PRECISA PEGAR O NÚMERO DO GID NO SEU NAVEGADOR)
# Exemplo: se na URL estiver #gid=987654321, coloque esse número abaixo
GID_VENDAS = "48884415" 
URL_VENDAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_VENDAS}"

def run_pipeline():
    print(">>> [1/4] Iniciando Ingestão e Infraestrutura...")
    
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise Exception("MOTHERDUCK_TOKEN não configurado!")

    con = duckdb.connect(f'md:?token={token}')
    
    # 1. Garante o Banco
    con.execute("CREATE DATABASE IF NOT EXISTS barbearia_db")
    con.execute("USE barbearia_db")

    # 2. Garante a Tabela de MEMÓRIA DA IA (Novidade!)
    print("Verificando tabela de histórico da IA...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS historico_ia (
            data_referencia DATE,
            insight_gerado VARCHAR,
            metricas_json VARCHAR,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Carrega Dados (Load)
    files = {
        "raw_clientes": URL_CLIENTES,
        "raw_vendas": URL_VENDAS
    }

    for table_name, url in files.items():
        try:
            print(f"Processando {table_name}...")
            df = pd.read_csv(url, on_bad_lines='warn')
            
            if len(df.columns) > 0 and "<!DOCTYPE" in str(df.columns[0]):
                raise Exception("ERRO: Link baixou HTML. Verifique o GID.")

            if len(df) == 0:
                send_telegram_alert(f"⚠️ {table_name} vazio!", level="warning")

            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            print(f"✅ {table_name}: {len(df)} linhas.")
            
        except Exception as e:
            send_telegram_alert(f"Erro no {table_name}: {e}", level="error")
            raise e

if __name__ == "__main__":
    run_pipeline()