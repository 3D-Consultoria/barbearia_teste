import duckdb
import yagmail
import os
from datetime import datetime

def send_report():
    print(">>> [3/3] Iniciando geração de métricas e envio de e-mail...")
    
    # 1. Conecta no banco
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    # 2. Busca os dados
    try:
        # Tenta ler da tabela mart, se falhar lê do CSV
        query_check = "SELECT * FROM mart_clientes LIMIT 1"
        con.execute(query_check)
        table_name = "mart_clientes"
    except Exception:
        print("Aviso: Tabela 'mart_clientes' não encontrada. Usando 'raw_customers.csv'.")
        table_name = "read_csv_auto('data/raw_customers.csv')"

    # Pega Contagem
    df_count = con.execute(f"SELECT COUNT(*) as total FROM {table_name}").df()
    qtd_clientes = df_count['total'].iloc[0]
    
    # Pega Nomes (Tenta achar a coluna de nome automaticamente)
    df_sample = con.execute(f"SELECT * FROM {table_name} LIMIT 50").df()
    
    # Lógica para achar a coluna de Nome (procura por 'nome', 'name', 'cliente' ou pega a segunda coluna)
    coluna_alvo = df_sample.columns[0] # Padrão: primeira coluna
    
    # Se tiver mais de 1 coluna, geralmente o ID é a primeira e o Nome a segunda
    if len(df_sample.columns) > 1:
        coluna_alvo = df_sample.columns[1]
        
    # Tenta achar nome específico
    for col in df_sample.columns:
        if 'nome' in col.lower() or 'name' in col.lower() or 'cliente' in col.lower():
            coluna_alvo = col
            break
            
    print(f"Coluna selecionada para exibição: {coluna_alvo}")

    # 3. Monta a lista HTML
    lista_nomes_html = ""
    for nome in df_sample[coluna_alvo]:
        lista_nomes_html += f"<li style='margin-bottom: 5px;'>{str(nome).title()}</li>"

    # 4. Configura o E-mail com ESTILO FORÇADO (Fundo Branco, Letra Preta)
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "leandro.lf.frazao@hotmail.com"
    date_now = datetime.now().strftime('%d/%m/%Y')

    subject = f"Resumo da Barbearia - {date_now}"
    
    # HTML Blindado: Usamos uma DIV branca para garantir que o texto apareça
    html_body = f"""
    <div style="background-color: #ffffff; color: #000000; padding: 20px; font-family: Arial, sans-serif;">
        <h2 style="color: #333333;">Olá! Segue o resumo de hoje ({date_now}):</h2>
        <hr style="border: 1px solid #cccccc;">
        
        <p style="font-size: 18px; color: #000000;">
            Total de Clientes na Base: <strong style="color: #007bff; font-size: 22px;">{qtd_clientes}</strong>
        </p>
        
        <h3 style="color: #333333; margin-top: 20px;">Lista de Clientes Recentes:</h3>
        <ul style="color: #000000;">
            {lista_nomes_html}
        </ul>
        
        <br>
        <hr style="border: 0; border-top: 1px solid #eee;">
        <p style="color: #666666; font-size: 12px;"><i>Enviado automaticamente por 3D Consultoria</i></p>
    </div>
    """
    
    # 5. Envia
    if not sender_email or not sender_password:
        print("ERRO: Credenciais não configuradas.")
        return

    try:
        yag = yagmail.SMTP(sender_email, sender_password)
        # Passamos o body como uma lista contendo a string única
        yag.send(
            to=receiver_email,
            subject=subject,
            contents=[html_body] 
        )
        print(f"Relatório enviado com sucesso! Total: {qtd_clientes}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        raise e

if __name__ == "__main__":
    send_report()