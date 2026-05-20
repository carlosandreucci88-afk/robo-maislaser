import streamlit as st
import pandas as pd
import requests
import json
import time
import re

# ============================================================
# CONFIGURAÇÕES DA API DO WHATSAPP (v25.0)
# ============================================================
TOKEN_META = "EAH5107Jgp0EBRqYdYtXD9kD2USkbZAZCSh8AaLpC8kX7YvXZBMDz22yTQtQqH5ozWpxRUKFcd6Ys8awcevFXazXn8TT9IHcGJ47Vb4JrvRrLkbX0TGLz5GFahYOG4jOaXcnWp7jKYzhBt1ORsNVl9hVdFwMEjmEvDI6tJr8RRBFZBDrvxROZBP7MLtrncBQZDZD"
ID_TELEFONE_META = "1083951441475080"
NOME_MODELO_MENSAGEM = "confirmacao_agenda_maislaser"

# URL do Google Apps Script (webhook) — preencha após publicar o script
# Exemplo: "https://script.google.com/macros/s/SEU_ID_AQUI/exec"
URL_WEBHOOK_CONTEXTO = "https://script.google.com/macros/s/AKfycbxRXgNsIL8J1uHCfS_E9HjXEorFSiHtlN9v7q9LHEVwzbG0lIG6aw-8Id9CmoawS52v/exec"

# ============================================================
# CONFIGURAÇÕES DO PAINEL VISUAL (STREAMLIT)
# ============================================================
st.set_page_config(page_title="Robô Agenda Maislaser", page_icon="✨", layout="centered")
st.title("🤖 Disparador de Agenda — Maislaser")
st.write("Suba a planilha gerada pelo sistema UNO para iniciar os disparos de confirmação.")

# ============================================================
# FUNÇÃO: Limpar número de telefone
# ============================================================
def limpar_numero(numero):
    """
    Limpa o número deixando apenas dígitos e garante o formato
    correto internacional com DDI 55 (Brasil).
    Trata casos onde o pandas lê como float (ex: 5511999990000.0)
    """
    if pd.isna(numero):
        return None

    num_str = str(numero).strip()

    # Remove ponto flutuante gerado pelo pandas (ex: 55119999.0 → 55119999)
    if num_str.endswith('.0'):
        num_str = num_str[:-2]

    # Remove tudo que não for dígito
    num_limpo = re.sub(r'\D', '', num_str)

    if num_limpo == '':
        return None

    # ✅ CORREÇÃO: Evita duplicar o 55 — verifica se JÁ começa com 55
    # e se o comprimento faz sentido para um número brasileiro com DDI
    # Número brasileiro com DDI: 55 + DDD (2) + número (8 ou 9) = 12 ou 13 dígitos
    if num_limpo.startswith('55') and len(num_limpo) >= 12:
        return num_limpo  # Já está correto, não adiciona 55 novamente
    elif not num_limpo.startswith('55'):
        return '55' + num_limpo
    else:
        return num_limpo

# ============================================================
# FUNÇÃO: Limpar nome do serviço para exibição na mensagem
# ============================================================
def limpar_nome_servico(servico):
    """
    Remove os prefixos 'F - ' e 'M - ' que o sistema UNO adiciona
    nos serviços (F = Feminino, M = Masculino).
    Deixa o nome mais limpo e natural na mensagem do cliente.
    Ex: 'F - Depilação de Axilas cortesia' → 'Depilação de Axilas'
    Também remove sufixos como 'cortesia', '(área P)', etc.
    """
    if pd.isna(servico) or str(servico).strip() == '':
        return ''

    s = str(servico).strip()

    # Remove prefixo de gênero 'F - ' ou 'M - '
    s = re.sub(r'^[FM]\s*-\s*', '', s)

    # Remove indicadores de área como '(área P)', '(área M)', '(área G)'
    s = re.sub(r'\(área\s*[A-Z]\)', '', s, flags=re.IGNORECASE)

    # Remove a palavra 'cortesia' no final (case insensitive)
    s = re.sub(r'\bcortesia\b', '', s, flags=re.IGNORECASE)

    # Remove espaços duplos e trim
    s = re.sub(r'\s+', ' ', s).strip()

    # Remove vírgula ou hífen no final se sobrar
    s = s.rstrip(',-').strip()

    return s

