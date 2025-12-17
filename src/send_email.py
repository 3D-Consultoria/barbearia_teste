import duckdb
import yagmail
import os
from datetime import datetime

def send_report():
    print(">>> [3/3] Iniciando envio de e-mail...")
    
    # Conecta no banco criado pelo dbt (modo leitura)
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    # Busca dados da tabela tratada pelo dbt
    query = "SELECT * FROM mart_clientes"
    try:
        df = con.execute(query).df()
    except Exception:
        print("Tabela mart_clientes não encontrada, lendo do raw para teste.")
        df = con.execute("SELECT * FROM read_csv_auto('data/raw_customers.csv')").df()

    # Gera HTML simples
    stats_html = df.to_html(index=False, classes='table table-striped', border=1)
    
    # Configuração de envio
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "leandro.lf.frazao@hotmail.com"
    
    if not sender_email or not sender_password:
        print("ERRO: Variáveis de ambiente EMAIL_USER ou EMAIL_PASS não configuradas.")
        return

    subject = f"Relatório Barbearia - {datetime.now().strftime('%d/%m/%Y')}"
    
    contents = [
        "<h2>Resumo Diário da Barbearia</h2>",
        f"<p>Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>",
        "<h3>Dados Atualizados:</h3>",
        stats_html,
        "<br><hr>",
        "<p><i>Enviado automaticamente por 3D Consultoria</i></p>"
    ]
    
    try:
        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(
            to=receiver_email,
            subject=subject,
            contents=contents
        )
        print(f"Email enviado com sucesso para {receiver_email}!")
    except Exception as e:
        print(f"Falha ao enviar email: {e}")
        raise e

if __name__ == "__main__":
    send_report()