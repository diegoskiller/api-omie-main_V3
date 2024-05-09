import requests
import locale
from sqlalchemy import desc
from flask import Flask, render_template, flash, redirect, url_for, request, session, jsonify, json
from datetime import date, datetime, timedelta
from models.models import Ops_visual, Movimentos_estoque, Estrutura_op, User, Lote_visual, Sequencia_op, Sequencia_lote, Config_Visual
from models.forms import LoginForm, RegisterForm
from flask_login import login_user, logout_user, current_user
from config import app, db, app_key, app_secret, bcrypt, login_manager
from operator import neg
import time
import re
import pandas as pd


#===================Inicio upload excel ==================#

@app.route('/upload_excel')
def upload_excel():
        return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file:
            file.save('uploaded_file.xlsx')

            df = pd.read_excel('uploaded_file.xlsx')
            num_linhas = len(df.dropna())
            
            return redirect(url_for('status_upload', num_linhas=num_linhas))

@app.route('/status_upload/<int:num_linhas>')
def status_upload(num_linhas):
        return render_template('status_upload.html', num_linhas=num_linhas)

@app.route('/processar')
def processar():
    Def_salva_dados_excel()
    return redirect(url_for('upload_excel'))




# abaixo a logica para salvar no banco de dados


def Def_salva_dados_excel():
    df = pd.read_excel('uploaded_file.xlsx') #recupera os dados do excel e salva na variavel df pode ser mantido como está
    
    
    data_atual = date.today().strftime("%Y-%m-%d")
    hora_atual = datetime.now().strftime("%H:%M")
    numero_op_visual = Def_numero_op()
    


    for _, row in df.dropna().iterrows(): #roda o loop nos dados do excel salvos na variavel df tbm pode ser mantido como está
        dados_do_excel = {re.sub(r'\W+', '_', col.lower()): val for col, val in row.items()} # salva os dados de cada coluna para ser acessado, pode ser mantido como está

        item = dados_do_excel.get('item', '')   #assim vc pega o dado que vc precisa, baseado no titulo da coluna que deve deixar entre parenteses seguindo o padrão
        quantidade = dados_do_excel.get('quantidade', 0.0) #se o conteudo daquela coluna for um numero deve passar o titulo da coluna e o parametro 0.0 entre parenteses, se for string deve passar o nome da coluna e uma aspas vazias ""

        #abaixo seria a logica do que vc quer salvar no banco, no exemplo usei para salvar uma OP, so copiei da rota que existe pra salvar op
        item = item
        situação = "Aberta"       
        descrição = Def_descricao(item)
        quantidade = float(quantidade)
        data_abertura = data_atual
        hora_abertura = hora_atual
        peso_enviado = 0
        fino_enviado = 0
        peso_retornado = 0
        fino_retornado = 0

        novo_item = Ops_visual(
            numero_op_visual=numero_op_visual,
            situação=situação,
            item=item,
            descrição=descrição,
            quantidade=quantidade,
            peso_enviado=peso_enviado,
            peso_retornado=peso_retornado,
            fino_enviado=fino_enviado,
            fino_retornado=fino_retornado,
            data_abertura=data_abertura,
            hora_abertura=hora_abertura
        )

        db.session.add(novo_item)

        print(f'Lançando no banco: {dados_do_excel}')      
    

    db.session.commit()
   
#===================Fim upload excel ==================#