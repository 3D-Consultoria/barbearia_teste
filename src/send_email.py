import duckdb
import yagmail
import os
from datetime import datetime

def send_report():
    print(">>> [3/3] Iniciando geração de métricas e envio de e-mail...")
    
    # 1. Conecta no banco
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    # 2. Busca os dados (Count e Nomes)
    try:
        # Pega a contagem total
        df_count = con.execute("SELECT COUNT(*) as total FROM mart_clientes").df()
        qtd_clientes = df_count['total'].iloc[0]
        
        # Pega os nomes dos clientes (Limitado a 50 para não estourar o email)
        # Ajuste 'nome' para o nome exato da coluna na sua planilha, se for diferente (ex: 'Name', 'Cliente')
        df_names = con.execute("SELECT * FROM mart_clientes LIMIT 50").df()
        
    except Exception:
        print("Tabela mart_clientes não encontrada, lendo do CSV raw.")
        df_count = con.execute("SELECT COUNT(*) as total FROM read_csv_auto('data/raw_customers.csv')").df()
        qtd_clientes = df_count['total'].iloc[0]
        df_names = con.execute("SELECT * FROM read_csv_auto('data/raw_customers.csv') LIMIT 50").df()

    # 3. Monta a lista de nomes em HTML (<ul><li>Nome</li></ul>)
    # Assume que a primeira coluna é o nome, ou busca coluna especifica
    coluna_nome = df_names.columns[0] # Pega a primeira coluna disponível
    lista_nomes_html = ""
    for nome in df_names[coluna_nome]:
        lista_nomes_html += f"<li>{nome}</li>"

    # 4. Configura o E-mail
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "leandro.lf.frazao@hotmail.com"
    date_now = datetime.now().strftime('%d/%m/%Y')

    # --- AQUI ESTÁ A CORREÇÃO QUE VOCÊ PEDIU ---
    
    # O Assunto agora é a Data
    subject = f"Resumo da Barbearia - {date_now}"
    
    # O Corpo agora tem os DADOS
    contents = [
        f"<h2>Olá! Segue o resumo de hoje ({date_now}):</h2>",
        "<hr>",
        f"<p style='font-size: 16px;'>Total de Clientes na Base: <strong>{qtd_clientes}</strong></p>",
        "<h3>Lista de Clientes Recentes:</h3>",
        f"<ul>{lista_nomes_html}</ul>", # Insere a lista formatada
        "<br>",
        "<p><i>Enviado automaticamente por 3D Consultoria</i></p>"
    ]
    
    # 5. Envia
    if not sender_email or not sender_password:
        print("ERRO: Credenciais não configuradas.")
        return

    try:
        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(
            to=receiver_email,
            subject=subject,
            contents=contents
        )
        print(f"Relatório enviado! Assunto: {subject}")
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        raise e

if __name__ == "__main__":
    send_report()