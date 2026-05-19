import streamlit as st
import pandas as pd
import requests
import json
import time
import re

# CONFIGURAÇÕES DA API DO WHATSAPP
TOKEN_META = "EAH5107Jgp0EBRfBfJzQ4C9hDMDrqay8a0JofFrtyQwTE4k3qsksNFOFCvZC9wZCglKPzBFinTWeJdqD70FVyqoF4lNzodUZAZAxYNxd7ucgw42dTS3R0INJVIquzUrUAC8jZATHtZBxR1iOj0rTs1xo424lc0mtkxpB6gdDYZBWLD7lmvWZARZB1H7cYzCfyag6jKtwZDZD"
ID_TELEFONE_META = "1083951441475080"
NOME_MODELO_MENSAGEM = "hello_world"  # Trocado para o modelo padrão sem variáveis

st.set_page_config(page_title="Teste de Disparo Maislaser", page_icon="✨", layout="centered")
st.title("🧪 Teste de Conexão API — Maislaser")

def limpar_numero(numero):
    if pd.isna(numero):
        return None
    num_str = str(numero).strip()
    if num_str.endswith('.0'):
        num_str = num_str[:-2]
    num_limpo = re.sub(r'\D', '', num_str)
    if not num_limpo.startswith('55') and num_limpo != '':
        num_limpo = '55' + num_limpo
    return num_limpo

def enviar_mensagem_teste(telefone_destino):
    url = f"https://graph.facebook.com/v25.0/{ID_TELEFONE_META}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN_META}",
        "Content-Type": "application/json"
    }
    # Payload limpo, sem componentes ou parâmetros, exato para o hello_world
    payload = {
        "messaging_product": "whatsapp",
        "to": str(telefone_destino),
        "type": "template",
        "template": {
            "name": NOME_MODELO_MENSAGEM,
            "language": {
                "code": "en_US"
            }
        }
    }
    try:
        resposta = requests.post(url, headers=headers, json=payload)
        return resposta.status_code, resposta.json()
    except Exception as e:
        return 500, {"error": str(e)}

arquivo_upload = st.file_uploader("Suba a planilha do UNO para testar o envio do modelo padrão", type=["xlsx"])

if arquivo_upload is not None:
    try:
        df = pd.read_excel(arquivo_upload)
        df['Cliente'] = df['Cliente'].fillna('').astype(str).str.strip()
        df['Telefone'] = df['Telefone'].apply(limpar_numero).fillna('').astype(str)
        df_agrupado = df.groupby(['Cliente', 'Telefone']).size().reset_index()

        st.dataframe(df_agrupado.head())

        if st.button("Executar Teste de Envio 🚀"):
            for index, row in df_agrupado.iterrows():
                tel = row['Telefone']
                nome = row['Cliente']
                if tel and len(tel) >= 10:
                    st.write(f"Tentando enviar teste para {nome} ({tel})...")
                    code, res = enviar_mensagem_teste(tel)
                    if code == 200 or code == 201:
                        st.success(f"✅ Conexão funcionando! Mensagem entregue com sucesso.")
                    else:
                        st.error(f"❌ Falha | Código HTTP: {code} | Resposta: {json.dumps(res)}")
                time.sleep(1.5)
    except Exception as e:
        st.error(f"Erro: {e}")
