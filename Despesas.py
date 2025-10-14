from datetime import datetime
import locale
from db import df_desp_apagar, df_desp_cadastrar, df_desp_editar, df_fornecedor, df_desp
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from dotenv import load_dotenv
import dropbox
from dropbox.files import WriteMode
import os
import requests
# Carregando variáveis de ambiente
load_dotenv()

# Configuração do locale
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')
# === CONFIGURAÇÃO DO DROPBOX ===
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')

# Verificar se as credenciais estão configuradas
if not all([DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN]):
    st.error("❌ Credenciais do Dropbox não encontradas!")
    st.info("""
    Configure as seguintes variáveis no arquivo .env:
    - DROPBOX_APP_KEY
    - DROPBOX_APP_SECRET  
    - DROPBOX_REFRESH_TOKEN
    """)
    st.stop()

def get_dropbox_access_token():
    """Obtém um novo access token usando o refresh token."""
    try:
        url = "https://api.dropboxapi.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN,
            "client_id": DROPBOX_APP_KEY,
            "client_secret": DROPBOX_APP_SECRET
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data.get("access_token")
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao renovar token: {e}")
        return None

# 🚀 Função para upload no Dropbox
def upload_arquivo_dropbox(file, filename):
    try:
        # Obter novo access token
        access_token = get_dropbox_access_token()
        if not access_token:
            st.error("❌ Não foi possível obter o access token!")
            return None
        
        dbx = dropbox.Dropbox(access_token)
        
        # Verificar se o token tem as permissões necessárias
        try:
            dbx.users_get_current_account()
        except dropbox.exceptions.AuthError as e:
            if "expired_access_token" in str(e):
                st.error("❌ Token do Dropbox expirou!")
                st.info("""
                **Para resolver:**
                1. Acesse: https://www.dropbox.com/developers/apps
                2. Encontre seu app
                3. Vá em "Settings" → "OAuth 2"
                4. Clique em "Generate access token"
                5. Copie o novo token
                6. Atualize a variável DROPBOX_ACCESS_TOKEN no arquivo .env
                """)
            else:
                st.error(f"Erro de autenticação: {e}")
                st.info("Verifique se o token tem as permissões corretas no Dropbox App Console")
            return None
        
        # Nome único para o arquivo
        nome_arquivo = f"{datetime.now().strftime('%d-%m-%Y')}_{filename}"
        dropbox_path = f'/comprovantes_brassaco/{nome_arquivo}'
        
        # Resetar o ponteiro do arquivo
        file.seek(0)
        
        # Upload
        dbx.files_upload(file.read(), dropbox_path, mode=WriteMode("overwrite"))
        
        # Tentar criar link compartilhado
        try:
            shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
            return shared_link.url.replace("?dl=0", "?dl=1")  # link direto para download
        except dropbox.exceptions.ApiError as e:
            if e.error.is_shared_link_already_exists():
                # Se o link já existe, obter o link existente
                shared_links = dbx.sharing_list_shared_links(dropbox_path)
                if shared_links.links:
                    return shared_links.links[0].url.replace("?dl=0", "?dl=1")
            else:
                raise e
        
    except dropbox.exceptions.AuthError as e:
        if "expired_access_token" in str(e):
            st.error("❌ Token do Dropbox expirou!")
            st.info("""
            **Para resolver:**
            1. Acesse: https://www.dropbox.com/developers/apps
            2. Encontre seu app
            3. Vá em "Settings" → "OAuth 2"
            4. Clique em "Generate access token"
            5. Copie o novo token
            6. Atualize a variável DROPBOX_ACCESS_TOKEN no arquivo .env
            """)
        else:
            st.error(f"Erro de autenticação: {e}")
            st.info("Verifique se o token tem a permissão 'files.content.write' e 'sharing.write' no Dropbox App Console")
        return None
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Dropbox: {str(e)}")
        return None

desp = df_desp()
forn = df_fornecedor()

