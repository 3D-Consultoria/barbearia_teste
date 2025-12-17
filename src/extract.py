import pandas as pd
import os

# ID da planilha fornecida
SHEET_ID = "1f655JLEQiOxSB0uKFRv9Ds9-00rAVNP2qTfeXRbSgq4"
# Exporta a primeira aba como CSV
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def run_extraction():
    print(">>> [1/3] Iniciando extração do Google Sheets...")
    
    try:
        # Lê a planilha direto da URL
        df = pd.read_csv(URL)
        
        # Cria pasta de dados se não existir
        os.makedirs("data", exist_ok=True)
        
        # Salva como raw_data.csv para o dbt consumir
        output_path = "data/raw_customers.csv"
        df.to_csv(output_path, index=False)
        
        print(f"Sucesso! {len(df)} linhas extraídas.")
        print(f"Arquivo salvo em: {output_path}")
        print("Colunas:", df.columns.tolist())
        
    except Exception as e:
        print(f"Erro na extração: {e}")
        raise e

if __name__ == "__main__":
    run_extraction()