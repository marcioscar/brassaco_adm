from datetime import datetime
import locale
from db import df_desp_apagar, df_desp_cadastrar, df_desp_editar, df_fornecedor, df_desp
import streamlit as st
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from streamlit_extras.dataframe_explorer import dataframe_explorer

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
FOLDER_ID = '1xmc_etpuUGdrUJgHMwZIXji5vVt_ySfH' # recibos_brassaco
# 🔑 Configuração das credenciais
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)


# 🚀 Função para upload no Drive
def upload_arquivo_drive(file, file_name):
    nome_arquivo = datetime.now().strftime("%d-%m-%Y") + '_' + file_name
    file_metadata = {'name': nome_arquivo,
                     'parents': [FOLDER_ID]
                     }

    media = MediaIoBaseUpload(
        io.BytesIO(file.read()), mimetype=file.type, resumable=True
    )

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    # 🔓 Permissão pública
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    # 🔗 Link público
    link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    return link


# Carregando variáveis de ambiente
load_dotenv()

# Configuração do S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')



def upload_to_s3(file_obj, file_name):
    try:
        # Gerando um nome único para o arquivo
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
        
        # Enviando o arquivo para o S3
        s3_client.upload_fileobj(
            file_obj,
            BUCKET_NAME,
            f"comprovantes/{unique_filename}",
            ExtraArgs={
                'ContentType': '*/*',
                'ACL': 'public-read'
            }
        )
        
        # Retornando a URL do arquivo no S3
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/comprovantes/{unique_filename}"
        return url
    except ClientError as e:
        st.error(f"Erro ao enviar arquivo para o S3: {e}")
        return None

desp = df_desp()
forn = df_fornecedor()

@st.dialog("Nova despesa")
def despesa():
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
        
        submitted = st.form_submit_button("Salvar")
        if submitted :
            if comprovante is not None:
                s3_url = upload_to_s3(comprovante, comprovante.name)
                if s3_url:
                    # Chamando a função de cadastro com a URL do arquivo no S3
                    df_desp_cadastrar(conta, data,valor, descricao, loja, fornecedor, s3_url, tipo)
                    st.success("Despesa cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao enviar o comprovante. Por favor, tente novamente.")
            else:
                df_desp_cadastrar(conta, data,valor, descricao, loja, fornecedor, None, tipo)
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
            "Data", format="DD/MM/YYYY"
        ),
        "comprovante": st.column_config.LinkColumn(
            "", display_text="📄"
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





