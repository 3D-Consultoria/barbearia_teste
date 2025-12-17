import duckdb
import yagmail
import os
from datetime import datetime
from openai import OpenAI

# --- CONFIGURAÇÃO DO CLIENTE ---
CONFIG_CLIENTE = {
    "nome_empresa": "Barbearia Teste",
    "tipo_negocio": "Barbearia Clássica",
    "foco_estrategico": "Fidelização e recorrência mensal.",
    "tom_de_voz": "Profissional e motivador."
}

def get_ai_analysis(metricas):
    """Agente de IA Consultor"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "IA indisponível."

    client = OpenAI(api_key=api_key)

    system_prompt = f"""
    Você é um Consultor Estratégico da 3D Consultoria para a {CONFIG_CLIENTE['nome_empresa']}.
    Foco: {CONFIG_CLIENTE['foco_estrategico']}
    
    Analise os KPIs abaixo e dê 1 (UM) insight curto (máx 3 linhas) para o dono agir hoje.
    """

    user_prompt = f"""
    MÉTRICAS DO DIA ({datetime.now().strftime('%d/%m/%Y')}):
    - Total Clientes: {metricas['total']}
    - Idade Média: {metricas['idade_media']} (Público principal: {metricas['faixa_principal']})
    - Aniversariantes Mês: {metricas['aniversariantes']}
    
    REGRA:
    - Se houver aniversariantes, sugira ação para eles.
    - Senão, foque na faixa etária predominante.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=0.7, max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Sem análise hoje."

def send_report():
    print(">>> [3/3] Iniciando Report Inteligente (Via dbt Marts)...")
    
    # Conecta no banco já processado pelo dbt
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    # --- 1. Busca Métricas PRONTAS (SQL puro) ---
    # Perceba como não tem mais lógica python complexa aqui
    try:
        # Pega métricas agregadas numa única query rápida
        kpi_query = """
        SELECT 
            COUNT(*) as total,
            CAST(AVG(idade) AS INTEGER) as media_idade,
            SUM(CASE WHEN is_aniversariante_mes THEN 1 ELSE 0 END) as total_aniversariantes,
            MODE(faixa_etaria) as faixa_principal
        FROM mart_clientes
        """
        df_kpi = con.execute(kpi_query).df()
        
        # Pega lista de nomes simples
        df_list = con.execute("SELECT nome_cliente FROM mart_clientes LIMIT 8").df()
        
    except Exception as e:
        print(f"Erro ao ler tabela dbt (mart_clientes): {e}")
        print("DICA: Rode 'dbt run' antes de executar esse script.")
        return

    # Prepara dados para IA
    metricas = {
        "total": int(df_kpi['total'].iloc[0]),
        "idade_media": int(df_kpi['media_idade'].iloc[0]) if df_kpi['media_idade'].notna().all() else 0,
        "aniversariantes": int(df_kpi['total_aniversariantes'].iloc[0]),
        "faixa_principal": df_kpi['faixa_principal'].iloc[0]
    }

    print(f"Dados Carregados do dbt: {metricas}")
    insight_ia = get_ai_analysis(metricas)

    # --- 2. Geração HTML ---
    lista_html = ""
    for nome in df_list['nome_cliente']:
        lista_html += f"<li style='margin-bottom: 4px;'>{nome}</li>"

    date_now = datetime.now().strftime('%d/%m/%Y')
    
    # Box de Destaque
    stats_box = f"""
    <div style="display: flex; gap: 10px; margin: 20px 0;">
        <div style="background: #f8f9fa; padding: 15px; border: 1px solid #ddd; border-radius: 8px; flex: 1; text-align: center;">
            <div style="font-size: 12px; color: #666; text-transform: uppercase;">Idade Média</div>
            <div style="font-size: 24px; font-weight: bold; color: #333;">{metricas['idade_media']}</div>
        </div>
        <div style="background: #e8f5e9; padding: 15px; border: 1px solid #c8e6c9; border-radius: 8px; flex: 1; text-align: center;">
            <div style="font-size: 12px; color: #2e7d32; text-transform: uppercase;">Aniversariantes</div>
            <div style="font-size: 24px; font-weight: bold; color: #2e7d32;">{metricas['aniversariantes']}</div>
        </div>
    </div>
    """

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        <div style="border-bottom: 2px solid #0056b3; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0;">📊 Resumo: {CONFIG_CLIENTE['nome_empresa']}</h2>
            <p style="margin: 5px 0 0; color: #777;">Data: {date_now}</p>
        </div>
        
        <p style="font-size: 18px;">Total de Clientes Ativos: <strong>{metricas['total']}</strong></p>
        
        {stats_box}

        <div style="background-color: #f0f7ff; border-left: 5px solid #0056b3; padding: 15px; margin: 25px 0;">
            <strong>🤖 Consultor Virtual:</strong>
            <p style="margin-top: 5px; font-style: italic;">"{insight_ia}"</p>
        </div>

        <h3>Novos Cadastros:</h3>
        <ul>{lista_html}</ul>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 40px;">
        <p style="text-align: center; font-size: 12px; color: #999;">3D Consultoria de Dados</p>
    </div>
    """

    # --- 3. Envio ---
    sender = os.environ.get("EMAIL_USER")
    pwd = os.environ.get("EMAIL_PASS")
    
    if sender and pwd:
        yag = yagmail.SMTP(sender, pwd)
        yag.send(to="leandro.lf.frazao@hotmail.com", subject=f"Resumo 3D: {date_now}", contents=[html_body])
        print("Email enviado!")
    else:
        print("Erro: Credenciais de email não configuradas.")

if __name__ == "__main__":
    send_report()