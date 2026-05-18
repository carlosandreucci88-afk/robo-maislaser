import streamlit as st
import pandas as pd
import requests
import json

# Configuração da página do sistema
st.set_page_config(page_title="Painel Maislaser", page_icon="🤖", layout="centered")

st.title("🤖 Painel de Confirmações WhatsApp - Maislaser")
st.write("Suba a planilha do UNO para disparar as mensagens de confirmação.")

st.sidebar.header("Configuração da API")
token = st.sidebar.text_input("Token do WhatsApp", type="password")
phone_number_id = st.sidebar.text_input("ID do Telefone (Meta)")

# Área para arrastar e soltar a planilha do UNO
uploaded_file = st.sidebar.file_uploader("Escolha a planilha do UNO (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Planilha carregada com sucesso!")
        st.dataframe(df.head())
        
        if st.button("🚀 Iniciar Disparos"):
            if not token or not phone_number_id:
                st.error("Por favor, preencha o Token e o ID do Telefone na barra lateral!")
            else:
                st.info("Processando disparos... Acompanhe o status abaixo.")
                # Aqui roda a lógica de leitura e envio
                
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
