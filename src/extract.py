import pandas as pd
import os
from notifications import send_telegram_alert

# --- CONFIGURAÇÃO DAS URLS ---
# IMPORTANTE: Pegue o link de exportação de cada aba da sua planilha.
# Geralmente muda o 'gid=' no final da URL.
# Exemplo: ".../export?format=csv&gid=0" (Aba 1)
# Exemplo: ".../export?format=csv&gid=12345" (Aba 2)

URL_CLIENTES = "COLOQUE_AQUI_O_LINK_CSV_DA_ABA_CLIENTES" 
URL_VENDAS = "COLOQUE_AQUI_O_LINK_CSV_DA_ABA_VENDAS"

def run_extraction():
    print(">>> [1/3] Iniciando extração de Tabelas...")
    os.makedirs("data", exist_ok=True)
    
    files = {
        "raw_clientes.csv": URL_CLIENTES,
        "raw_vendas.csv": URL_VENDAS
    }

    for filename, url in files.items():
        try:
            # Verifica se o link foi configurado
            if "COLOQUE_AQUI" in url:
                raise Exception(f"URL para {filename} não configurada no script!")

            print(f"Baixando {filename}...")
            df = pd.read_csv(url)
            
            if len(df) == 0:
                send_telegram_alert(f"⚠️ Arquivo {filename} veio VAZIO!", level="warning")
            
            output_path = f"data/{filename}"
            df.to_csv(output_path, index=False)
            print(f"✅ {filename} salvo com {len(df)} linhas.")
            
        except Exception as e:
            msg_erro = f"🚨 Falha ao baixar {filename}: {str(e)}"
            print(msg_erro)
            send_telegram_alert(msg_erro, level="error")
            raise e

if __name__ == "__main__":
    run_extraction()