import duckdb
import yagmail
import os
import pandas as pd
from datetime import datetime
from openai import OpenAI

def get_ai_analysis(total_clientes, novos_clientes, media_idade, aniversariantes_mes):
    """
    IA Consultora recebendo dados demográficos
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "<p><i>(IA indisponível: Configure a OPENAI_API_KEY)</i></p>"

    client = OpenAI(api_key=api_key)

    # Prompt enriquecido com dados de IDADE
    prompt = f"""
    Você é um estrategista de marketing para barbearias.
    
    DADOS DO NEGÓCIO HOJE ({datetime.now().strftime('%d/%m/%Y')}):
    - Total de Clientes: {total_clientes}
    - Novos Clientes (Semana): {novos_clientes}
    - Média de Idade do Público: {media_idade:.0f} anos
    - Aniversariantes deste mês: {aniversariantes_mes} clientes

    TAREFA:
    Analise a faixa etária e os aniversariantes.
    Escreva 1 insight curto e acionável (máx 3 linhas).
    Exemplo: Se a média for jovem, sugira cortes da moda. Se tiver aniversariantes, sugira uma promoção de fidelidade.
    Use um tom motivador.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um consultor de dados criativo."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na IA: {e}")
        return "Não foi possível gerar análise hoje."

def calcular_idade(nascimento_str):
    """Converte string de data em idade"""
    try:
        # Tenta converter formatos comuns (DD/MM/YYYY ou YYYY-MM-DD)
        nasc = pd.to_datetime(nascimento_str, dayfirst=True)
        hoje = datetime.now()
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    except:
        return None

def send_report():
    print(">>> [3/3] Iniciando Processamento de Dados + IA...")
    
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    # --- 1. Busca Dados ---
    try:
        query_check = "SELECT * FROM mart_clientes LIMIT 1"
        con.execute(query_check)
        table_name = "mart_clientes"
    except Exception:
        table_name = "read_csv_auto('data/raw_customers.csv')"

    # Carrega tudo para o Pandas para manipular datas facilmente
    df = con.execute(f"SELECT * FROM {table_name}").df()
    
    qtd_clientes = len(df)
    
    # --- 2. Lógica Inteligente de Colunas (Nome e Nascimento) ---
    coluna_nome = df.columns[0]
    coluna_nasc = None
    
    # Tenta encontrar colunas pelo nome
    for col in df.columns:
        col_lower = col.lower()
        if 'nome' in col_lower or 'name' in col_lower or 'cliente' in col_lower:
            coluna_nome = col
        if 'nasc' in col_lower or 'birth' in col_lower or 'data' in col_lower:
            coluna_nasc = col
            
    print(f"Colunas detectadas -> Nome: {coluna_nome} | Nascimento: {coluna_nasc}")

    # --- 3. Cálculos Demográficos ---
    media_idade = 0
    aniversariantes_mes = 0
    
    if coluna_nasc:
        # Converte para datetime e cria coluna 'idade'
        df['data_obj'] = pd.to_datetime(df[coluna_nasc], dayfirst=True, errors='coerce')
        
        # Calcula média de idade (ignorando erros)
        now = datetime.now()
        df['idade'] = df['data_obj'].apply(lambda x: now.year - x.year - ((now.month, now.day) < (x.month, x.day)) if pd.notnull(x) else None)
        media_idade = df['idade'].mean() if not df['idade'].isnull().all() else 0
        
        # Conta aniversariantes do mês atual
        mes_atual = now.month
        aniversariantes_mes = df[df['data_obj'].dt.month == mes_atual].shape[0]
    else:
        print("AVISO: Coluna de data de nascimento não encontrada.")

    # --- 4. Chama a IA ---
    analise_ia = get_ai_analysis(qtd_clientes, 3, media_idade, aniversariantes_mes)

    # --- 5. Monta HTML ---
    # Lista de nomes (top 10)
    lista_nomes_html = ""
    for nome in df[coluna_nome].head(10):
        lista_nomes_html += f"<li style='margin-bottom: 5px;'>{str(nome).title()}</li>"

    # Bloco de Estatísticas Extras
    stats_html = ""
    if coluna_nasc and media_idade > 0:
        stats_html = f"""
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; flex: 1;">
                <span style="font-size: 12px; color: #666;">Idade Média</span><br>
                <strong style="font-size: 18px; color: #333;">{media_idade:.0f} anos</strong>
            </div>
            <div style="background: #e8f5e9; padding: 10px; border-radius: 5px; flex: 1;">
                <span style="font-size: 12px; color: #666;">Aniversariantes (Mês)</span><br>
                <strong style="font-size: 18px; color: #2e7d32;">{aniversariantes_mes}</strong>
            </div>
        </div>
        """

    date_now = datetime.now().strftime('%d/%m/%Y')
    
    html_body = f"""
    <div style="background-color: #ffffff; color: #000000; padding: 20px; font-family: Arial, sans-serif; max-width: 600px;">
        <h2 style="color: #333;">Relatório Inteligente - {date_now}</h2>
        <hr style="border: 1px solid #eee;">
        
        <p style="font-size: 18px;">Total de Clientes: <strong style="color: #007bff;">{qtd_clientes}</strong></p>
        
        {stats_html}
        
        <div style="background-color: #f0f8ff; border-left: 5px solid #007bff; padding: 15px; margin: 20px 0;">
            <h4 style="margin-top: 0; color: #0056b3;">🤖 Consultor IA diz:</h4>
            <p style="font-style: italic; color: #333; line-height: 1.5;">"{analise_ia}"</p>
        </div>
        
        <h3 style="color: #333; margin-top: 30px;">Últimos Clientes:</h3>
        <ul style="color: #555;">
            {lista_nomes_html}
        </ul>
        
        <br>
        <p style="color: #999; font-size: 12px; text-align: center;">Gerado por 3D Consultoria</p>
    </div>
    """
    
    # --- 6. Envia ---
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "leandro.lf.frazao@hotmail.com"

    if not sender_email: return

    try:
        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(
            to=receiver_email,
            subject=f"Resumo Estratégico - {date_now}",
            contents=[html_body]
        )
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro: {e}")
        raise e

if __name__ == "__main__":
    send_report()