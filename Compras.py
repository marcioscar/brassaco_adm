from datetime import datetime
import locale
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
import streamlit_authenticator_mongo as stauth

from db import df_compra_apagar, df_compra_editar, df_compras, df_compra_cadastrar, df_fornecedor, df_fornecedor_cadastrar
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

forn = df_fornecedor()
compras = df_compras()
compras["valor"] = compras["valor"].apply(lambda x: locale.currency(x, grouping=True))

compras["Editar"] = False  

@st.dialog("Nova Compra")
def compra():
    with st.form("Compra"):
        fornecedor = st.selectbox("Fornecedor", options=forn["nome"].unique())
        col1, col2 = st.columns(2)
        with col1:
            nf = st.text_input("NF")
            valor = st.number_input("Valor", value=0.0)
        with col2:            
            data = datetime.combine(st.date_input('Data', format="DD/MM/YYYY"), datetime.min.time())
        submitted = st.form_submit_button("Salvar")
        if submitted:
            df_compra_cadastrar(nf, valor, fornecedor, data)
            st.success("Compra cadastrada com sucesso!")
            st.rerun()

@st.dialog("Novo Fornecedor")
def fornecedor():
    with st.form("Fornecedor"):
        nome = st.text_input("Nome")

        submitted = st.form_submit_button("Salvar")
        if submitted:
            df_fornecedor_cadastrar(nome)
            st.success("Fornecedor cadastrado com sucesso!")
            st.rerun()

@st.dialog("Editar Compras")
def editar(id, nf, valor, fornecedor,data):
    with st.form("Editar"):
        conta_index = list(compras["fornecedor"].unique()).index(fornecedor) if fornecedor in compras["fornecedor"].unique() else 0
        col1, col2 = st.columns(2)
        with col1:
            fornecedor = st.selectbox("Fornecedor", options=compras["fornecedor"].unique(), index=conta_index)
            valor = st.number_input("Valor", value=float(valor.replace('R$', '').replace('.', '').replace(',', '.')))
        with col2:
            nf = st.text_input("NF", value=nf)
            data = datetime.combine(st.date_input('Data', value=data, format="DD/MM/YYYY"), datetime.min.time())
        submitted = st.form_submit_button("Salvar")
        if submitted:
            df_compra_editar(id, nf, valor, fornecedor,data)
            st.success("Compra editada com sucesso!")
            st.rerun()
    col1, col2 = st.columns([3, 2])
    with col2:
        if st.button("Apagar", type='secondary', icon="❌"):
            df_compra_apagar(id)
            st.success("Receita apagada com sucesso!")
            st.rerun()    

col1, col2, col3 = st.columns([6, 2, 2], vertical_alignment="center")
with col1:
    st.subheader("Compras")
with col2:
   if st.button("Compra", type='secondary',icon="🛒"):
    compra()
with col3:
    if st.button("Fornecedor", type='secondary',icon="🏢"):
        fornecedor()

filtered_df = dataframe_explorer(compras, case=False)
    
edited_df = st.data_editor(
filtered_df, 
column_order=["nf", "valor", "fornecedor", 'data', 'Editar'], 
column_config={
    "data": st.column_config.DateColumn(
        "Data", format="DD/MM/YYYY"
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

if st.button("Editar", type='secondary', icon="✅"):
    linha_selecionada = edited_df[edited_df["Editar"] == True]
    if not linha_selecionada.empty:
        # Convertendo os valores da Series para valores únicos
        id = linha_selecionada["_id"].iloc[0]
        data = linha_selecionada["data"].iloc[0]
        valor = linha_selecionada["valor"].iloc[0]
        nf = linha_selecionada["nf"].iloc[0]
        fornecedor = linha_selecionada["fornecedor"].iloc[0]
        editar(id, nf, valor, fornecedor,data)
    else:
        st.warning("Selecione uma linha para editar")