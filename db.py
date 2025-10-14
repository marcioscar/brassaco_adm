from dotenv import load_dotenv
import pandas as pd
from pymongo import MongoClient
import pymongo
from datetime import datetime
import os
from bson import ObjectId
import streamlit as st

filtro = {
    "data": {"$gte": datetime(2025, 1, 1)}  # Data maior ou igual a 1 de janeiro de 2025
}

filtro_despesas = {
    "data": {"$gte": datetime(2025, 1, 1)},  # Data maior ou igual a 1 de janeiro de 2025
    "$or": [
        {"pago": True},   # Registros onde pago é True
        {"pago": {"$exists": False}}  # Registros onde pago não existe
    ]
}


@st.cache_resource
def conexao():
    try:
        load_dotenv()
        uri = os.getenv("DATABASE_URL")
        client = MongoClient(uri, server_api=pymongo.server_api.ServerApi(
        version="1", strict=True, deprecation_errors=True))
    except Exception as e:
        raise Exception(
            "Erro: ", e)
    db = client["brassaco"]
    
    return  db


def df_fornecedor():
    db = conexao()
    fornecedores = db["fornecedores"]
    data_forn = fornecedores.find()
    data_forn =  pd.DataFrame(list(data_forn)) 
    data_forn.sort_values(by='nome', ascending=True, inplace=True)
    return data_forn


def df_desp():
    db = conexao()
    despesas = db["despesas"]
    # Filtro para pegar apenas despesas do ano atual
    ano_atual = datetime.now().year
    filtro_ano = {
        "data": {
            "$gte": datetime(ano_atual, 1, 1),
            "$lt": datetime(ano_atual + 1, 1, 1)
        }
    }
    data_desp = despesas.find(filtro_ano)
    df_desp =  pd.DataFrame(list(data_desp)) 
    df_desp.sort_values(by='data', ascending=False, inplace=True)
    return df_desp


def df_rec():
    db = conexao()
    receitas = db["receitas"]
    ano_atual = datetime.now().year
    filtro_ano = {
        "data": {
            "$gte": datetime(ano_atual, 1, 1),
            "$lt": datetime(ano_atual + 1, 1, 1)
        }
    }
    data_rec = receitas.find(filtro_ano)
    df_rec =  pd.DataFrame(list(data_rec)) 
    df_rec.sort_values(by='data', ascending=False, inplace=True)
    return df_rec


def df_estoque():
    db = conexao()
    estoque = db["estoque"]
    data_estoque = estoque.find()
    df_estoque =  pd.DataFrame(list(data_estoque)) 
    df_estoque.sort_values(by='data', ascending=False, inplace=True)
    return df_estoque


def df_compras():
    db = conexao()
    compras = db["compras"]
    ano_atual = datetime.now().year
    filtro_ano = {
        "data": {
            "$gte": datetime(ano_atual, 1, 1),
            "$lt": datetime(ano_atual + 1, 1, 1)
        }
    }
    data_compras = compras.find(filtro_ano)
    df_compras =  pd.DataFrame(list(data_compras)) 
    df_compras.sort_values(by='data', ascending=False, inplace=True)
    return df_compras


def df_rec_apagar(id):
    db = conexao()
    try:
        # Converte a string do ID para ObjectId
        object_id = ObjectId(id)
        filtro = {"_id": object_id}
        print(f"ID: {id}")
        receitas = db["receitas"]
        receitas.delete_one(filtro)
        print(f"Receita deletada com sucesso: {id}")
    except Exception as e:
        print(f"Erro ao deletar receita: {e}")


def df_compra_apagar(id):
    db = conexao()
    try:
        # Converte a string do ID para ObjectId
        object_id = ObjectId(id)
        filtro = {"_id": object_id}
        print(f"ID: {id}")
        compras = db["compras"]
        compras.delete_one(filtro)
        print(f"Compra deletada com sucesso: {id}")
    except Exception as e:
        print(f"Erro ao deletar compra: {e}")        


def df_desp_apagar(id):
    db = conexao()
    try:
        # Converte a string do ID para ObjectId
        object_id = ObjectId(id)
        filtro = {"_id": object_id}
        print(f"ID: {id}")
        despesas = db["despesas"]
        despesas.delete_one(filtro)
        print(f"Despesa deletada com sucesso: {id}")
    except Exception as e:
        print(f"Erro ao deletar despesas: {e}")
        


def df_rec_cadastrar(conta, valor, descricao, loja, data, carteira):
    db = conexao()
    receitas = db["receitas"]
    data_rec_cadastrar = receitas.insert_one({
        "conta": conta,
        "data": data,
        "valor": valor,
        "descricao": descricao,
        "loja": loja,
        "carteira": carteira
    })
    
    return data_rec_cadastrar  


def df_compra_cadastrar(nf, valor, fornecedor, data):
    db = conexao()
    compras = db["compras"]
    data_compra_cadastrar = compras.insert_one({
        "nf": nf,
        "data": data,
        "valor": valor,
        "fornecedor": fornecedor
    })
    
    return data_compra_cadastrar


def df_fornecedor_cadastrar(nome):
    db = conexao()
    fornecedores = db["fornecedores"]
    data_fornecedor_cadastrar = fornecedores.insert_one({
        "nome": nome
    })
    return data_fornecedor_cadastrar


def df_desp_cadastrar(conta, data, valor, descricao, loja, fornecedor, comprovante, tipo):
    db = conexao()
    despesas = db["despesas"]
    data_desp_cadastrar = despesas.insert_one({
        "fornecedor": fornecedor,
        "conta": conta,
        "data": data,
        "valor": valor,
        "descricao": descricao,
        "loja": loja,
        "comprovante": comprovante,
        "tipo": tipo
    })
    
    return data_desp_cadastrar   


def df_desp_editar(id, conta, data, valor, descricao, loja, tipo):
    db = conexao()
    despesas = db["despesas"]
    filtro = {"_id": ObjectId(id)}
    despesas.update_one(filtro, {"$set": {"conta": conta, "data": data, "valor": valor, "descricao": descricao, "loja": loja, "tipo": tipo}})


def df_rec_editar(id, conta, valor, descricao, loja, data, carteira):
    db = conexao()
    receitas = db["receitas"]
    filtro = {"_id": ObjectId(id)}
    receitas.update_one(filtro, {"$set": {"conta": conta, "data": data, "valor": valor, "descricao": descricao, "carteira": carteira, 'loja':loja}})


def df_compra_editar(id, nf, valor, fornecedor,data):
    db = conexao()
    compras = db["compras"]
    filtro = {"_id": ObjectId(id)}
    compras.update_one(filtro, {"$set": {"nf": nf, "data": data, "valor": valor,  "fornecedor": fornecedor, }})


# def df_salario():
#     db = conexao()
#     folha = db["folha"]
#     funcionarios = folha.find().sort("nome", 1)
#     df_funcionarios = pd.DataFrame(list(funcionarios)) 
#     # df_rec_agrupado = df_rec.groupby(['data'])['valor'].sum().reset_index()
#     return df_funcionarios

# @st.cache_data
# def folha():
#     db = conexao()
#     folha = db["folha"]
#     return folha

@st.cache_resource
def df_adm():
    db = conexao()
    adm = db["adm"]
    return adm


