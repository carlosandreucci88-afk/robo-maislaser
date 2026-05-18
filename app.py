import streamlit as st
import pandas as pd
import requests
import re

# =========================================================================
# CREDENCIAIS DA META (Altere aqui se gerar um token definitivo/novo)
# =========================================================================
TOKEN_META = "EAH5107Jgp0EBRaZB3ZAVSqisUuMTFNlX3aCgZB445TMzH8YiRQv9Mm0WVwNYZAvmwjUiFWsiKWo6itjGzuuZBYwO5huSXVCTj0U537mYT62CG6Ub9E0EoP7XyhFKf46RJaTxIz3DBNVatTchBUo6ZCkZCDaGZC44uq4fqgBLdZACeflbM5ZCDKw8uu1uj8vizBpwZDZD"
ID_TELEFONE_META = "10894333337592658"
# =========================================================================

st.set_page_config(page_title="Painel Maislaser", page_icon="🤖", layout="wide")

st.title("🤖 Painel de Confirmação WhatsApp - Maislaser")
st.write("Selecione a unidade e informe o WhatsApp de alertas antes de carregar os dados do UNO.")

# 1. SELEÇÃO DA UNIDADE
unidade = st.selectbox(
    "1. Selecione a Unidade:",
    ["Clique para selecionar...", "Mogi das Cruzes", "Suzano"]
)

if unidade != "Clique para selecionar...":
    
    st.markdown("---")
    st.subheader(f"🏠 Configuração de Alertas - Unidade {unidade}")
    
    whatsapp_alerta = st.text_input(
        "2. Digite o número de WhatsApp que vai receber os alertas de quem Confirmar/Reagendar (com DDD, ex: 11999998888):",
        value=""
    )
    
    whatsapp_alerta_limpo = re.sub(r'\D', '', whatsapp_alerta)
    
    if len(whatsapp_alerta_limpo) >= 10:
        
        st.markdown("---")
        st.success(f"✅ Configuração de alertas salva para o número informado!")
        
        # 2. SELEÇÃO DA PLANILHA
        arquivo_excel = st.file_uploader("3. Escolha a planilha exportada do UNO (.xlsx)", type=["xlsx"])
        
        if arquivo_excel is not None:
            try:
                # Leitura dos dados do UNO
                df = pd.read_excel(arquivo_excel)
                
                if "Telefone" in df.columns and "Cliente" in df.columns and "Serviço" in df.columns:
                    
                    # Limpeza preventiva dos dados para não quebrar a API da Meta
                    df['Cliente'] = df['Cliente'].fillna("Cliente").astype(str).str.strip()
                    df['Telefone'] = df['Telefone'].fillna("").astype(str).str.strip()
                    df['Serviço'] = df['Serviço'].fillna("Procedimentos").astype(str).str.strip()
                    
                    df = df[df['Telefone'] != ""]
                    
                    # Agrupa serviços do mesmo cliente e monta a lista de envios unificados
                    df_agrupado = df.groupby(['Cliente', 'Telefone'])['Serviço'].apply(lambda x: ', '.join(x)).reset_index()
                    
                    st.write(f"### Clientes Agrupados Prontos para Envio (Total de mensagens únicas: {len(df_agrupado)}):")
                    st.dataframe(df_agrupado)
                    
                    # Ação do Botão de Disparo
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
                            
                            if not servicos_cliente or servicos_cliente.lower() in ['nan', 'none', '']:
                                servicos_cliente = "Sessões agendadas"
                            
                            # Ajuste de DDI do Brasil para envio correto
                            tel_limpo = re.sub(r'\D', '', linha["Telefone"])
                            if not tel_limpo.startswith("55"):
                                tel_limpo = "55" + tel_limpo
                            
                            # JSON estruturado para o template aprovado 'confirmacao_agenda_maislaser'
                            payload = {
                                "messaging_product": "whatsapp",
                                "to": tel_limpo,
                                "type": "template",
                                "template": {
                                    "name": "confirmacao_agenda_maislaser",
                                    "language": {
                                        "code": "pt_BR"
                                    },
                                    "components": [
                                        {
                                            "type": "body",
                                            "parameters": [
                                                {"type": "text", "text": nome_cliente},       # {{1}} Nome do Cliente
                                                {"type": "text", "text": servicos_cliente},   # {{2}} Serviços Agrupados
                                                {"type": "text", "text": unidade}             # {{3}} Unidade Selecionada
                                            ]
                                        }
                                    ]
                                }
                            }
                            
                            # Requisição Post para a Meta
                            resposta = requests.post(url_api, headers=headers, json=payload)
                            
                            if resposta.status_code in [200, 201]:
                                sucessos += 1
                            else:
                                erros += 1
                                # Tratamento visual amigável para expiração de tokens
                                if "missing permissions" in resposta.text.lower() or "does not exist" in resposta.text.lower():
                                    st.error(f"❌ Erro crítico com as credenciais da Meta ao tentar enviar para {nome_cliente}. Provavelmente seu Token de Acesso expirou lá no painel do Facebook. Por favor, gere um novo Token e atualize o código.")
                                    break
                                else:
                                    st.error(f"Falha ao enviar para {nome_cliente} ({tel_limpo}). Erro: {resposta.text}")
                            
                            # Barra de progresso visual do Streamlit
                            percentual = (index + 1) / len(df_agrupado)
                            progresso.progress(percentual)
                            status_texto.text(f"Processando envios: {index + 1}/{len(df_agrupado)}")
                            
                        if erros == 0 and sucessos > 0:
                            st.success(f"🎉 Excelente! Todos os {sucessos} disparos unificados foram enviados com sucesso!")
                        elif sucessos > 0:
                            st.warning(f"⚠️ Envios finalizados de forma parcial. Sucessos: {sucessos} | Erros encontrados: {erros}")
                else:
                    st.error("❌ Formato inválido: A planilha precisa conter obrigatoriamente as colunas 'Cliente', 'Telefone' e 'Serviço'.")
                        
            except Exception as e:
                st.error(f"Erro ao processar arquivo excel: {e}")
    else:
        st.warning("⚠️ Insira um número de WhatsApp de alertas válido com DDD para liberar a área de upload.")
else:
    st.info("💡 Selecione uma das unidades no campo acima para carregar o sistema.")