# ============================================================
# FUNÇÃO: Enviar mensagem via WhatsApp Cloud API
# ============================================================
def enviar_mensagem_whatsapp(nome, procedimento, unidade, telefone_destino):
    """
    Faz a chamada de API para a Meta enviando o modelo estruturado
    na versão nativa v25.0.
    """
    url = f"https://graph.facebook.com/v25.0/{ID_TELEFONE_META}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN_META}",
        "Content-Type": "application/json"
    }

    # Garante que quebras de linha não quebrem a API
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
                        {"type": "text", "text": str(nome)},           # {{1}} Nome do cliente
                        {"type": "text", "text": procedimento_limpo},  # {{2}} Serviço(s) agrupados
                        {"type": "text", "text": str(unidade)}         # {{3}} Nome da unidade
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

# ============================================================
# INTERFACE — SELEÇÃO DE UNIDADE E NÚMERO DE ALERTA
# ============================================================
unidade_selecionada = st.selectbox(
    "Selecione a Unidade que está operando hoje:",
    ["Mogi das Cruzes", "Suzano"]
)

numero_alerta_input = st.text_input(
    "Digite o número de WhatsApp que receberá os alertas (com DDD):",
    value=""
)

if numero_alerta_input:
    numero_alerta_formatado = limpar_numero(numero_alerta_input)
    st.info(f"📢 Os alertas de agendamento serão enviados para: {numero_alerta_formatado}")

# ============================================================
# UPLOAD DA PLANILHA
# ============================================================
arquivo_upload = st.file_uploader("Selecione a planilha do UNO (.xlsx)", type=["xlsx"])