@st.dialog("Nova despesa")
def despesa():
    link = ''
    with st.form("Despesa"):
        fornecedor = st.selectbox("Fornecedor", options=forn["nome"].unique())
        col1, col2 = st.columns(2)
        with col1:
            conta = st.selectbox("Conta", options=desp["conta"].unique())
            valor = st.number_input("Valor", value=0.0)
            descricao = st.text_input("Descrição")
        with col2:
            data = datetime.combine(st.date_input('Data', format="DD/MM/YYYY"), datetime.min.time())
            loja = st.selectbox("Loja", options=desp["loja"].unique())
            tipo = st.selectbox("Tipo", options=["fixa", "variavel"])
        comprovante = st.file_uploader("Comprovante", type=["jpg", "jpeg", "pdf"])
        if comprovante is not None:
            with st.spinner("Fazendo upload do comprovante..."):
                link = upload_arquivo_dropbox(comprovante, comprovante.name)
                if link:
                    st.success("Comprovante enviado com sucesso!")
                    # st.markdown(f"[📄 Ver comprovante]({link})")
            

        submitted = st.form_submit_button("Salvar")
        if submitted :    
            # Chamando a função de cadastro com a URL do arquivo no Dropbox
            df_desp_cadastrar(conta, data,valor, descricao, loja, fornecedor, link, tipo)
            st.success("Despesa cadastrada com sucesso!")
            st.rerun()
        
                


@st.dialog("Editar despesa")
def editar(id, conta, data, valor, descricao, loja, tipo):
    
    with st.form("Editar"):
        # Encontrando o índice do valor atual nas opções
        conta_index = list(desp["conta"].unique()).index(conta) if conta in desp["conta"].unique() else 0
        loja_index = list(desp["loja"].unique()).index(loja) if loja in desp["loja"].unique() else 0
        tipo_index = ["fixa", "variavel"].index(tipo) if tipo in ["fixa", "variavel"] else 0
        col1, col2 = st.columns([1, 1])
        with col1:
            conta = st.selectbox("Conta", options=desp["conta"].unique(), index=conta_index)
            valor = st.number_input("Valor", value=float(valor.replace('R$', '').replace('.', '').replace(',', '.')))
            descricao = st.text_input("Descrição", value=descricao)
        
        with col2:
            data = datetime.combine(st.date_input('Data', value=data, format="DD/MM/YYYY"), datetime.min.time())
            loja = st.selectbox("Loja", options=desp["loja"].unique(), index=loja_index)
            tipo = st.selectbox("Tipo", options=["fixa", "variavel"], index=tipo_index)
        id = st.text_input("ID", value=id, disabled=True, )
        submitted = st.form_submit_button("Salvar")
        if submitted:
            df_desp_editar(id,conta, data, valor, descricao, loja, tipo)
            st.success("Despesa editada com sucesso!")
            st.rerun()
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Apagar", type='secondary', icon="❌"):
            df_desp_apagar(id)
            st.success("Despesa apagada com sucesso!")
            st.rerun()


col1, col2 = st.columns([6, 1], vertical_alignment="center")
with col1:
    st.subheader("Despesas")
with col2:
   if st.button("Despesa", type='secondary',icon="📤"):
        despesa()
desp["Editar"] = False  
desp["valor"] = desp["valor"].apply(lambda x: locale.currency(x, grouping=True))


    
col1, col2 = st.columns([6, 2], vertical_alignment="bottom")
with col1:
    filtered_df = dataframe_explorer(desp, case=False)

edited_df = st.data_editor(
    filtered_df, 
    column_order=["conta", "valor", "descricao", "loja", "fornecedor", "data", "comprovante", "Editar"], 
    column_config={
        "data": st.column_config.DateColumn(
            "Data", format="DD/MM/YYYY",
            disabled=True,
        ),
        "comprovante": st.column_config.LinkColumn(
            "", 
            display_text="📄",
            disabled=True,
        ),
        "Editar": st.column_config.CheckboxColumn(
            "Editar",
            help="Marque para editar esta linha",
            default=False,
        )
    },
    hide_index=True, 
    height=500, 
)



with col2:
    if st.button("Editar", type='secondary', icon="✅"):
        linha_selecionada = edited_df[edited_df["Editar"] == True]
        if not linha_selecionada.empty:
            # Convertendo os valores da Series para valores únicos
            id = linha_selecionada["_id"].iloc[0]
            conta = linha_selecionada["conta"].iloc[0]
            data = linha_selecionada["data"].iloc[0]
            valor = linha_selecionada["valor"].iloc[0]
            descricao = linha_selecionada["descricao"].iloc[0]
            loja = linha_selecionada["loja"].iloc[0]
            tipo = linha_selecionada["tipo"].iloc[0]
            editar(id, conta, data, valor, descricao, loja, tipo)
        else:
            st.warning("Selecione uma linha para editar")





