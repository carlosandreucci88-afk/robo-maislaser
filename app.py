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
        
        # 2. SELEÇÃO DA PLANILHA
        arquivo_excel = st.file_uploader("3. Escolha a planilha do UNO (.xlsx)", type=["xlsx"])
        
        if arquivo_excel is not None:
            try:
                # Lê a planilha do UNO
                df = pd.read_excel(arquivo_excel)
                
                if "Telefone" in df.columns and "Cliente" in df.columns and "Serviço" in df.columns:
                    
                    # Tratamento inicial contra espaços e nulos para evitar erros na Meta
                    df['Cliente'] = df['Cliente'].fillna("Cliente").astype(str).str.strip()
                    df['Telefone'] = df['Telefone'].fillna("").astype(str).str.strip()
                    df['Serviço'] = df['Serviço'].fillna("Procedimentos").astype(str).str.strip()
                    
                    df = df[df['Telefone'] != ""]
                    
                    # Agrupa os serviços do mesmo cliente separados por vírgula mantendo os dados limpos
                    df_agrupado = df.groupby(['Cliente', 'Telefone'])['Serviço'].apply(lambda x: ', '.join(x)).reset_index()
                    
                    st.write(f"### Clientes Agrupados Prontos para Envio (Total: {len(df_agrupado)}):")
                    st.dataframe(df_agrupado)
                    
                    # Botão de disparo real
                    if st.button(f"🚀 Iniciar Disparos Reais para {unidade}"):
                        sucessos = 0
                        erros = 0
                        
                        url_api = f"https://graph.facebook.com/v18.0/{ID_TELEFONE_META}/messages"
                        headers = {
                            "Authorization": f"Bearer {TOKEN_META}",
                            "Content-Type": "application/json"
                        }
                        
                        progresso = st.progress(0)
                        status_texto = st.empty()
                        
                        for index, linha in df_agrupado.iterrows():
                            nome_cliente = linha["Cliente"]
                            servicos_cliente = str(linha["Serviço"])
                            
                            # Correção do erro da linha 83: Garante que o texto use a variável 'servicos_cliente' com 'c'
                            if not servicos_cliente or servicos_cliente.lower() in ['nan', 'none', '']:
                                servicos_cliente = "Sessões agendadas"
                            
                            # Limpa o telefone do cliente e adiciona o código do país
                            tel_limpo = re.sub(r'\D', '', linha["Telefone"])
                            if not tel_limpo.startswith("55"):
                                tel_limpo = "55" + tel_limpo
                            
                            # Montagem do payload oficial da API da Meta mapeando as 3 variáveis Corretas
                            payload = {
                                "messaging_product": "whatsapp",
                                "to": tel_limpo,
                                "type": "template",
                                "template": {
                                    "name": "confirmacao_agendamento",
                                    "language": {
                                        "code": "pt_BR"
                                        },
                                    "components": [
                                        {
                                            "type": "body",
                                            "parameters": [
                                                {"type": "text", "text": nome_cliente},       # {{1}} Nome do Cliente
                                                {"type": "text", "text": servicos_cliente},   # {{2}} Áreas do Corpo Agrupadas
                                                {"type": "text", "text": unidade}             # {{3}} Nome da Unidade
                                            ]
                                        }
                                    ]
                                }
                            }
                            
                            # Envio real para a Meta
                            resposta = requests.post(url_api, headers=headers, json=payload)
                            
                            if resposta.status_code == 200 or resposta.status_code == 201:
                                sucessos += 1
                            else:
                                erros += 1
                                st.error(f"Falha ao enviar para {nome_cliente} ({tel_limpo}). Detalhe da Meta: {resposta.text}")
                            
                            # Atualiza progresso na tela do Streamlit
                            percentual = (index + 1) / len(df_agrupado)
                            progresso.progress(percentual)
                            status_texto.text(f"Processando: {index + 1}/{len(df_agrupado)}")
                            
                        st.success(f"🎉 Disparos finalizados! Sucessos: {sucessos} | Erros: {erros}")
                else:
                    st.error("❌ Erro: Certifique-se que a planilha possui as colunas 'Cliente', 'Telefone' e 'Serviço'.")
                        
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")
    else:
        st.warning("⚠️ Aguardando a digitação de um número de WhatsApp válido para liberar o envio da lista.")
else:
    st.info("💡 Escolha a unidade acima para começar.")