if arquivo_upload is not None:
    try:
        df = pd.read_excel(arquivo_upload)
        total_original = len(df)

        # Colunas obrigatórias que o sistema UNO exporta
        colunas_necessarias = ['Cliente', 'Serviço', 'Telefone']
        verificacao_colunas = all(col in df.columns for col in colunas_necessarias)

        if not verificacao_colunas:
            st.error(
                f"❌ Atenção: A planilha precisa conter exatamente as colunas: "
                f"{', '.join(colunas_necessarias)}\n\n"
                f"Colunas encontradas: {', '.join(df.columns.tolist())}"
            )
        else:
            # --------------------------------------------------
            # ✅ CORREÇÃO 1: Filtrar apenas agendamentos ATIVOS
            # Ignora registros Cancelados, Faltou, Remarcado etc.
            # --------------------------------------------------
            if 'Situação' in df.columns:
                total_antes_filtro = len(df)
                df = df[df['Situação'].str.strip().str.lower() == 'agendado']
                total_filtrados = total_antes_filtro - len(df)
                if total_filtrados > 0:
                    st.warning(
                        f"⚠️ {total_filtrados} registro(s) ignorado(s) por não estarem "
                        f"com situação 'Agendado' (cancelados, faltou, etc.)."
                    )

            # --------------------------------------------------
            # LIMPEZA DOS DADOS
            # --------------------------------------------------
            df['Cliente'] = df['Cliente'].fillna('').astype(str).str.strip()
            df['Telefone'] = df['Telefone'].apply(limpar_numero).fillna('').astype(str)

            # ✅ CORREÇÃO 2: Limpa prefixos F-/M- e sufixos de área dos serviços
            df['Serviço'] = df['Serviço'].apply(limpar_nome_servico)

            # Converte data serial do Excel para horário legível
            df['Horario'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y às %Hh%M')

            # Remove linhas onde o serviço ficou vazio após limpeza
            df = df[df['Serviço'] != '']

            # --------------------------------------------------
            # AGRUPAMENTO: Une todos os serviços do mesmo cliente
            # Pega o primeiro horário encontrado por cliente/telefone
            # --------------------------------------------------
            df_servicos = (
                df.groupby(['Cliente', 'Telefone'])['Serviço']
                .apply(lambda x: ', '.join(sorted(set(x))))
                .reset_index()
            )
            df_horario = (
                df.groupby(['Cliente', 'Telefone'])['Horario']
                .first()
                .reset_index()
            )
            df_agrupado = df_servicos.merge(df_horario, on=['Cliente', 'Telefone'])
            df_agrupado = df_agrupado[['Cliente', 'Serviço', 'Telefone', 'Horario']]
            total_agrupado = len(df_agrupado)

            # --------------------------------------------------
            # EXIBIÇÃO DOS DADOS NA TELA
            # --------------------------------------------------
            st.success(
                f"✅ Planilha carregada com sucesso! "
                f"{len(df)} registros válidos encontrados."
            )
            st.info(
                f"🔄 Agrupamento concluído: serviços unidos por cliente. "
                f"Serão disparadas **{total_agrupado}** mensagens."
            )

            st.subheader(f"Pré-visualização dos disparos ({unidade_selecionada}):")
            st.dataframe(df_agrupado, use_container_width=True)

            # --------------------------------------------------
            # BOTÃO DE DISPARO
            # --------------------------------------------------
            if st.button("🚀 Iniciar Disparos em Massa"):
                progresso = st.progress(0)
                status_texto = st.empty()

                sucessos = 0
                erros = 0
                total_linhas = len(df_agrupado)

                for i, (_, linha) in enumerate(df_agrupado.iterrows()):
                    nome_cliente = linha['Cliente']
                    procedimento = linha['Serviço']
                    telefone_formatado = linha['Telefone']

                    if telefone_formatado and len(telefone_formatado) >= 12:
                        status_texto.text(
                            f"📤 Enviando {i+1}/{total_linhas}: "
                            f"{nome_cliente} ({telefone_formatado})..."
                        )

                        horario_cliente = linha['Horario']

                        code, res = enviar_mensagem_whatsapp(
                            nome_cliente, procedimento,
                            unidade_selecionada, telefone_formatado
                        )

                        if code in (200, 201):
                            sucessos += 1
                            # Salva contexto no webhook para processar respostas dos clientes
                            if URL_WEBHOOK_CONTEXTO:
                                try:
                                    requests.post(URL_WEBHOOK_CONTEXTO, json={
                                        "acao": "salvar_contexto",
                                        "telefone": telefone_formatado,
                                        "nome": nome_cliente,
                                        "servico": procedimento,
                                        "unidade": unidade_selecionada,
                                        "horario": horario_cliente,
                                        "numero_alerta": numero_alerta_formatado
                                    }, timeout=5)
                                except Exception:
                                    pass
                        else:
                            erros += 1
                            st.error(
                                f"❌ Falha — {nome_cliente} ({telefone_formatado}) | "
                                f"HTTP {code} | {json.dumps(res, ensure_ascii=False)}"
                            )
                    else:
                        erros += 1
                        st.error(
                            f"⚠️ Número inválido ou ausente para: "
                            f"{nome_cliente} (encontrado: '{telefone_formatado}')"
                        )

                    # Delay para respeitar limites de taxa da Meta
                    time.sleep(1.5)

                    # Atualiza barra de progresso
                    progresso.progress((i + 1) / total_linhas)

                status_texto.text("✅ Processamento concluído!")
                if sucessos > 0:
                    st.balloons()
                st.success(
                    f"🎉 Disparos finalizados! "
                    f"✅ Sucessos: {sucessos} | ❌ Erros/Falhas: {erros}"
                )

    except Exception as erro_geral:
        st.error(f"❌ Erro ao processar o arquivo: {erro_geral}")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.caption("Desenvolvido para uso exclusivo interno da Maislaser.")
