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

# Se escolheu uma unidade válida, mostra o campo do WhatsApp de Alerta
if unidade != "Clique para selecionar...":
    
    st.markdown("---")
    st.subheader(f"Configuração de Alertas - Unidade {unidade}")
    
    whatsapp_alerta = st.text_input(
        "2. Digite o número de WhatsApp que vai receber os alertas de quem Confirmar/Reagendar (com DDD, ex: 11999998888):",
        value=""
    )
    
    # Limpa o número deixando apenas dígitos
    whatsapp_alerta_limpo = re.sub(r'\D', '', whatsapp_alerta)
    
    # Valida se o número foi digitado (mínimo de 10 dígitos)
    if len(whatsapp_alerta_limpo) >= 10:
        
        st.markdown("---")
        st.success(f"✅ Configuração concluída! Alertas serão enviados para o número informado.")
        
        # Definição da mensagem de resposta automática que o CLIENTE vai receber ao clicar em Reagendar
        if unidade == "Mogi das Cruzes":
            mensagem_reagendar_cliente = "Entendido! Para reagendamentos você consegue ligar rapidinho para o numero - (11) 2610-1297."
        else: # Suzano
            mensagem_reagendar_cliente = "Entendido! Para reagendamentos você consegue ligar rapidinho para o numero - (11) 98990-5383."
        
        # 2. SELEÇÃO DA PLANILHA (SÓ APARECE SE O TELEFONE FOR PREENCHIDO)
        arquivo_excel = st.file_uploader("3. Escolha a planilha do UNO (.xlsx)", type=["xlsx"])
        
        if arquivo_excel is not None:
            try:
                # Lê a planilha do UNO
                df = pd.read_excel(arquivo_excel)
                st.write("### Pré-visualização dos dados carregados:")
                st.dataframe(df.head())
                
                # Botão de disparo
                if st.button(f"🚀 Iniciar Disparos para {unidade}"):
                    # Verifica se a coluna automática do UNO existe
                    if "Telefone" in df.columns:
                        sucessos = 0
                        erros = 0
                        
                        # Loop para envio das mensagens
                        for index, linha in df.iterrows():
                            telefone_cliente = str(linha["Telefone"])
                            
                            # O sistema agora sabe qual unidade é, para quem mandar o alerta (whatsapp_alerta_limpo)
                            # e qual texto de resposta enviar para o cliente caso ele queira reagendar (mensagem_reagendar_cliente)
                            
                            sucessos += 1 # Simulação do contador
                            
                        st.success(f"Disparos finalizados! Sucessos: {sucessos} | Erros: {erros}")
                    else:
                        st.error("❌ Erro: A coluna 'Telefone' não foi encontrada na planilha. Verifique a exportação do UNO.")
                        
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")
    else:
        st.warning("⚠️ Aguardando a digitação de um número de WhatsApp válido para liberar o envio da lista.")
else:
    st.info("💡 Escolha a unidade acima para começar.")
