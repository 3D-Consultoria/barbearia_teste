import duckdb
import yagmail
import os
import json
from datetime import datetime
from openai import OpenAI
from notifications import send_telegram_alert

CONFIG_CLIENTE = {
    "nome_empresa": "Barbearia Teste",
    "tipo_negocio": "Barbearia",
    "foco_estrategico": "Crescimento consistente e fidelização.",
    "tom_de_voz": "Analítico, direto e estratégico."
}

def get_ai_analysis(metricas, top_bairro, historico_recente):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key: return "IA indisponível."

    client = OpenAI(api_key=api_key)

    # Formata histórico para a IA saber o que NÃO repetir
    txt_memoria = ""
    if historico_recente:
        txt_memoria = "OBSERVAÇÃO IMPORTANTE - O QUE VOCÊ JÁ DISSE RECENTEMENTE (NÃO REPITA):\n"
        for i, h in enumerate(historico_recente):
            txt_memoria += f"- {h}\n"

    txt_periodos = "\n".join([f"- {k}: R$ {v['valor']} ({v['qtd']} vendas)" for k, v in metricas['periodos'].items()])

    system_prompt = f"""
    Você é o Consultor Financeiro da 3D Consultoria.
    
    CONTEXTO:
    Empresa: {CONFIG_CLIENTE['nome_empresa']}
    
    DADOS DE HOJE:
    {txt_periodos}
    Ticket Médio: R$ {metricas['ticket_medio']}
    Top Bairro: {top_bairro}
    
    {txt_memoria}
    
    TAREFA:
    Analise os dados de hoje. Dê 1 insight tático NOVO.
    Seja criativo. Evite repetir os conselhos listados acima.
    Máximo 3 linhas.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content
    except:
        return "Sem análise disponível hoje."

def send_report():
    print(">>> [3/3] Gerando Relatório com Memória...")
    token = os.environ.get("MOTHERDUCK_TOKEN")
    con = duckdb.connect(f'md:barbearia_db?token={token}')
    
    try:
        # 1. Query Temporal
        query_temporal = """
        SELECT 
            AVG(valor_faturamento) as ticket_medio,
            SUM(CASE WHEN data_venda = CURRENT_DATE - INTERVAL 1 DAY THEN valor_faturamento ELSE 0 END) as valor_ontem,
            COUNT(CASE WHEN data_venda = CURRENT_DATE - INTERVAL 1 DAY THEN 1 END) as qtd_ontem,
            SUM(CASE WHEN date_trunc('week', data_venda) = date_trunc('week', CURRENT_DATE) THEN valor_faturamento ELSE 0 END) as valor_semana,
            COUNT(CASE WHEN date_trunc('week', data_venda) = date_trunc('week', CURRENT_DATE) THEN 1 END) as qtd_semana,
            SUM(CASE WHEN date_trunc('month', data_venda) = date_trunc('month', CURRENT_DATE) THEN valor_faturamento ELSE 0 END) as valor_mes,
            COUNT(CASE WHEN date_trunc('month', data_venda) = date_trunc('month', CURRENT_DATE) THEN 1 END) as qtd_mes,
            SUM(CASE WHEN date_trunc('year', data_venda) = date_trunc('year', CURRENT_DATE) THEN valor_faturamento ELSE 0 END) as valor_ano,
            COUNT(CASE WHEN date_trunc('year', data_venda) = date_trunc('year', CURRENT_DATE) THEN 1 END) as qtd_ano
        FROM stg_vendas
        """
        df_tempo = con.execute(query_temporal).df()
        dados = df_tempo.iloc[0]
        
        metricas_ia = {
            "ticket_medio": f"{dados['ticket_medio']:.2f}",
            "periodos": {
                "Ontem": {"valor": f"{dados['valor_ontem']:.2f}", "qtd": dados['qtd_ontem']},
                "Semana Atual": {"valor": f"{dados['valor_semana']:.2f}", "qtd": dados['qtd_semana']},
                "Mês Atual": {"valor": f"{dados['valor_mes']:.2f}", "qtd": dados['qtd_mes']},
                "Ano Atual": {"valor": f"{dados['valor_ano']:.2f}", "qtd": dados['qtd_ano']},
            }
        }

        # 2. Dados Auxiliares
        res_bairro = con.execute("SELECT bairro, SUM(total_gasto_ltv) as t FROM mart_dashboard WHERE bairro IS NOT NULL GROUP BY bairro ORDER BY t DESC LIMIT 1").fetchone()
        top_bairro = res_bairro[0] if res_bairro else "Indefinido"
        df_vips = con.execute("SELECT nome, total_gasto_ltv, dias_desde_ultima_visita FROM mart_dashboard ORDER BY total_gasto_ltv DESC LIMIT 5").df()

        # 3. BUSCA MEMÓRIA (O que a IA falou nos últimos 3 dias?)
        # Tenta buscar, se a tabela estiver vazia (primeiro dia), retorna lista vazia
        try:
            historico_recente = con.execute("SELECT insight_gerado FROM historico_ia ORDER BY data_referencia DESC LIMIT 3").fetchall()
            # Limpa o resultado para uma lista simples de strings
            lista_memoria = [h[0] for h in historico_recente]
        except:
            lista_memoria = []

    except Exception as e:
        send_telegram_alert(f"Erro SQL Prep: {e}", level="error")
        raise e

    # 4. Gera Insight com Contexto
    insight = get_ai_analysis(metricas_ia, top_bairro, lista_memoria)

    # 5. SALVA O INSIGHT NO BANCO (Para não esquecer amanhã)
    try:
        # Prepara JSON para salvar
        json_metrics = json.dumps(metricas_ia)
        # Query parametrizada para evitar erros de aspas
        con.execute(
            "INSERT INTO historico_ia (data_referencia, insight_gerado, metricas_json) VALUES (CURRENT_DATE, ?, ?)",
            [insight, json_metrics]
        )
        print("💾 Insight salvo na memória da IA.")
    except Exception as e:
        print(f"Erro ao salvar histórico (não crítico): {e}")

    # 6. HTML e Envio (Igual ao anterior)
    lista_vips = ""
    for index, row in df_vips.iterrows():
        status = "🔴 Sumido" if row['dias_desde_ultima_visita'] > 30 else "🟢 Ativo"
        lista_vips += f"<li style='margin-bottom:5px; font-size:13px;'><b>{row['nome']}</b>: R$ {row['total_gasto_ltv']:.2f} <span style='color:#666'>({status})</span></li>"

    html_body = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; max-width: 600px; border: 1px solid #e0e0e0; padding: 0; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #0056b3; color: white; padding: 20px; text-align: center;">
            <h2 style="margin:0;">📊 Relatório Diário de Vendas</h2>
            <p style="margin:5px 0 0; font-size:14px; opacity:0.9;">{datetime.now().strftime('%d/%m/%Y')} • {CONFIG_CLIENTE['nome_empresa']}</p>
        </div>
        <div style="padding: 20px;">
            <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 25px; border-radius: 4px;">
                <strong style="color: #333;">💡 Análise do Consultor:</strong>
                <p style="margin-top: 5px; font-style: italic; color: #555; line-height: 1.5;">"{insight}"</p>
            </div>
            <h3 style="color: #0056b3; border-bottom: 2px solid #eee; padding-bottom: 5px;">📅 Performance Temporal</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f1f1f1; text-align: left;">
                    <th style="padding: 10px; border-bottom: 1px solid #ddd;">Período</th>
                    <th style="padding: 10px; border-bottom: 1px solid #ddd;">Faturamento</th>
                    <th style="padding: 10px; border-bottom: 1px solid #ddd;">Vendas</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>Ontem</b></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; color: #2e7d32;">R$ {metricas_ia['periodos']['Ontem']['valor']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{metricas_ia['periodos']['Ontem']['qtd']}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>Semana Atual</b></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; color: #1565c0;">R$ {metricas_ia['periodos']['Semana Atual']['valor']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{metricas_ia['periodos']['Semana Atual']['qtd']}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>Mês Atual</b></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; color: #333;">R$ {metricas_ia['periodos']['Mês Atual']['valor']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{metricas_ia['periodos']['Mês Atual']['qtd']}</td>
                </tr>
            </table>
            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <div style="flex: 1; background: #e3f2fd; padding: 10px; border-radius: 6px; text-align: center;">
                    <small style="color:#0277bd; font-weight:bold;">TICKET MÉDIO</small><br>
                    <span style="font-size: 18px;">R$ {metricas_ia['ticket_medio']}</span>
                </div>
                <div style="flex: 1; background: #fff3e0; padding: 10px; border-radius: 6px; text-align: center;">
                    <small style="color:#ef6c00; font-weight:bold;">TOP BAIRRO</small><br>
                    <span style="font-size: 16px;">{top_bairro}</span>
                </div>
            </div>
            <h3 style="color: #333; font-size: 16px; margin-top: 20px;">🏆 Top 5 Clientes (LTV)</h3>
            <ul style="padding-left: 20px; color: #444;">{lista_vips}</ul>
        </div>
        <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 11px; color: #999;">
            Gerado automaticamente por <strong>3D Consultoria</strong><br>
            Dados processados via MotherDuck Cloud
        </div>
    </div>
    """
    
    sender = os.environ.get("EMAIL_USER")
    pwd = os.environ.get("EMAIL_PASS")
    
    if sender:
        try:
            yag = yagmail.SMTP(sender, pwd)
            yag.send(to="leandro.lf.frazao@hotmail.com", subject=f"Relatório 3D - {datetime.now().strftime('%d/%m')}", contents=[html_body])
            print("Relatório enviado!")
        except Exception as e:
            send_telegram_alert(f"Erro envio email: {e}", level="error")
            raise e

if __name__ == "__main__":
    send_report()