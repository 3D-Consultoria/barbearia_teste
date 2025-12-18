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

    # 1. Conecta na raiz do MotherDuck
    con = duckdb.connect(f'md:?token={token}')
    
    # 2. Garante que o banco de dados existe
    print("Verificando/Criando banco de dados 'barbearia_db'...")
    con.execute("CREATE DATABASE IF NOT EXISTS barbearia_db")
    
    # 3. Entra no banco correto
    con.execute("USE barbearia_db")
    
    files = {
        "raw_clientes": URL_CLIENTES,
        "raw_vendas": URL_VENDAS
    }

    for table_name, url in files.items():
        try:
            print(f"Baixando e enviando {table_name}...")
            
            if "LINK_CSV" in url:
                print(f"⚠️ PULA {table_name}: URL não configurada no código.")
                continue

            # --- CORREÇÃO AQUI ---
            # on_bad_lines='warn': Se a linha tiver colunas a mais (sujeira), 
            # ele pula a linha, avisa no log, mas NÃO quebra o pipeline.
            df = pd.read_csv(url, on_bad_lines='warn')
            
            if len(df) == 0:
                send_telegram_alert(f"⚠️ {table_name} veio vazio!", level="warning")

            # Load para MotherDuck
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            
            print(f"✅ {table_name} carregada na nuvem ({len(df)} linhas).")
            
        except Exception as e:
            msg = f"🚨 Falha no Load de {table_name}: {e}"
            print(msg)
            send_telegram_alert(msg, level="error")
            raise e

if __name__ == "__main__":
    run_pipeline()