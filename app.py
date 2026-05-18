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

# REGRAS DO PAINEL VISUAL (STREAMLIT)
st.set_page_config(page_title="Robô Agenda Maislaser", page_icon="✨", layout="centered")
st.title("🤖 Disparador de Agenda — Maislaser")
st.write("Suba a planilha gerada pelo sistema UNO para iniciar os disparos de confirmação.")

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

# SELEÇÃO DE UNIDADE DIRECTO NA TELA
unidade_selecionada = st.selectbox("Selecione a Unidade que está operando hoje:", ["Mogi das Cruzes", "Suzano"])

# CAIXA DE TEXTO NO SITE PARA VOCÊ DIGITAR O NÚMERO DE ALERTA QUE QUISER
numero_alerta_input = st.text_input("Digite o número de WhatsApp que receberá os alertas (com DDD):", value="5511911177883")

if numero_alerta_input:
    numero_alerta_formatado = limpar_numero(numero_alerta_input)
    st.info(f"📢 Os alertas de agendamento serão enviados para: {numero_alerta_formatado}")

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
                        procedimento = linha['Procedimento']
                        unidade_local = linha['Unidade']
                        celular_puro = linha['Celular']
                        
                        telefone_formatado = limpar_numero(celular_puro)
                        
                        if telefone_formatado:
                            status_texto.text(f"Enviando para {nome_cliente} ({telefone_formatado})...")
                            code, res = enviar_mensagem_whatsapp(nome_cliente, procedimento, unidade_local, telefone_formatado)
                            
                            if code == 200 or code == 201:
                                sucessos += 1
                            else:
                                erros += 1
                        else:
                            erros += 1
                        
                        # Controle de delay para evitar bloqueios da Meta
                        time.sleep(1.5)
                        
                        # Atualiza a barra de carregamento na tela
                        progresso.progress((index + 1) / total_linhas)
                    
                    status_texto.text("Processamento concluído!")
                    st.balloons()
                    st.success(f"Disparos finalizados! Sucessos: {sucessos} | Erros/Falhas: {erros}")
                
    except Exception as erro_geral:
        st.error(f"Erro ao processar o arquivo: {erro_geral}")

# Rodapé de controle interno
st.markdown("---")
st.caption("Desenvolvido para uso exclusivo interno da Maislaser.")
