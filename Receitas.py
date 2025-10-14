from datetime import datetime
import locale
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from db import df_rec, df_rec_apagar, df_rec_cadastrar, df_rec_editar
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')


rec = df_rec()
rec["valor"] = rec["valor"].apply(lambda x: locale.currency(x, grouping=True))


@st.dialog("Nova receita")
def receita():
    with st.form("Receita"):
        col1, col2 = st.columns(2)
        with col1:
            conta = st.selectbox("Conta", options=["dinheiro", "cartao", "pix"])
            valor = st.number_input("Valor", value=0.0)
            descricao = st.text_input("Descrição")
        with col2:
            loja = st.selectbox("Loja", options=['QI', 'QNE','NRT', 'SDS', ])
            data = datetime.combine(st.date_input('Data', format="DD/MM/YYYY"), datetime.min.time())
            carteira = st.selectbox("Carteira", options=['dinheiro','bradesco_sds', 'bradesco_qi', 'bradesco_nrt', 'inter_sds', 'inter_qi', 'inter_nrt'])
        submitted = st.form_submit_button("Salvar")
        if submitted:
            df_rec_cadastrar(conta, valor, descricao, loja, data, carteira)
            st.success("Receita cadastrada com sucesso!")
            st.rerun()


@st.dialog("Editar receita")
def editar(id, conta, data, valor, descricao, loja, carteira):
    with st.form("Editar"):
        conta_index = list(rec["conta"].unique()).index(conta) if conta in rec["conta"].unique() else 0
        loja_index = list(rec["loja"].unique()).index(loja) if loja in rec["loja"].unique() else 0
        carteira_index = list(rec["carteira"].unique()).index(carteira) if carteira in rec["carteira"].unique() else 0
        col1, col2 = st.columns(2)
        with col1:
            conta = st.selectbox("Conta", options=rec["conta"].unique(), index=conta_index)
            valor = st.number_input("Valor", value=float(valor.replace('R$', '').replace('.', '').replace(',', '.')))
            descricao = st.text_input("Descrição", value=descricao)
        with col2:
            loja = st.selectbox("Loja", options=rec["loja"].unique(), index=loja_index)
            data = datetime.combine(st.date_input('Data', value=data, format="DD/MM/YYYY"), datetime.min.time())
            carteira = st.selectbox("Carteira", options=rec["carteira"].unique(), index=carteira_index)
        submitted = st.form_submit_button("Salvar")
        if submitted:
            df_rec_editar(id, conta, valor, descricao, loja, data, carteira)
            st.success("Receita editada com sucesso!")
            st.rerun()
    col1, col2 = st.columns([3, 2])
    with col2:
        if st.button("Apagar", type='secondary', icon="❌"):
            df_rec_apagar(id)
            st.success("Receita apagada com sucesso!")
            st.rerun()    


rec["Editar"] = False  
col1, col2 = st.columns([6, 1], vertical_alignment="center")
with col1:
    st.subheader("Receitas")
with col2:
   if st.button("Receita", type='secondary',icon="📥"):
      receita()

col1, col2 = st.columns([6, 2], vertical_alignment="bottom")
with col1:
    filtered_df = dataframe_explorer(rec, case=False)


edited_df = st.data_editor(
    filtered_df, 
    column_order=["conta", "valor", "descricao", "loja","data", "carteira", 'Editar'], 
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
            carteira = linha_selecionada["carteira"].iloc[0]
            editar(id, conta, data, valor, descricao, loja, carteira)
        else:
            st.warning("Selecione uma linha para editar")


