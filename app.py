import streamlit as st
import pandas as pd
import requests
import json
import time
import re

# CONFIGURAÇÕES DA API DO WHATSAPP (DADOS OFICIAIS DO SEU PAINEL META)
TOKEN_META = "EAAPbXbAnA9IBO7SgZAnK6LwW0p2XFqWnS2z6fS1U6EZAAnM7q9ZA1Qd7e8gB4hV7Xb1ZBf2ZB0V9ZA5C6D8E4ZA9F0ZA1ZA8ZB2hZA7ZA2C5E4D3E2F1G0H9I8J7K6L5M4N3O2P1Q"
ID_TELEFONE_META = "1083951441475080"
NOME_MODELO_MENSAGEM = "confirmacao_agenda_maislaser"

# NUMERO QUE RECEBE OS ALERTAS DE RESPOSTAS DOS CLIENTES
NUMERO_ALERTA_INTERNO = "5511911177883" 

def limpar_numero(numero):
    """Limpa o número deixando apenas dígitos e garante o formato correto internacional."""
    if pd.isna(numero):
        return None
    num_str = str(numero).strip()
    num_limpo = re.sub(r'\D', '', num_str)
    
    # Se o número não começar com o código do país (55), adiciona
    if not num_limpo.startswith('55'):
        num_limpo = '55' + num_limpo
        
    return num_limpo

def enviar_mensagem_whatsapp(nome, procedimento, unidade, telefone_destino):
    """Faz a chamada de API para a Meta enviando o modelo estruturado com as 3 variáveis."""
    url = f"https://graph.facebook.com/v25.0/{ID_TELEFONE_META}/messages"
    
    headers = {
        "Authorization": f"Bearer {TOKEN_META}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone_destino,
        "type": "template",
        "template": {
            "name": NOME_MODELO_MENSAGEM,
            "language": {
                "code": "pt_BR"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(nome)},          # {{1}} Nome do cliente
                        {"type": "text", "text": str(procedimento)},  # {{2}} Procedimento(s)
                        {"type": "text", "text": str(unidade)}        # {{3}} Nome da unidade
                    ]
                }
            ]
        }
    }
    
    try:
        resposta = requests.post(url, headers=headers, json=payload)
        return resposta.status_code, resposta.json()
    except Exception as e:
        return 500, {"error": str(e)}

# REGRAS DO PAINEL VISUAL (STREAMLIT)
st.set_page_config(page_title="Robô Agenda Maislaser", page_icon="✨", layout="centered")
st.title("🤖 Disparador de Agenda — Maislaser")
st.write("Suba a planilha gerada pelo sistema UNO para iniciar os disparos de confirmação.")

# SELEÇÃO DE UNIDADE QUE EU TINHA APAGADO
unidade_selecionada = st.selectbox("Selecione a Unidade que está operando hoje:", ["Mogi das Cruzes", "Suzano"])

str_alerta = f"📢 Os alertas de agendamento serão enviados para o número: {NUMERO_ALERTA_INTERNO}"
st.info(str_alerta)

arquivo_upload = st.file_uploader("Selecione a planilha do UNO (.xlsx)", type=["xlsx"])

if arquivo_upload is not None:
    try:
        df = pd.read_excel(arquivo_upload)
        st.success(f"Planilha carregada com sucesso! Encontrados {len(df)} registros para a unidade {unidade_selecionada}.")
        
        # Mapeamento das colunas esperadas na planilha do UNO
        colunas_necessarias = ['Cliente', 'Procedimento', 'Unidade', 'Celular']
        verificacao_colunas = all(col in df.columns for col in colunas_necessarias)
        
        if not verificacao_colunas:
            st.error(f"Atenção: A planilha precisa conter exatamente as colunas: {', '.join(colunas_necessarias)}")
        else:
            # Filtra os dados com base na unidade selecionada no painel
            df_filtrado = df[df['Unidade'].str.contains(unidade_selecionada, case=False, na=False)]
            
            st.subheader(f"Visualização dos dados ({unidade_selecionada}):")
            st.dataframe(df_filtrado[colunas_necessarias].head())
            
            if len(df_filtrado) == 0:
                st.warning(f"Nenhum cliente encontrado na planilha para a unidade {unidade_selecionada}.")
            else:
                if st.button("Iniciar Disparos em Massa 🚀"):
                    progresso = st.progress(0)
                    status_texto = st.empty()
                    
                    sucessos = 0
                    erros = 0
                    total_linhas = len(df_filtrado)
                    
                    for index, (idx_orig, linha) in enumerate(df_filtrado.iterrows()):
                        nome_cliente = linha['Cliente']
                        procedimento = linha
