import pandas as pd
import duckdb
import os
from notifications import send_telegram_alert

# --- CONFIGURAÇÃO ---
URL_CLIENTES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSbvYHhT0lnjkj6RCzVDslOtj6Vlt9A7QwbHV4hKlpKTNFw0OQzy6vT08ABMxb2301AwfE3RbzpR5Y/pubhtml?gid=0&single=true" 
URL_VENDAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSbvYHhT0lnjkj6RCzVDslOtj6Vlt9A7QwbHV4hKlpKTNFw0OQzy6vT08ABMxb2301AwfE3RbzpR5Y/pubhtml?gid=48884415&single=true"

def run_pipeline():
    print(">>> [1/4] Iniciando Ingestão para Data Lake (MotherDuck)...")
    
    # Pega o Token
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise Exception("MOTHERDUCK_TOKEN não configurado!")

    # Conecta direto na nuvem
    con = duckdb.connect(f'md:barbearia_db?token={token}')
    
    files = {
        "raw_clientes": URL_CLIENTES,
        "raw_vendas": URL_VENDAS
    }

    for table_name, url in files.items():
        try:
            print(f"Baixando e enviando {table_name}...")
            
            # 1. Lê o CSV com Pandas (Extração)
            df = pd.read_csv(url)
            
            if len(df) == 0:
                send_telegram_alert(f"⚠️ {table_name} veio vazio!", level="warning")

            # 2. Carrega para o MotherDuck (Load)
            # Cria a tabela se não existir, ou substitui
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            
            print(f"✅ {table_name} carregada na nuvem ({len(df)} linhas).")
            
        except Exception as e:
            send_telegram_alert(f"🚨 Falha no Load de {table_name}: {e}", level="error")
            raise e

if __name__ == "__main__":
    run_pipeline()