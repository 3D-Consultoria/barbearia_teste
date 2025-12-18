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
    
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        raise Exception("MOTHERDUCK_TOKEN não configurado!")

    # Conecta no MotherDuck e seleciona o banco
    con = duckdb.connect(f'md:?token={token}')
    print("Verificando banco de dados...")
    con.execute("CREATE DATABASE IF NOT EXISTS barbearia_db")
    con.execute("USE barbearia_db")
    
    files = {
        "raw_clientes": URL_CLIENTES,
        "raw_vendas": URL_VENDAS
    }

    for table_name, url in files.items():
        try:
            print(f"Baixando {table_name}...")
            # on_bad_lines='warn' evita travar com linhas sujas
            df = pd.read_csv(url, on_bad_lines='warn')
            
            # Verificação de Segurança: Se baixou HTML por engano, vai ter coluna '<!DOCTYPE'
            if len(df.columns) > 0 and "<!DOCTYPE" in str(df.columns[0]):
                raise Exception("ERRO CRÍTICO: O link configurado baixou um SITE (HTML) e não um CSV. Verifique o link de exportação.")

            if len(df) == 0:
                send_telegram_alert(f"⚠️ {table_name} veio vazio!", level="warning")

            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            print(f"✅ {table_name} carregada ({len(df)} linhas).")
            
        except Exception as e:
            msg = f"🚨 Falha no Load de {table_name}: {e}"
            print(msg)
            send_telegram_alert(msg, level="error")
            raise e

if __name__ == "__main__":
    run_pipeline()