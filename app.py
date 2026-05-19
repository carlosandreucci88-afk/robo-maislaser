import streamlit as st
import pandas as pd
import requests
import json
import time
import re

# CONFIGURAÇÕES DA API DO WHATSAPP (DADOS OFICIAIS DO SEU PAINEL META)
TOKEN_META = "EAH5107Jgp0EBRfBfJzQ4C9hDMDrqay8a0JofFrtyQwTE4k3qsksNFOFCvZC9wZCglKPzBFinTWeJdqD70FVyqoF4lNzodUZAZAxYNxd7ucgw42dTS3R0INJVIquzUrUAC8jZATHtZBxR1iOj0rTs1xo424lc0mtkxpB6gdDYZBWLD7lmvWZARZB1H7cYzCfyag6jKtwZDZD"
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
    
    # Remove ponto flutuante caso o pandas tenha lido como float (ex: 55119.0)
    num_str = str(numero).strip()
    if num_str.endswith('.0'):
        num_str = num_str[:-2]
        
    num_limpo = re.sub(r'\D', '', num_str)
    
    # Se o número não começar com o código do país (55), adiciona
    if not num_limpo.startswith('55') and num_limpo != '':
        num_limpo = '55' + num_limpo
        
    return num_limpo

def enviar_mensagem_whatsapp(nome, procedimento, unidade, telefone_destino):
    """Faz a chamada de API para a Meta enviando o modelo estruturado de forma direta."""
    url = f"https://graph.facebook.com/v20.0/{ID_TELEFONE_META}/messages"
    
    headers = {
        "Authorization": f"Bearer {TOKEN_META}",
        "Content-Type": "application/json"
    }
    
    # Força a conversão para string limpa tirando quebras de linha para não quebrar a API
    procedimento_limpo = str(procedimento).replace('\n', ' ').replace('\r', '').strip()
    
    payload = {
        "messaging_product": "whatsapp",
        "to": str(telefone_destino),
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
                        {"type": "text", "text": procedimento_limpo},  # {{2}} Serviço / Procedimentos Agrupados
                        {"type": "text", "text": str(unidade)}        # {{3}} Nome da unidade vindo do site
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

# SELEÇÃO DE UNIDADE DIRETO NA TELA
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
        total_original = len(df)
        
        # COLUNAS DO ARQUIVO REAL UNO
        colunas_necessarias = ['Cliente', 'Serviço', 'Telefone']
        verificacao_colunas = all(col in df.columns for col in colunas_necessarias)
        
        if not verificacao_colunas:
            st.error(f"Atenção: A planilha precisa conter exatamente as colunas: {', '.join(colunas_necessarias)}")
        else:
            # 🔄 TRATAMENTO ANTES DO AGRUPAMENTO PARA EVITAR ERROS NO TELEFONE
            df['Cliente'] = df['Cliente'].fillna('').astype(str).str.strip()
            df['Serviço'] = df['Serviço'].fillna('').astype(str).str.strip()
            
            # Limpa cada número individualmente na coluna antes de agrupar
            df['Telefone'] = df['Telefone'].apply(limpar_numero).fillna('').astype(str)
            
            # Agrupa os serviços em uma única linha por cliente/telefone separados por vírgula
            df_agrupado = df.groupby(['Cliente', 'Telefone'])['Serviço'].apply(lambda x: ', '.join(list(set(x)))).reset_index()
            df_agrupado = df_agrupado[['Cliente', 'Serviço', 'Telefone']]
            total_agrupado = len(df_agrupado)
            
            # Avisos de contagem na tela
            st.success(f"Planilha carregada com sucesso! Encontrados {total_original} registros originais.")
            st.info(f"🔄 Agrupamento concluído: Os serviços foram unidos por cliente. No total, serão disparadas apenas {total_agrupado} mensagens.")
            
            st.subheader(f"Visualização dos dados para envio ({unidade_selecionada}):")
            st.dataframe(df_agrupado.head())
            
            if st.button("Iniciar Disparos em Massa 🚀"):
                progresso = st.progress(0)
                status_texto = st.empty()
                
                sucessos = 0
                erros = 0
                total_linhas = len(df_agrupado)
                
                for index, linha in df_agrupado.iterrows():
                    nome_cliente = linha['Cliente']
                    procedimento = linha['Serviço']
                    celular_puro = linha['Telefone']
                    
                    telefone_formatado = celular_puro
                    
                    if telefone_formatado and len(telefone_formatado) >= 10:
                        status_texto.text(f"Enviando para {nome_cliente} ({telefone_formatado})...")
                        
                        # Dispara usando a função oficial mapeada
                        code, res = enviar_mensagem_whatsapp(nome_cliente, procedimento, unidade_selecionada, telefone_formatado)
                        
                        if code == 200 or code == 201:
                            sucessos += 1
                        else:
                            erros += 1
                            st.error(f"❌ Falha ao enviar para {nome_cliente} ({telefone_formatado}) | Código HTTP: {code} | Retorno: {json.dumps(res, ensure_ascii=False)}")
                    else:
                        erros += 1
                        st.error(f"⚠️ Número de telefone inválido ou ausente para o cliente: {nome_cliente} (Dado encontrado: {celular_puro})")
                    
                    # Controle de delay para respeitar as diretrizes da Meta
                    time.sleep(1.5)
                    
                    # Atualiza a barra de carregamento na tela
                    progresso.progress((index + 1) / total_linhas)
                
                status_texto.text("Processamento concluído!")
                if sucessos > 0:
                    st.balloons()
                st.success(f"Disparos finalizados! Sucessos: {sucessos} | Erros/Falhas: {erros}")
                
    except Exception as erro_geral:
        st.error(f"Erro ao processar o arquivo: {erro_geral}")

# Rodapé de controle interno
st.markdown("---")
st.caption("Desenvolvido para uso exclusivo interno da Maislaser.")
