import duckdb
import yagmail
import os
import pandas as pd
from datetime import datetime
from openai import OpenAI

# --- CONFIGURAÇÃO DO CLIENTE (O "Cérebro" do Agente) ---
# No futuro, isso pode vir de um arquivo config.yaml ou banco de dados
CONFIG_CLIENTE = {
    "nome_empresa": "Barbearia Teste",
    "tipo_negocio": "Barbearia Clássica e Estética Masculina",
    "foco_estrategico": "Aumentar recorrência de cortes e venda de produtos (pomadas/óleos).",
    "tom_de_voz": "Profissional, parceiro e motivador."
}

def get_ai_analysis(metricas):
    """
    Função Genérica: Transforma dados brutos em consultoria estratégica
    usando o Template Mestre de Prompt.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "IA indisponível (Chave não configurada)."

    client = OpenAI(api_key=api_key)

    # 1. Prompt do Sistema (A "Persona")
    system_prompt = f"""
    Você é um Consultor de Negócios Sênior da 3D Consultoria.
    Seu cliente atual é: {CONFIG_CLIENTE['nome_empresa']}, um negócio do tipo: {CONFIG_CLIENTE['tipo_negocio']}.
    
    OBJETIVO: {CONFIG_CLIENTE['foco_estrategico']}
    TOM DE VOZ: {CONFIG_CLIENTE['tom_de_voz']}
    
    Sua missão é analisar as métricas diárias e fornecer 1 (UM) insight acionável e curto.
    Não seja genérico. Use os números fornecidos para justificar sua dica.
    """

    # 2. Prompt do Usuário (Os Dados + Regras de Decisão)
    user_prompt = f"""
    Aqui estão os dados atualizados de hoje ({datetime.now().strftime('%d/%m/%Y')}):

    MÉTRICAS:
    - Total de Clientes: {metricas.get('total', 0)}
    - Novos Clientes (Semana): {metricas.get('novos', 0)}
    - Idade Média do Público: {metricas.get('idade_media', 0)} anos
    - Aniversariantes do Mês: {metricas.get('aniversariantes', 0)}

    REGRA DE PRIORIDADE PARA O INSIGHT (Siga estritamente):
    1. URGENTE: Se houver > 0 aniversariantes, sugira uma ação de fidelização para eles.
    2. ATENÇÃO: Se a idade média for < 25, sugira trends/Instagram. Se > 40, sugira conforto/serviços clássicos.
    3. PADRÃO: Se nada acima se destacar, sugira uma técnica para pedir avaliações no Google ou Upsell de produtos.

    SAÍDA ESPERADA:
    Escreva apenas o parágrafo do insight. Máximo 3 linhas.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro na API OpenAI: {e}")
        return "Não foi possível gerar a análise estratégica hoje."

