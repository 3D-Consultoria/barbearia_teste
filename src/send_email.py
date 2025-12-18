import duckdb
import yagmail
import os
from datetime import datetime
from openai import OpenAI
from notifications import send_telegram_alert

CONFIG_CLIENTE = {
    "nome_empresa": "Barbearia Teste",
    "tipo_negocio": "Barbearia",
    "foco_estrategico": "Aumentar Ticket Médio e atrair bairros vizinhos.",
    "tom_de_voz": "Analítico e Estratégico."
}

def get_ai_analysis(financas, top_bairro):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "IA indisponível."

    client = OpenAI(api_key=api_key)

    system_prompt = f"""
    Você é o Consultor Financeiro da 3D Consultoria.
    Analise os dados financeiros e geográficos da {CONFIG_CLIENTE['nome_empresa']}.
    
    DADOS:
    - Faturamento Total (Histórico): R$ {financas['faturamento']}
    - Ticket Médio: R$ {financas['ticket_medio']}
    - Serviço Carro-Chefe: {financas['top_servico']}
    - Bairro que mais gasta: {top_bairro}
    
    TAREFA:
    Escreva um insight de 3 linhas. 
    Se o ticket médio for baixo (< 40), sugira upsell (combo).
    Se houver concentração em um bairro, sugira ads para bairros vizinhos.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=250
        )
        return response.choices[0].message.content
    except:
        return "Sem análise."

def send_report():
    print(">>> [3/3] Conectando ao MotherDuck para Relatório...")
    
    token = os.environ.get("MOTHERDUCK_TOKEN")
    # Conecta na nuvem (ReadOnly é ignorado no MotherDuck mas mantemos padrão)
    con = duckdb.connect(f'md:barbearia_db?token={token}')
    
    try:
        # 1. Busca Dados Financeiros Gerais
        df_fin = con.execute("SELECT * FROM mart_financeiro").df()
        faturamento = df_fin['faturamento_total'].iloc[0] or 0
        ticket_medio = df_fin['ticket_medio'].iloc[0] or 0
        top_servico = df_fin['servico_mais_vendido'].iloc[0]

        # 2. Busca Melhor Bairro (Geografia)
        query_bairro = """
            SELECT bairro, SUM(total_gasto_ltv) as total 
            FROM mart_dashboard 
            WHERE bairro IS NOT NULL
            GROUP BY bairro 
            ORDER BY total DESC LIMIT 1
        """
        res_bairro = con.execute(query_bairro).fetchone()
        top_bairro = res_bairro[0] if res_bairro else "Indefinido"

        # 3. Lista de VIPs
        df_vips = con.execute("SELECT nome, total_gasto_ltv, dias_desde_ultima_visita FROM mart_dashboard ORDER BY total_gasto_ltv DESC LIMIT 5").df()

    except Exception as e:
        send_telegram_alert(f"Erro ao ler dados do DuckDB: {e}", level="error")
        raise e

    # IA Analysis
    metricas_ia = {
        "faturamento": f"{faturamento:.2f}",
        "ticket_medio": f"{ticket_medio:.2f}",
        "top_servico": top_servico
    }
    insight = get_ai_analysis(metricas_ia, top_bairro)

    # --- HTML ---
    lista_vips = ""
    for index, row in df_vips.iterrows():
        # Lógica de Churn: Se não vem há 30 dias, está 'Sumido'
        status = "🔴 Sumido" if row['dias_desde_ultima_visita'] > 30 else "🟢 Ativo"
        lista_vips += f"<li style='margin-bottom:5px;'><b>{row['nome']}</b>: R$ {row['total_gasto_ltv']:.2f} <span style='font-size:12px'>({status})</span></li>"

    html_body = f"""
    <div style="font-family: Arial, color: #333; max-width: 600px; border: 1px solid #eee; padding: 20px; border-radius: 8px;">
        <h2 style="color: #0056b3; margin-top:0;">💰 Resumo Financeiro & CRM</h2>
        <p style="color:#666; font-size:12px;">Data: {datetime.now().strftime('%d/%m/%Y')}</p>
        <hr style="border:0; border-top:1px solid #eee;">
        
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <div style="background: #e8f5e9; padding: 15px; flex: 1; border-radius: 8px; text-align: center;">
                <small style="color:#2e7d32; text-transform:uppercase;">Faturamento</small><br>
                <strong style="font-size: 22px; color: #2e7d32;">R$ {faturamento:,.2f}</strong>
            </div>
            <div style="background: #e3f2fd; padding: 15px; flex: 1; border-radius: 8px; text-align: center;">
                <small style="color:#1565c0; text-transform:uppercase;">Ticket Médio</small><br>
                <strong style="font-size: 22px; color: #1565c0;">R$ {ticket_medio:,.2f}</strong>
            </div>
        </div>

        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin-bottom: 20px;">
            <strong>🤖 Consultor 3D diz:</strong><br>
            <i style="color:#555;">"{insight}"</i>
        </div>

        <h3 style="color: #333;">🏆 Clientes VIPs (Top 5)</h3>
        <ul style="padding-left: 20px; color: #444;">{lista_vips}</ul>
        
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 14px;">
            <b>📍 Top Bairro:</b> {top_bairro} <br>
            <b>✂️ Top Serviço:</b> {top_servico}
        </div>
        
        <p style="text-align: center; color: #999; font-size: 11px; margin-top: 20px;">Gerado por 3D Consultoria</p>
    </div>
    """
    
    # Envio
    sender = os.environ.get("EMAIL_USER")
    pwd = os.environ.get("EMAIL_PASS")
    
    if sender:
        try:
            yag = yagmail.SMTP(sender, pwd)
            yag.send(to="leandro.lf.frazao@hotmail.com", subject=f"Relatório Financeiro - {datetime.now().strftime('%d/%m')}", contents=[html_body])
            print("Relatório enviado!")
        except Exception as e:
            send_telegram_alert(f"Erro ao enviar E-mail: {e}", level="error")
            raise e
    else:
        print("Credenciais de e-mail não configuradas.")

if __name__ == "__main__":
    send_report()