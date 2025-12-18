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