def send_report():
    print(">>> [3/3] Iniciando Agente Inteligente 3D Consultoria...")
    
    # --- 1. Engenharia de Dados (DuckDB) ---
    con = duckdb.connect(database='data/barbearia.duckdb', read_only=True)
    
    try:
        query_check = "SELECT * FROM mart_clientes LIMIT 1"
        con.execute(query_check)
        table_name = "mart_clientes"
    except Exception:
        table_name = "read_csv_auto('data/raw_customers.csv')"

    # Carrega dados para Pandas
    df = con.execute(f"SELECT * FROM {table_name}").df()
    
    # --- 2. Análise Exploratória Automática ---
    # Identificação inteligente de colunas
    coluna_nome = df.columns[0]
    coluna_nasc = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'nome' in col_lower or 'name' in col_lower or 'cliente' in col_lower:
            coluna_nome = col
        if 'nasc' in col_lower or 'birth' in col_lower or 'data' in col_lower:
            coluna_nasc = col

    # Cálculos Demográficos
    media_idade = 0
    aniversariantes_mes = 0
    now = datetime.now()

    if coluna_nasc:
        df['data_obj'] = pd.to_datetime(df[coluna_nasc], dayfirst=True, errors='coerce')
        # Calcula idade
        df['idade'] = df['data_obj'].apply(
            lambda x: now.year - x.year - ((now.month, now.day) < (x.month, x.day)) 
            if pd.notnull(x) else None
        )
        media_idade = df['idade'].mean() if not df['idade'].isnull().all() else 0
        # Conta aniversariantes
        aniversariantes_mes = df[df['data_obj'].dt.month == now.month].shape[0]

    # Prepara o Dicionário de Métricas para a IA
    metricas_para_ia = {
        "total": len(df),
        "novos": 3, # Num cenário real, viria de um filtro 'created_at > x'
        "idade_media": int(media_idade),
        "aniversariantes": aniversariantes_mes
    }

    # --- 3. Chamada do Agente (IA) ---
    print(f"Enviando dados para o Consultor Virtual... (Idade Média: {int(media_idade)})")
    insight_ia = get_ai_analysis(metricas_para_ia)

    # --- 4. Geração do HTML (Front-end do Email) ---
    # Lista de nomes
    lista_html = ""
    for nome in df[coluna_nome].head(8):
        lista_html += f"<li style='margin-bottom: 4px;'>{str(nome).title()}</li>"

    # Box de Estatísticas
    stats_box = ""
    if media_idade > 0:
        stats_box = f"""
        <div style="display: flex; gap: 15px; margin: 20px 0;">
            <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; flex: 1; text-align: center; border: 1px solid #eee;">
                <span style="font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px;">Idade Média</span><br>
                <strong style="font-size: 20px; color: #333;">{int(media_idade)}</strong> <small>anos</small>
            </div>
            <div style="background: #e8f5e9; padding: 10px; border-radius: 6px; flex: 1; text-align: center; border: 1px solid #c8e6c9;">
                <span style="font-size: 11px; color: #2e7d32; text-transform: uppercase; letter-spacing: 1px;">Aniversariantes</span><br>
                <strong style="font-size: 20px; color: #2e7d32;">{aniversariantes_mes}</strong>
            </div>
        </div>
        """

    date_now = now.strftime('%d/%m/%Y')
    
    html_body = f"""
    <div style="background-color: #ffffff; color: #000000; padding: 30px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px;">
        
        <div style="border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #333;">📊 Resumo Executivo</h2>
            <p style="margin: 5px 0 0; color: #777; font-size: 14px;">{CONFIG_CLIENTE['nome_empresa']} • {date_now}</p>
        </div>

        <p style="font-size: 16px; margin-bottom: 10px;">Base Total de Clientes:</p>
        <div style="font-size: 36px; font-weight: bold; color: #007bff; margin-bottom: 20px;">
            {len(df)}
        </div>
        
        {stats_box}
        
        <div style="background-color: #f0f7ff; border-left: 4px solid #0056b3; padding: 20px; border-radius: 4px; margin: 25px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 20px; margin-right: 10px;">🤖</span>
                <strong style="color: #0056b3;">Insight Estratégico do Dia:</strong>
            </div>
            <p style="font-style: italic; color: #444; line-height: 1.6; margin: 0;">
                "{insight_ia}"
            </p>
        </div>
        
        <h3 style="color: #333; font-size: 18px; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
            Cadastros Recentes
        </h3>
        <ul style="color: #555; padding-left: 20px; line-height: 1.8;">
            {lista_html}
        </ul>
        
        <div style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #999; font-size: 12px;">
            <p>Gerado automaticamente por <strong>3D Consultoria de Dados</strong></p>
        </div>
    </div>
    """

    # --- 5. Envio ---
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "leandro.lf.frazao@hotmail.com" # Em prod, isso viria do CONFIG_CLIENTE

    if not sender_email:
        print("ERRO: Credenciais de email ausentes.")
        return

    try:
        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(
            to=receiver_email,
            subject=f"Resumo Estratégico: {date_now}",
            contents=[html_body]
        )
        print("Relatório enviado com sucesso!")
    except Exception as e:
        print(f"Erro no envio: {e}")
        raise e

if __name__ == "__main__":
    send_report()