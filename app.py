import streamlit as st
import pandas as pd
from db import df_adm, df_compras, df_estoque, df_rec, df_desp
from datetime import datetime
import streamlit_authenticator_mongo as stauth
import yaml
from yaml.loader import SafeLoader
import locale
import os

# Configuração de locale mais robusta
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except locale.Error:
            os.environ['LANG'] = 'pt_BR.UTF-8'
            os.environ['LC_ALL'] = 'pt_BR.UTF-8'
            try:
                locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
            except locale.Error:
                print("Aviso: Não foi possível configurar o locale para pt_BR.UTF-8")

import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(page_title="Brassaco Adm", page_icon="icon.png", layout="wide")
st.logo('logo.png', icon_image='icon.png', size='large')

rec = df_rec()
desp = df_desp()
compras = df_compras()
estoque = df_estoque()
adm = df_adm()

doc = {
    'username':'',
    'password': stauth.Hasher(['']).generate()[0],
    'email': '',
    'name': ''
}
# adm.insert_one(doc)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    adm,
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

authenticator.login('Login', 'main')




def Dashboard():
    with st.sidebar:
        st.title("Filtros")
        ano_atual = datetime.now().year
        anos_disponiveis = list(range(ano_atual, ano_atual-5, -1))
        ano = st.selectbox("Ano", options=anos_disponiveis)
        
        meses = {
            "Janeiro": 1,
            "Fevereiro": 2,
            "Março": 3,
            "Abril": 4,
            "Maio": 5,
            "Junho": 6,
            "Julho": 7,
            "Agosto": 8,
            "Setembro": 9,
            "Outubro": 10,
            "Novembro": 11,
            "Dezembro": 12
        }
        mes = st.selectbox("Mês", options=list(meses.keys()), index=datetime.now().month-1)
        mes_numero = meses[mes]
        conta = st.multiselect("Conta", options=rec['conta'].unique())
    
    # Criando três colunas, com a do meio menor para centralizar
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image('logo.png', use_container_width=True)
    
    col1, col2, col3 = st.columns([1, 1, 1], gap="small")
    with col1:
        
        st.markdown("<div style='text-align: center'> <strong>Brassaco</strong></div>", unsafe_allow_html=True)
        # Filtro base para todas as lojas
        filtro_base = (rec['data'].dt.year == ano) & (rec['data'].dt.month == mes_numero)
        if conta:
            filtro_base = filtro_base & (rec['conta'].isin(conta))
        
        # Função para formatar o DataFrame
        def formatar_dataframe(df):
            df['valor'] = df['valor'].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            return df
        total_brassaco = rec[((rec['loja'] == 'QI') | (rec['loja'] == 'QNE')) & filtro_base]['valor'].sum()    
        rec_filtrado = rec[((rec['loja'] == 'QI') | (rec['loja'] == 'QNE')) & filtro_base]
        
        with st.expander(f"Receitas  ► R$ {total_brassaco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")):
            
            df_brassaco = formatar_dataframe(
                rec[
                    ((rec['loja'] == 'QI') | (rec['loja'] == 'QNE')) & 
                    filtro_base
                ].groupby('conta')['valor'].sum().reset_index()
            )
            
            st.dataframe(df_brassaco, use_container_width=True, hide_index=True)
        resultado_diario = rec_filtrado.groupby(rec['data'].dt.date).agg({
            'valor': 'sum'
            }).reset_index()
        
        # Calculando valores acumulados do mês atual
        resultado_diario['valor_acumulado'] = resultado_diario['valor'].cumsum()
        resultado_diario['dia'] = pd.to_datetime(resultado_diario['data']).dt.day
        
        # Calculando valores acumulados do mês anterior
        mes_anterior = mes_numero - 1 if mes_numero > 1 else 12
        ano_anterior = ano if mes_numero > 1 else ano - 1
        
        filtro_mes_anterior = (rec['data'].dt.year == ano_anterior) & (rec['data'].dt.month == mes_anterior)
        rec_mes_anterior = rec[((rec['loja'] == 'QI') | (rec['loja'] == 'QNE')) & filtro_mes_anterior]
        
        resultado_mes_anterior = rec_mes_anterior.groupby(rec_mes_anterior['data'].dt.date).agg({
            'valor': 'sum'
            }).reset_index()
        resultado_mes_anterior['valor_acumulado'] = resultado_mes_anterior['valor'].cumsum()
        resultado_mes_anterior['dia'] = pd.to_datetime(resultado_mes_anterior['data']).dt.day
        
        # Criando DataFrame com todos os dias do mês
        todos_dias = pd.DataFrame({
            'dia': range(1, 32)
        })
        
        # Combinando com os dados reais
        df_completo = todos_dias.merge(
            resultado_diario[['dia', 'valor_acumulado']].rename(columns={'valor_acumulado': 'Mês Atual'}),
            on='dia',
            how='left'
        ).merge(
            resultado_mes_anterior[['dia', 'valor_acumulado']].rename(columns={'valor_acumulado': 'Mês Anterior'}),
            on='dia',
            how='left'
        ).ffill()
        
        st.line_chart(
            df_completo.set_index('dia'),
            use_container_width=True
        )
            
    with col2:
        total_pel = rec[((rec['loja'] == 'NRT') ) & filtro_base]['valor'].sum()    
        rec_pel_filtrado = rec[((rec['loja'] == 'NRT')) & filtro_base]
        st.markdown("<div style='text-align: center'><strong>Plastibra</strong></div>", unsafe_allow_html=True)
        with st.expander(f"Receitas  ►    R$ {total_pel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")):
            st.dataframe(
                formatar_dataframe(
                    rec[
                    (rec['loja'] == 'NRT') & 
                    filtro_base
                ].groupby('conta')['valor'].sum().reset_index()
            ), 
            use_container_width=True, 
            hide_index=True
        )
        resultado_diario_pel = rec_pel_filtrado.groupby(rec_pel_filtrado['data'].dt.date).agg({
            'valor': 'sum'
            }).reset_index()
        
        # Calculando valores acumulados do mês atual
        resultado_diario_pel['valor_acumulado'] = resultado_diario_pel['valor'].cumsum()
        resultado_diario_pel['dia'] = pd.to_datetime(resultado_diario_pel['data']).dt.day        
        # Calculando valores acumulados do mês atual
        resultado_diario_pel['valor_acumulado'] = resultado_diario_pel['valor'].cumsum()
        resultado_diario_pel['dia'] = pd.to_datetime(resultado_diario_pel['data']).dt.day
        
        # Calculando valores acumulados do mês anterior
        mes_anterior = mes_numero - 1 if mes_numero > 1 else 12
        ano_anterior = ano if mes_numero > 1 else ano - 1
        
        filtro_mes_anterior = (rec['data'].dt.year == ano_anterior) & (rec['data'].dt.month == mes_anterior)
        rec_mes_anterior_pel = rec[((rec['loja'] == 'NRT') ) & filtro_mes_anterior]
        
        resultado_mes_anterior_pel = rec_mes_anterior_pel.groupby(rec_mes_anterior_pel['data'].dt.date).agg({
            'valor': 'sum'
            }).reset_index()
        resultado_mes_anterior_pel['valor_acumulado'] = resultado_mes_anterior_pel['valor'].cumsum()
        resultado_mes_anterior_pel['dia'] = pd.to_datetime(resultado_mes_anterior_pel['data']).dt.day
        
        # Criando DataFrame com todos os dias do mês
        todos_dias = pd.DataFrame({
            'dia': range(1, 32)
        })
        
        # Combinando com os dados reais
        df_completo_pel = todos_dias.merge(
            resultado_diario_pel[['dia', 'valor_acumulado']].rename(columns={'valor_acumulado': 'Mês Atual'}),
            on='dia',
            how='left'
        ).merge(
            resultado_mes_anterior_pel[['dia', 'valor_acumulado']].rename(columns={'valor_acumulado': 'Mês Anterior'}),
            on='dia',
            how='left'
        ).ffill()
        
        st.line_chart(
            df_completo_pel.set_index('dia'),
            use_container_width=True
        )

    with col3:
        
        st.markdown("<div style='text-align: center'><strong>Sacobras</strong></div>", unsafe_allow_html=True)
        total_sel = rec[((rec['loja'] == 'SDS') ) & filtro_base]['valor'].sum()  
        rec_sel_filtrado = rec[((rec['loja'] == 'SDS')) & filtro_base]  

        with st.expander(f"Receitas  ►    R$ {total_sel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")):
            st.dataframe(
                formatar_dataframe(
                    rec[
                        (rec['loja'] == 'SDS') & 
                    filtro_base
                ].groupby('conta')['valor'].sum().reset_index()
            ), 
            use_container_width=True, 
            hide_index=True
        )
        resultado_diario_sel = rec_sel_filtrado.groupby(rec_sel_filtrado['data'].dt.date).agg({
        'valor': 'sum'
        }).reset_index()


        # Calculando valores acumulados do mês atual
        resultado_diario_sel['valor_acumulado'] = resultado_diario_sel['valor'].cumsum()
        resultado_diario_sel['dia'] = pd.to_datetime(resultado_diario_sel['data']).dt.day        
        # Calculando valores acumulados do mês atual
        resultado_diario_sel['valor_acumulado'] = resultado_diario_sel['valor'].cumsum()
        resultado_diario_sel['dia'] = pd.to_datetime(resultado_diario_sel['data']).dt.day
        
        # Calculando valores acumulados do mês anterior
        mes_anterior = mes_numero - 1 if mes_numero > 1 else 12
        ano_anterior = ano if mes_numero > 1 else ano - 1
        
        filtro_mes_anterior = (rec['data'].dt.year == ano_anterior) & (rec['data'].dt.month == mes_anterior)
        rec_mes_anterior_sel = rec[((rec['loja'] == 'SDS') ) & filtro_mes_anterior]
        
        resultado_mes_anterior_sel = rec_mes_anterior_sel.groupby(rec_mes_anterior_sel['data'].dt.date).agg({
            'valor': 'sum'
            }).reset_index()
        resultado_mes_anterior_sel['valor_acumulado'] = resultado_mes_anterior_sel['valor'].cumsum()
        resultado_mes_anterior_sel['dia'] = pd.to_datetime(resultado_mes_anterior_sel['data']).dt.day
        
        # Criando DataFrame com todos os dias do mês
        todos_dias = pd.DataFrame({
            'dia': range(1, 32)
        })
        
        # Combinando com os dados reais
        df_completo_sel = todos_dias.merge(
            resultado_diario_sel[['dia', 'valor_acumulado']].rename(columns={'valor_acumulado': 'Mês Atual'}),
            on='dia',
            how='left'
        ).merge(
            resultado_mes_anterior_sel[['dia', 'valor_acumulado']].rename(columns={'valor_acumulado': 'Mês Anterior'}),
            on='dia',
            how='left'
        ).ffill()
        
        st.line_chart(
            df_completo_sel.set_index('dia'),
            use_container_width=True
        )    

    st.markdown("<div style='text-align: center'><strong>Total das Despesas</strong></div>", unsafe_allow_html=True)
    col3, col4 = st.columns([1, 1])
    with col3:
        filtro_base_desp = (desp['data'].dt.year == ano) & (desp['data'].dt.month == mes_numero)
        total_desp = desp[filtro_base_desp]['valor'].sum()  
        
        st.text(f"Depesas  ►    R$ {total_desp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.dataframe(
            formatar_dataframe(
                desp[filtro_base_desp].groupby('conta')['valor'].sum().reset_index()
        ), 
        use_container_width=True, 
        hide_index=True
        )
        
    with col4:        
        # Preparando dados para o gráfico de barras
        # Mês atual
        desp_atual = desp[filtro_base_desp].groupby('conta')['valor'].sum()

        # Mês anterior
        filtro_mes_anterior_desp = (desp['data'].dt.year == ano_anterior) & (desp['data'].dt.month == mes_anterior)
        desp_anterior = desp[filtro_mes_anterior_desp].groupby('conta')['valor'].sum()

        # Combinando os dados
        df_comparativo = pd.DataFrame({
            'Mês Atual': desp_atual,
            'Mês Anterior': desp_anterior
        }).fillna(0)
        st.write(desp_atual)
        # Criando o gráfico de barras lado a lado
        fig = px.bar(
            df_comparativo.reset_index(),
            x='conta',
            y=['Mês Anterior','Mês Atual' ],
            barmode='group',
            title='Comparativo de Despesas por Conta',
            
        )
        
        # Personalizando o layout
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_title='Contas',
            yaxis_title='Valor (R$)',
            legend_title='Período',
            height=300
        )
        
        # Formatando os tooltips
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                         "R$ %{y:,.2f.}".replace(",", "X").replace(".", ",").replace("X", ".") 
                         
        )
        
        st.plotly_chart(fig, use_container_width=True)

    
    total_receita = rec[filtro_base]['valor'].sum()   
    rec_mes_anterior = rec[filtro_mes_anterior]
    total_receita_anterior = rec_mes_anterior['valor'].sum()
    dif_receita = total_receita - total_receita_anterior

    total_despesa_anterior = desp[filtro_mes_anterior_desp]['valor'].sum()
    dif_despesa = total_desp - total_despesa_anterior
    
    lucro_operacional = total_receita - total_desp
    lucro_operacional_anterior = total_receita_anterior - total_despesa_anterior
    dif_lucro = lucro_operacional - lucro_operacional_anterior

    # Calculando CMV
    filtro_base_compras = (compras['data'].dt.year == ano) & (compras['data'].dt.month == mes_numero)
    filtro_mes_anterior_compras = (compras['data'].dt.year == ano_anterior) & (compras['data'].dt.month == mes_anterior)

    total_compras = compras[filtro_base_compras]['valor'].sum()
    compras_mes_anterior = compras[filtro_mes_anterior_compras]['valor'].sum()
    dif_compras = total_compras - compras_mes_anterior

    
    # Calculando estoque
    filtro_base_estoque = (estoque['data'].dt.year == ano) & (estoque['data'].dt.month == mes_numero)
    filtro_mes_anterior_estoque = (estoque['data'].dt.year == ano_anterior) & (estoque['data'].dt.month == mes_anterior)

    estoque_atual = estoque[filtro_base_estoque]['valor'].sum()
    estoque_anterior = estoque[filtro_mes_anterior_estoque]['valor'].sum()
    
    
    # CMV = Estoque Inicial + Compras - Estoque Final
    cmv = estoque_anterior + total_compras - estoque_atual
    cmv_anterior = estoque_anterior + compras_mes_anterior - estoque_atual
    dif_cmv = cmv - cmv_anterior

    filtro_base_desp_fixa = (desp['data'].dt.year == ano) & (desp['data'].dt.month == mes_numero) & (desp['tipo'] == 'fixa')
    total_desp_fixa = desp[filtro_base_desp_fixa]['valor'].sum()  
    
    filtro_mes_anterior_desp_fixa = (desp['data'].dt.year == ano_anterior) & (desp['data'].dt.month == mes_anterior) & (desp['tipo'] == 'fixa')
    total_desp_fixa_anterior = desp[filtro_mes_anterior_desp_fixa]['valor'].sum()  
    
    # Lucro Operacional considerando CMV consertar total_desp aqui tem que ser somente as despesas do tipo fixa
    lucro_operacional_cmv = total_receita - total_desp_fixa - cmv
    lucro_operacional_anterior_cmv = total_receita_anterior - total_desp_fixa_anterior - cmv_anterior
    dif_lucro_cmv = lucro_operacional_cmv - lucro_operacional_anterior_cmv
    
    
    a, b = st.columns(2)
    c, d = st.columns(2)

    a.metric("Receitas", f" R$ {total_receita:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{dif_receita:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=True)
    b.metric("Despesas", f" R$ {total_desp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{dif_despesa:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=True)
    
    c.metric("Lucro CMV", f" R$ {lucro_operacional_cmv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{dif_lucro_cmv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=True)
    d.metric("Lucro Operacional", f" R$ {lucro_operacional:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), f"{dif_lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=True)
    style_metric_cards(border_size_px=0,border_left_color= "#93c7fa", border_color="#000000")        


if st.session_state["authentication_status"]:
    with st.sidebar:
        st.write(f'**{st.session_state["name"]}**')
        authenticator.logout('Sair', 'main', key='unique_key')
        
    pg = st.navigation([ Dashboard,  'Despesas.py', 'Receitas.py', 'Compras.py'])
    pg.run()
elif st.session_state["authentication_status"] is False:
    st.error('usuário/senha errados')
elif st.session_state["authentication_status"] is None:
    st.warning('entre com o usuário e senha')




