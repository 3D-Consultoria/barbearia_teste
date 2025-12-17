import duckdb
import yagmail
import os
from datetime import datetime

def send_report():
    print(">>> [3/3] Iniciando geração de métricas e envio de e-mail...")
    
    # 1. Conecta no banco de dados (modo leitura)
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    # 2. Executa a query de contagem (SQL)
    # Verifica se a tabela existe, senão lê do CSV para evitar erro no primeiro run
    try:
        query = "SELECT COUNT(*) as total FROM mart_clientes"
        df = con.execute(query).df()
    except Exception:
        print("Tabela mart_clientes não encontrada no banco, lendo do CSV raw.")
        df = con.execute("SELECT COUNT(*) as total FROM read_csv_auto('data/raw_customers.csv')").df()
        
    # Pega o valor único da contagem
    qtd_clientes = df['total'].iloc[0]
    print(f"Contagem obtida: {qtd_clientes}")

    # 3. Prepara o conteúdo do e-mail (Texto simples, sem tabelas complexas)
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "leandro.lf.frazao@hotmail.com"
    
    date_now = datetime.now().strftime('%d/%m/%Y')
    
    # Corpo do email usando HTML básico que funciona em qualquer lugar
    subject = f"Resumo Diário: {qtd_clientes} Clientes"
    
    contents = [
        f"<h2>Resumo da Barbearia - {date_now}</h2>",
        "<hr>",
        f"<p>Olá! Até o momento, temos a seguinte métrica:</p>",
        f"<h1>{qtd_clientes}</h1>",
        "<p><strong>Clientes Cadastrados na Base</strong></p>",
        "<br>",
        "<p><i>Relatório automático - 3D Consultoria</i></p>"
    ]
    
    # 4. Envia
    if not sender_email or not sender_password:
        print("ERRO: Credenciais de e-mail não configuradas.")
        return

    try:
        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(
            to=receiver_email,
            subject=subject,
            contents=contents
        )
        print("Relatório enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        raise e

if __name__ == "__main__":
    send_report()