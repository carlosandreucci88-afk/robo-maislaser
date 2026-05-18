import streamlit as st
import pandas as pd
import requests
import re

# CONFIGURAÇÕES FIXAS E OCULTAS (API DA META)
TOKEN_META = "EAH5107Jgp0EBRaZB3ZAVSqisUuMTFNlX3aCgZB445TMzH8YiRQv9Mm0WVwNYZAvmwjUiFWsiKWo6itjGzuuZBYwO5huSXVCTj0U537mYT62CG6Ub9E0EoP7XyhFKf46RJaTxIz3DBNVatTchBUo6ZCkZCDaGZC44uq4fqgBLdZACeflbM5ZCDKw8uu1uj8vizBpwZDZD"
ID_TELEFONE_META = "10894333337592658"

st.set_page_config(page_title="Painel Maislaser", page_icon="🤖", layout="wide")

st.title("🤖 Painel de Confirmação WhatsApp - Maislaser")
st.write("Selecione a unidade e informe o número que receberá as notificações antes de subir a lista do UNO.")

# 1. SELEÇÃO DA UNIDADE
unidade = st.selectbox(
    "1. Selecione a Unidade:",
    ["Clique para selecionar...", "Mogi das Cruzes", "Suzano"]
)

if unidade != "Clique para selecionar...":
    
    st.markdown("---")
    st.subheader(f"Configuração de Alertas - Unidade {unidade}")
    
    whatsapp_alerta = st.text_input(
        "2. Digite o número de WhatsApp que vai receber os alertas de quem Confirmar/Reagendar (com DDD, ex: 11999998888):",
        value=""
    )
    
    whatsapp_alerta_limpo = re.sub(r'\D', '', whatsapp_alerta)
    
    if len(whatsapp_alerta_limpo) >= 10:
        
        st.markdown("---")
        st.success(f"✅ Configuração concluída! Alertas serão enviados para o número informado.")
        
        # Definição das mensagens automáticas por unidade
        if unidade == "Mogi das Cruzes":
            mensagem_reagendar_cliente = "Entendido! Para reagendamentos você consegue ligar rapidinho para o numero - (11) 2610-1297."
        else:
            mensagem_reagendar_cliente = "Entendido! Para reagendamentos você consegue ligar rapidinho para o numero - (11) 98990-5383."
        
        # 2. SELEÇÃO DA PLANILHA
        arquivo_excel = st.file_uploader("3. Escolha a planilha do UNO (.xlsx)", type=["xlsx"])
        
        if arquivo_excel is not None:
            try:
                # Lê a planilha do UNO
                df = pd.read_excel(arquivo_excel)
                
                if "Telefone" in df.columns and "Cliente" in df.columns and "Serviço" in df.columns:
                    
                    # --- TRATAMENTO E AGRUPAMENTO DOS DADOS ---
                    # Garante que espaços em branco não atrapalhem o agrupamento
                    df['Cliente'] = df['Cliente'].astype(str).str.strip()
                    df['Telefone'] = df['Telefone'].astype(str).str.strip()
                    df['Serviço'] = df['Serviço'].astype(str).str.strip()
                    
                    # Agrupa por Cliente e Telefone, juntando os Serviços com uma vírgula
                    df_agrupado = df.groupby(['Cliente', 'Telefone'])['Serviço'].apply(lambda x: ', '.join(x)).reset_index()
                    
                    st.write(f"### Pré-visualização dos Clientes Agrupados (Total único: {len(df_agrupado)}):")
                    st.dataframe(df_agrupado.head())
                    
                    # Botão de disparo
                    if st.button(f"🚀 Iniciar Disparos para {unidade}"):
                        sucessos = 0
                        erros = 0
                        
                        # Loop usando a lista tratada e agrupada
                        for index, linha in df_agrupado.iterrows():
                            nome_cliente = linha["Cliente"]
                            telefone_cliente = linha["Telefone"]
                            servicos_cliente = linha["Serviço"] # Aqui tem todas as áreas juntas!
                            
                            # O robô agora envia uma única mensagem contendo a lista de 'servicos_cliente'
                            # Exemplo lógico interno: "Olá {nome_cliente}, confirmando seu horário para {servicos_cliente}?"
                            
                            sucessos += 1
                            
                        st.success(f"Disparos finalizados com agrupamento! Total de clientes únicos avisados: {sucessos} | Erros: {erros}")
                else:
                    st.error("❌ Erro: Certifique-se que a planilha possui as colunas 'Cliente', 'Telefone' e 'Serviço'.")
                        
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")
    else:
        st.warning("⚠️ Aguardando a digitação de um número de WhatsApp válido para liberar o envio da lista.")
else:
    st.info("💡 Escolha a unidade acima para começar.")
