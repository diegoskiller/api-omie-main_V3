import requests
from sqlalchemy import desc
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, render_template, flash, redirect, url_for, request, session, jsonify, json, send_from_directory, send_file, Response
from datetime import date, datetime, timedelta, timezone
from models.models import Ops_visual, Movimentos_estoque, Estrutura_op, User, Lote_visual, Lotes_mov_op, Sequencia_op, Sequencia_lote, Config_Visual, Pedido, Ferramentas, Packlist, Cadastro_itens, Setores, Operadores, Familia
from models.forms import LoginForm, RegisterForm
from models import *
from flask_login import login_user, logout_user, current_user
from config import app, db, app_key, app_secret, bcrypt, login_manager
from operator import neg
from reportlab.pdfgen import canvas
#import time
import re
import os
import pandas as pd
import logging
import io
from sqlalchemy.sql import func
from io import BytesIO
import xlsxwriter
from tqdm import tqdm
import subprocess
from urllib.parse import urlparse
import pymysql
from sqlalchemy.engine.url import make_url



#============variaveis gerais=============# 


#============URL DE SISTEMA=============#

url_produtos = "https://app.omie.com.br/api/v1/geral/produtos/"
url_estrutura = "https://app.omie.com.br/api/v1/geral/malha/"
url_consulta_estoque = "https://app.omie.com.br/api/v1/estoque/consulta/"
url_ajuste_estoque = "https://app.omie.com.br/api/v1/estoque/ajuste/"
url_caracter = "https://app.omie.com.br/api/v1/geral/prodcaract/"


#============LOCAIS DE ESTOQUE=============# 

A1 = "2436985075"
AC = "2511785274"
A3 = "4084861665"
CQ = "4085565942"
SE = "4085566100"
AS = "4085566245"
MKM = "4085566344"

locaisOmie = [A1, AC, A3, CQ, SE, AS]
itemgeral = ""
text_botoes = ""



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#============== REGISTER ============#
@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm() 
    if current_user.is_authenticated:
         return redirect( url_for('logged'))
    if form.validate_on_submit(): 

        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")

        new_user = User(email=form.email.data, password=encrypted_password, name=form.name.data)  

        db.session.add(new_user)
        db.session.commit() 

        #flash(f'Conta criada com socesso para o usuário {form.email.data}', category='success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#=============== LOGIN ==============#
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect( url_for('logged'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        logged_user = form.email.data
        session["logged_user"] = logged_user

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("logged"))
        #else:
            #flash(f'Erro ao logar no usuário {form.email.data}', category='danger')
            
    return render_template('login_page.html', form=form)  

#=============Sessão====================#
@app.route("/logged")
def logged():
    if "logged_user" in session:
        logged_user = session["logged_user"]
        return redirect(url_for('index'))
    else:
        return redirect(url_for("login"))    

#============= Logout ==================#
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))  




#===================Quando usuario estiver logado ==================#
def datahora(d_h):
    data_e_hora_USA = datetime.now()
    diferenca = timedelta(hours=-3)
    fuso_horario = timezone(diferenca)
    pre_data_e_hora = data_e_hora_USA.astimezone(fuso_horario)
    data = pre_data_e_hora.strftime('%d/%m/%Y')
    hora = pre_data_e_hora.strftime('%H:%M')
    if d_h == "data":
        rdh = data
    else:
        rdh = hora
    return rdh        



@app.route('/index', methods = ['GET','POST'])
def index():
    if not current_user.is_authenticated:
         return redirect( url_for('login'))
    return render_template('index.html')

@app.route('/index_config', methods = ['GET','POST'])
def index_config():
    if not current_user.is_authenticated:
         return redirect( url_for('login'))
    return render_template('index_config.html')

@app.route('/index_uploads', methods = ['GET','POST'])
def index_uploads():
    if not current_user.is_authenticated:
         return redirect( url_for('login'))
    return render_template('index_uploads.html')

@app.route('/busca', methods = ['GET','POST'])
def busca():
    if not current_user.is_authenticated:
         return redirect( url_for('login'))
    if request.method == 'POST':
        item = request.form.get("item")
        status = Def_item_ok(item)
        id_produto = status[2].get('id_produto')
        if status[0] == "ok":
            item = status[1]

            #Busca = Def_cadastro_prod(item)
            estoque = Def_consulta_estoque(id_produto, A1)

            flash (f'Busca do item: {item} realizada com sucesso', category='success')
        else:
            flash (f' Código: {item} - não cadastrado - ERRO={status}', category='success')
       

        return  render_template('busca.html',  busca = busca, estoque = estoque)

        #return  render_template('buscarv2.html',  busca = busca)



@app.route('/estrutura', methods = ['GET','POST'])
def estrutura():
    item = request.form.get("item")
    if not current_user.is_authenticated:
         return redirect( url_for('login'))
    

    if request.method == 'POST':  
        
        estrutura = Def_consulta_estrutura(item)
        
        return render_template("estrutura.html", estrutura=estrutura)

@app.route('/itens', methods = ['GET','POST'])
def itens():
    if not current_user.is_authenticated:
         return redirect( url_for('login'))
    item = request.form.get("item")
    #if item == None:
    #    item = "CBA-4000"
    dados = Def_cadastro_prod(item)
    
    return  render_template('itens.html',  dados = dados  )



@app.route('/cadastro_itens', methods=['GET', 'POST'])
def cadastro_itens():
    page = request.args.get('page', 1, type=int)

    filtro_cod = request.form.get('filtro_cod', '').upper()
    filtro_desc = request.form.get('filtro_desc', '').upper()

    if filtro_cod == "":
        filtro_cod = None

    if filtro_desc == "":
        filtro_desc = None

    query = Cadastro_itens.query

    if filtro_cod is not None:
        query = query.filter(Cadastro_itens.item.ilike(f"%{filtro_cod}%"))

    if filtro_desc is not None:
        query = query.filter(Cadastro_itens.descricao.ilike(f"%{filtro_desc}%"))

    itens = query.order_by(Cadastro_itens.id.desc()).paginate(page=page, per_page=10)

  

    return render_template('Cadastro_Itens.html', itens=itens, itens_page=itens)


@app.route('/exportar_itens_excel')
def exportar_itens_excel():
    try:
        itens = Cadastro_itens.query.all()
        
        data = {
            "Item": [item.item for item in itens],
            "Descrição": [item.descricao for item in itens],
            "Ncm": [item.ncm for item in itens],
            "Família": [item.familia for item in itens],
            "Cliente": [item.cliente for item in itens],
            "Código do Cliente": [item.codigo_cliente for item in itens],
            "Material": [item.material for item in itens],
            "Setor": [item.setor for item in itens],
            "Peso Unitário": [item.peso for item in itens],
            "Fino Unitário": [item.fino for item in itens],
            "Valor Unitário": [item.valor_unitario for item in itens],
            "Unidade Omie": [item.unidade for item in itens],
            "Unidade Visual": [item.um_visual for item in itens],
            "Uso": [item.uso for item in itens],
            "Data Alteração": [item.data_alteracao for item in itens],
            "Observação": [item.obs for item in itens]
        }
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Itens')
            
            workbook  = writer.book
            worksheet = writer.sheets['Itens']
            
            # Formatação para a primeira linha (header)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            # Formatação para as células de dados
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })
            
            # Aplica a formatação na primeira linha
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ajusta a largura das colunas
                worksheet.set_column(col_num, col_num, 20)
            
            # Aplica a formatação nas células de dados
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)
        
        return send_file(output, download_name='Itens.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/importar_itens', methods=['POST'])
def importar_itens():
    file = request.files['file']
    if not file:
        flash('Nenhum arquivo selecionado', 'danger')
        return redirect(url_for('cadastro_itens'))

    try:
        df = pd.read_excel(file)
    except Exception as e:
        flash(f'Erro ao ler o arquivo Excel: {str(e)}', 'danger')
        return redirect(url_for('cadastro_itens'))

    import_errors = []

    for index, row in df.iterrows():
        try:
            item = Cadastro_itens.query.filter_by(item=row['Item']).first()
            if item:
                item.descricao = row['Descrição']
                item.cliente = row['Cliente']
                item.material = row['Material']
                item.peso = row['Peso']
                item.fino = row['Fino']
                item.unidade = row['Unidade']
                item.uso = row['Uso']
                item.data_alteracao = row['Data Alteração']
                item.obs = row['Observação']
                item.id_produto = row['Id_Produto']
                item.um_visual = row['Um Visual']
                item.codigo_cliente = row['Código Cliente']
                item.ncm = row['Ncm']
                item.familia = row['Família']
                item.setor = row['Setor']
                item.valor_unitario = row['Valor Unitário']
            else:
                new_item = Cadastro_itens(
                    item=row['Item'],
                    descricao=row['Descrição'],
                    cliente=row['Cliente'],
                    material=row['Material'],
                    peso=row['Peso'],
                    fino=row['Fino'],
                    unidade=row['Unidade'],
                    uso=row['Uso'],
                    data_alteracao=row['Data Alteração'],
                    obs=row['Observação'],
                    id_produto=row['Id_Produto'],
                    um_visual=row['Um Visual'],
                    codigo_cliente=row['Código Cliente'],
                    ncm=row['Ncm'],
                    familia=row['Família'],
                    setor=row['Setor'],
                    valor_unitario=row['Valor Família']
                )
                db.session.add(new_item)
        except KeyError as ke:
            import_errors.append(f"Erro de chave no índice {index}: Coluna {str(ke)} não encontrada.")
        except SQLAlchemyError as sqle:
            import_errors.append(f"Erro no banco de dados no índice {index}: {str(sqle)}")
        except Exception as e:
            import_errors.append(f"Erro desconhecido no índice {index}: {str(e)}")

    if import_errors:
        flash(f'Erros ocorreram durante a importação: {", ".join(import_errors)}', 'danger')
    else:
        try:
            db.session.commit()
            flash('Itens importados com sucesso', 'success')
        except SQLAlchemyError as sqle:
            db.session.rollback()
            flash(f'Erro ao salvar os itens no banco de dados: {str(sqle)}', 'danger')

    return redirect(url_for('cadastro_itens'))


@app.route('/estoque_visual', methods=['GET', 'POST'])
def estoque_visual():
    page = request.args.get('page', 1, type=int)
    filtro_cod = request.form.get('filtro_cod', '').upper()
    filtro_desc = request.form.get('filtro_desc', '').upper()

    if filtro_cod == "":
        filtro_cod = None

    if filtro_desc == "":
        filtro_desc = None

    if filtro_cod:
        visual = Lote_visual.query.filter(Lote_visual.item.ilike(f"%{filtro_cod}%")).paginate(page=page, per_page=10)
    elif filtro_desc:
        visual = Lote_visual.query.filter(Lote_visual.descricao.ilike(f"%{filtro_desc}%")).paginate(page=page, per_page=10)
    else:
        visual = Lote_visual.query.paginate(page=page, per_page=10)

    visual_items = []
    for lote in visual.items:
        desc = Def_cadastro_prod(lote.item)
        descricao = desc[5] if len(desc) > 5 else 'N/A'
        lote_dict = lote.__dict__
        lote_dict['descricao'] = descricao
        lote_dict.pop('_sa_instance_state', None)
        visual_items.append(lote_dict)

    return render_template('Estoque_Visual.html', visual=visual_items, visual_page=visual)

@app.route('/exportar_visual_excel')
def exportar_visual_excel():
    try:
        visual = Lote_visual.query.filter_by().all()

        data = {
            "Referencia": [item.referencia for item in visual],
            "Item": [item.item for item in visual],
            "Descrição": [Def_cadastro_prod(item.item)[5] for item in visual],
            "Lote": [item.numero_lote for item in visual],
            "Peso": [item.quantidade / 1000 for item in visual],
            "Unid": ['KG' for item in visual],
            "Operador que Produziu": [item.operador for item in visual],
        }
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Estoque Visual')
            
            workbook  = writer.book
            worksheet = writer.sheets['Estoque Visual']
            
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })
            
            worksheet.set_column(1, 1, 30)
            worksheet.set_column(3, 3, 20, cell_format)
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                if col_num == 2:
                    worksheet.set_column(col_num, col_num, 60)
                else:
                    worksheet.set_column(col_num, col_num, 18)
                
               
            
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)
        
        return send_file(output, download_name='Estoque_Visual.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/importar_visual', methods=['POST'])
def importar_visual():
    file = request.files.get('file')
    if not file:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado."})

    try:
        df = pd.read_excel(file)
        errors = []
        updated = 0
        created = 0

        for index, row in df.iterrows():
            try:
                lote_visual = Lote_visual.query.filter_by(item=row['Item'], numero_lote=row['Lote']).first()
                if lote_visual:
                    lote_visual.quantidade = row['Peso']
                    lote_visual.referencia = row['Referencia']
                    lote_visual.local = row['Unid']
                    db.session.commit()
                    updated += 1
                else:
                    new_lote = Lote_visual(
                        item=row['Item'],
                        numero_lote=row['Lote'],
                        quantidade=row['Peso'],
                        referencia=row['Referencia'],
                        local=row['Unid'],
                        tipo='Setor_Visual',
                        peso=0,
                        fino=0,
                        obs='',
                        data_criacao='',
                        processado_op=0,
                        quant_inicial=row['Peso'],
                        operador=row['Operador']
                    )
                    db.session.add(new_lote)
                    db.session.commit()
                    created += 1
            except Exception as e:
                errors.append(f"Erro no item {row['Item']} na linha {index}: {str(e)}")

        return jsonify({"success": True, "message": f"Importação concluída. {updated} itens atualizados, {created} itens criados. Erros: {'; '.join(errors)}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao processar o arquivo: {str(e)}"})



@app.route('/item/<item>', methods = ['GET','POST'])
def item(item):
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    item = item
    
    dados = Def_cadastro_prod(item)
    
    return  render_template('item.html',  dados = dados  )






@app.route('/setores', methods=['GET', 'POST'])
def setores():
    filtro_setor = request.form.get('filtro_setor', '').upper()
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    
    if filtro_setor:
        setores = Setores.query.filter(Setores.setor.contains(filtro_setor)).paginate(page=page, per_page=10)
    else:
        setores = Setores.query.paginate(page=page, per_page=10)
    
    return render_template('Setores.html', setores=setores)

@app.route('/add_setor', methods=['POST'])
def add_setor():
    setor = request.form.get('setor')
    meta_fino = request.form.get('meta_fino')
    meta_retalho = request.form.get('meta_retalho')
    meta_sucata = request.form.get('meta_sucata')
    meta_falha = request.form.get('meta_falha')
    meta_selecao = request.form.get('meta_selecao')
    meta_retrabalho = request.form.get('meta_retrabalho')
    meta_setup = request.form.get('meta_setup')
    
    novo_setor = Setores(setor=setor, meta_fino=meta_fino, meta_retalho=meta_retalho, meta_sucata=meta_sucata, 
                         meta_falha=meta_falha, meta_selecao=meta_selecao, meta_retrabalho=meta_retrabalho, meta_setup=meta_setup)
    
    db.session.add(novo_setor)
    db.session.commit()
    
    flash('Setor adicionado com sucesso!', 'success')
    return redirect(url_for('setores'))

@app.route('/deletar_setor/<int:id>', methods=['POST'])
def deletar_setor(id):
    setor = Setores.query.get_or_404(id)
    db.session.delete(setor)
    db.session.commit()
    flash('Setor deletado com sucesso!', 'success')
    return redirect(url_for('setores'))

@app.route('/exportar_setores')
def exportar_setores():
    setores = Setores.query.all()
    
    data = {
        "Setor": [setor.setor for setor in setores],
        "Meta Fino": [setor.meta_fino for setor in setores],
        "Meta Retalho": [setor.meta_retalho for setor in setores],
        "Meta Sucata": [setor.meta_sucata for setor in setores],
        "Meta Falha": [setor.meta_falha for setor in setores],
        "Meta Selecao": [setor.meta_selecao for setor in setores],
        "Meta Retrabalho": [setor.meta_retrabalho for setor in setores],
        "Meta Setup": [setor.meta_setup for setor in setores],
    }
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Setores')
        
        workbook  = writer.book
        worksheet = writer.sheets['Setores']
        
        # Formatação para a primeira linha (header)
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })
        
        # Formatação para as células de dados
        cell_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1,
            'align': 'center'
        })
        
        # Aplica a formatação na primeira linha
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # Ajusta a largura das colunas
            worksheet.set_column(col_num, col_num, 20)
        
        # Aplica a formatação nas células de dados
        for row_num, row_data in enumerate(df.values, 1):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num, col_num, cell_data, cell_format)

    output.seek(0)
    
    return send_file(output, download_name='Setores.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



@app.route('/operadores', methods=['GET', 'POST'])
def operadores():
    filtro_operador = request.form.get('filtro_operador', '').upper()
    setores = Setores.query.all()
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    
    if filtro_operador:
        operadores = Operadores.query.filter(Operadores.operador.contains(filtro_operador)).paginate(page=page, per_page=10)
    else:
        operadores = Operadores.query.paginate(page=page, per_page=10)
    
    return render_template('Operadores.html', operadores=operadores, setores=setores)

@app.route('/add_operador', methods=['POST'])
def add_operador():
    operador = request.form.get('operador')
    setor = request.form.get('setor')
    
    novo_operador = Operadores(operador=operador, setor=setor)
    
    db.session.add(novo_operador)
    db.session.commit()
    
    flash('Operador adicionado com sucesso!', 'success')
    return redirect(url_for('operadores'))

@app.route('/deletar_operador/<int:id>', methods=['POST'])
def deletar_operador(id):
    operador = Operadores.query.get_or_404(id)
    db.session.delete(operador)
    db.session.commit()
    flash('Operador deletado com sucesso!', 'success')
    return redirect(url_for('operadores'))

@app.route('/exportar_operadores')
def exportar_operadores():
    operadores = Operadores.query.all()
    
    data = {
        "Operador": [operador.operador for operador in operadores],
        "Setor": [operador.setor for operador in operadores],
    }
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Operadores')
        
        workbook  = writer.book
        worksheet = writer.sheets['Operadores']
        
        # Formatação para a primeira linha (header)
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })
        
        # Formatação para as células de dados
        cell_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1,
            'align': 'center'
        })
        
        # Aplica a formatação na primeira linha
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # Ajusta a largura das colunas
            worksheet.set_column(col_num, col_num, 20)
        
        # Aplica a formatação nas células de dados
        for row_num, row_data in enumerate(df.values, 1):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num, col_num, cell_data, cell_format)

    output.seek(0)
    
    return send_file(output, download_name='Operadores.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



@app.route('/familia', methods=['GET', 'POST'])
def familia():
    filtro_familia = request.form.get('filtro_familia', '').upper()

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)

    if filtro_familia:
        familias = Familia.query.filter(Familia.familia.contains(filtro_familia)).paginate(page=page, per_page=10)
    else:
        familias = Familia.query.paginate(page=page, per_page=10)

    return render_template('Familia.html', familias=familias)

@app.route('/add_familia', methods=['POST'])
def add_familia():
    familia = request.form.get('familia')

    nova_familia = Familia(familia=familia)

    db.session.add(nova_familia)
    db.session.commit()

    flash('Família adicionada com sucesso!', 'success')
    return redirect(url_for('familia'))

@app.route('/deletar_familia/<int:id>', methods=['POST'])
def deletar_familia(id):
    familia = Familia.query.get_or_404(id)
    db.session.delete(familia)
    db.session.commit()
    flash('Família deletada com sucesso!', 'success')
    return redirect(url_for('familia'))

@app.route('/exportar_familia')
def exportar_familia():
    familias = Familia.query.all()

    data = {
        "Família": [familia.familia for familia in familias],
    }

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Família')

        workbook  = writer.book
        worksheet = writer.sheets['Família']

        # Formatação para a primeira linha (header)
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center'
        })

        # Formatação para as células de dados
        cell_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1,
            'align': 'center'
        })

        # Aplica a formatação na primeira linha
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # Ajusta a largura das colunas
            worksheet.set_column(col_num, col_num, 20)

        # Aplica a formatação nas células de dados
        for row_num, row_data in enumerate(df.values, 1):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num, col_num, cell_data, cell_format)

    output.seek(0)

    return send_file(output, download_name='Familia.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')




@app.route('/sequencias', methods=['GET', 'POST'])
def sequencias():
    filtro_op = request.form.get('filtro_op', '').upper()

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)

    if filtro_op:
        sequencias = Sequencia_lote.query.filter(Sequencia_lote.op_visual.contains(filtro_op)).paginate(page=page, per_page=10)
    else:
        sequencias = Sequencia_lote.query.paginate(page=page, per_page=10)

    sequencia_op = Sequencia_op.query.filter_by(tabela_campo='ops_numero').first()

    return render_template('Sequencia_Lote.html', sequencias=sequencias, sequencia_op=sequencia_op)

@app.route('/alterar_sequencia_op', methods=['POST'])
def alterar_sequencia_op():
    tabela_campo = request.form.get('tabela_campo')
    valor = request.form.get('valor')
    valor_anterior = request.form.get('valor_anterior')

    sequencia = Sequencia_op.query.filter_by(tabela_campo=tabela_campo).first()

    if sequencia:
        sequencia.valor = valor
        sequencia.valor_anterior = valor_anterior
        db.session.commit()
        flash('Sequência OP alterada com sucesso!', 'success')
    else:
        flash('Erro ao alterar sequência OP.', 'danger')

    return redirect(url_for('sequencias'))

@app.route('/deletar_sequencia_lote/<string:op_visual>', methods=['POST'])
def deletar_sequencia_lote(op_visual):
    sequencia = Sequencia_lote.query.get_or_404(op_visual)
    db.session.delete(sequencia)
    db.session.commit()
    flash('Sequência de lote deletada com sucesso!', 'success')
    return redirect(url_for('sequencias'))



@app.route('/estoque_omie', methods=['GET', 'POST'])
def estoque_omie():
    filtro_cod = request.form.get('filtro_cod', '').upper()

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)

    if filtro_cod:
        configuracoes = Config_Visual.query.filter(Config_Visual.config.contains(filtro_cod)).paginate(page=page, per_page=10)
    else:
        configuracoes = Config_Visual.query.paginate(page=page, per_page=10)

    return render_template('Estoque_Omie.html', configuracoes=configuracoes)

@app.route('/add_config_omie', methods=['POST'])
def add_config_omie():
    config = request.form.get('config')
    info = request.form.get('info')

    nova_config = Config_Visual(config=config, info=info)
    db.session.add(nova_config)
    db.session.commit()

    flash('Configuração adicionada com sucesso!', 'success')
    return redirect(url_for('estoque_omie'))

@app.route('/deletar_config_omie/<config>', methods=['POST'])
def deletar_config_omie(config):
    configuracao = Config_Visual.query.get(config)
    if configuracao:
        db.session.delete(configuracao)
        db.session.commit()
        flash('Configuração deletada com sucesso!', 'success')
    else:
        flash('Configuração não encontrada.', 'danger')
    return redirect(url_for('estoque_omie'))


@app.route('/exportar_omie_excel')
def exportar_omie_excel():
    try:
        configuracoes = Config_Visual.query.all()

        data = {
            "Config": [config.config for config in configuracoes],
            "Info": [config.info for config in configuracoes]
        }

        df = pd.DataFrame(data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Estoque Omie')

            workbook  = writer.book
            worksheet = writer.sheets['Estoque Omie']

            # Formatação para a primeira linha (header)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })

            # Formatação para as células de dados
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })

            # Aplica a formatação na primeira linha
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ajusta a largura das colunas
                worksheet.set_column(col_num, col_num, 20)

            # Aplica a formatação nas células de dados
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)

        return send_file(output, download_name='Estoque_Omie.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/atualizar_config_omie', methods=['POST'])
def atualizar_config_omie():
    config = request.form.get('config')
    info = request.form.get('info')

    configuracao = Config_Visual.query.get(config)
    if configuracao:
        configuracao.info = info
        db.session.commit()
        flash('Configuração atualizada com sucesso!', 'success')
    else:
        flash('Configuração não encontrada.', 'danger')
    
    return redirect(url_for('estoque_omie'))



@app.route('/update', methods=['GET', 'POST'])
def update():
        if not current_user.is_authenticated:
            return redirect( url_for('login'))
        data = {
                "call":"AlterarProduto",
                "app_key":app_key,
                "app_secret":app_secret,
                "param":[{
                    "codigo":"teste1235",
                    "descricao":"Produto de teste",
                    "unidade":"UN"
                    }
            ]}

        return redirect(url_for('itens'))


@app.route('/gerenciar_estoque', methods = ['GET','POST'])
def gerenciar_estoque(): 
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    return  render_template('gerenciar_estoque.html')

@app.route('/estoque', methods = ['GET','POST'])
def estoque():
    Error = ""
    if not current_user.is_authenticated: # tipo, saldoFisico, unidade, valor_unitario, descricao, item
        return redirect( url_for('login'))
    
    if request.form.get("item") == None:
        item = itemgeral
    else:
        item = request.form.get("item")
    
    if item != None:
        status = Def_item_ok(item)

        if status[0] == "ok":
            item = status[1]
            error = "Sucesso" 
            flash (f'Consulta do item {item} = {status[0]}, Realizada com Sucesso', category='success')
        
        else:
            error = "Erro"

            flash (f' Código: {item} = não Encontrado','error')

    consulta = Lote_visual.query.filter_by(item = item).all()
    
    # consulta = Lote_visual.query.get(item).all()
    unidade = Def_cadastro_prod(item)[12]
    
    setor_all = 0
    peso_all = 0
    setor_a1 = 0
    setor_ac = 0
    setor_se = 0
    setor_cq = 0
    setor_as = 0
    setor_a3 = 0
    setor_mkm = 0
   
    
    for row in consulta:
        if row.local == "2436985075":
            setor_a1 = (setor_a1 + row.quantidade)
        elif row.local == "2511785274":
            setor_ac = (setor_ac + row.quantidade)
        elif row.local == "4085566100":
            setor_se = (setor_se + row.quantidade)
        elif row.local == "4085565942":
            setor_cq = (setor_cq + row.quantidade)
        elif row.local == "4085566245":
            setor_as = (setor_as + row.quantidade)
        elif row.local == "4084861665":
            setor_a3 = (setor_a3 + row.quantidade)
        elif row.local == "4085566344":
            setor_mkm = (setor_mkm + row.quantidade)
        
        setor_all = (setor_all + row.quantidade)
        peso_all = (peso_all + row.peso)
    

    return  render_template('estoquer2.html', consulta = consulta, unidade = unidade,
                             item = item, setor_a1 = setor_a1, setor_ac = setor_ac, setor_se = setor_se,
                              setor_cq = setor_cq, setor_as = setor_as, setor_a3 = setor_a3,
                               setor_mkm = setor_mkm, setor_all = setor_all, peso_all = peso_all, error = error)

    
    


@app.route('/lista_movimento', methods = ['GET','POST'])
def lista_movimento():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    page = request.args.get('page', 1, type=int)
    item = request.form.get("item")
    if item == None:
        dados = Movimentos_estoque.query.order_by(Movimentos_estoque.id.desc()).paginate(page=page,per_page=20)
    else:
        dados = Movimentos_estoque.query.order_by(Movimentos_estoque.id.desc()).filter_by(item = item).paginate(page=page,per_page=20)
    return  render_template('lista_movimento.html',  movimentos = dados)

@app.route('/lista_movimento_filtro', methods = ['GET','POST'])
def lista_movimento_filtro():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    page = request.args.get('page', 1, type=int)
    data_movimento = request.form.get("data")
    if data_movimento == None:
        filtro = Movimentos_estoque.query.order_by(Movimentos_estoque.id.desc()).paginate(page=page,per_page=20)
    else:
        filtro = Movimentos_estoque.query.order_by(Movimentos_estoque.id.desc()).filter_by(data_movimento = data_movimento).paginate(page=page,per_page=20)
    
    return  render_template('lista_movimento_filtro.html', filtro = filtro, data_movimento = data_movimento)

# ================================== OPS ===============================================#

@app.route('/update_op', methods=['GET', 'POST'])
def update_op():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    
    if request.method == 'POST':
        edit_item = Ops_visual.query.get(request.form.get('id'))  
        edit_item.item = request.form.get("item")
        edit_item.descrição = request.form.get("descricao")
        edit_item.quantidade = request.form.get("quantidade")
        edit_item.piv = request.form.get("piv")
        edit_item.setor = request.form.get("setor")
        edit_item.operador = request.form.get("operador")

        db.session.commit()
        
        flash (f'Op editada com sucesso', category='success')

        return redirect(url_for('ordens_producao_visual'))
        


@app.route('/delete_op/<id>', methods=['GET', 'POST'])
def delete(id):
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    item = Ops_visual.query.get(id)

    db.session.delete(item)
    db.session.commit()

    flash (f'Op deletada com sucesso', category='success')

    return redirect(url_for('ordens_producao_visual'))


# ===============================Ordem de produção Visual================================================

@app.route('/ordens_producao_visual', methods=['GET', 'POST'])
def ordens_producao_visual():
    filtro_op = request.form.get("filtro_op")
    filtro_cod = request.form.get("filtro_cod")
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    
    if filtro_op == "":
        filtro_op = None
    
    if filtro_cod == "":
        filtro_cod = None

    if filtro_op is not None:
        dados = Ops_visual.query.order_by(Ops_visual.numero_op_visual.desc()).filter_by(numero_op_visual=filtro_op).paginate(page=page, per_page=10)
    else:
        if filtro_cod is not None:
            dados = Ops_visual.query.order_by(Ops_visual.numero_op_visual.desc()).filter_by(item=filtro_cod).paginate(page=page, per_page=10)
        else:
            dados = Ops_visual.query.order_by(Ops_visual.numero_op_visual.desc()).paginate(page=page, per_page=10)    
    
    setores = Setores.query.all()
    operadores = Operadores.query.all()
    cadastro_itens = Cadastro_itens.query.all()

    setores_dict = [setor.__dict__ for setor in setores]
    operadores_dict = [operador.__dict__ for operador in operadores]
    cadastro_itens_dict = [item.__dict__ for item in cadastro_itens]
    
    for d in setores_dict + operadores_dict + cadastro_itens_dict:
        d.pop('_sa_instance_state', None)

    return render_template('ordens_producao_visual.html', itens=dados, setores=setores_dict, operadores=operadores_dict, cadastro_itens=cadastro_itens_dict)



@app.route('/insert_op_Visual', methods=['POST'])
def insert_op_visual():     
    hora_atual = datahora("hora")
    data_atual = datahora("data")
    # ano_dia = date.today().strftime("%Y%d")
    # hora_minuto = datetime.now().strftime("%H%M")
    numero_op_visual = Def_numero_op()

    if request.method == 'POST':
        item = request.form.get("item")
        status = Def_item_ok(item)
        if status[0] == "ok":
            item = status[1]


            situação = "Aberta"       
            descrição = Def_descricao(item)
            piv = request.form.get("piv")
            setor = request.form.get("setor")
            operador = request.form.get("operador")
            quantidade = float(request.form.get("quantidade"))
            data_abertura = data_atual
            hora_abertura = hora_atual
            peso_enviado = 0
            fino_enviado = 0
            peso_retornado = 0
            fino_retornado = 0
            quantidade_real = 0

            novo_item = Ops_visual(numero_op_visual=numero_op_visual, situação=situação, item=item,
                                   piv = piv, descrição=descrição, quantidade=quantidade,
                                   peso_enviado=peso_enviado, peso_retornado=peso_retornado,
                                   fino_enviado=fino_enviado, fino_retornado=fino_retornado,
                                   data_abertura = data_abertura, hora_abertura = hora_abertura,
                                   setor = setor, operador = operador, quantidade_real = quantidade_real)

            db.session.add(novo_item)
            db.session.commit()


            
            
            referencia = numero_op_visual
            
            tipo = "Material Produzido"
            peso = 0
            fino = 0
            Def_mov_op(referencia, tipo, item, descrição, quantidade, peso, fino)



            flash (f'OP para o item {item} Aberta com sucesso', category='success')
        else:
             flash (f' Código: {item} - não cadastrado - ERRO={status}', category='success')
                

    return redirect(url_for('ordens_producao_visual'))


#-------------------definições para atributo de botões -------------------

@app.route('/temp_coproduto', methods = ['GET','POST'])
def temp_coproduto():
    global text_botoes
    text_botoes = "Coproduto Produzido"
    return text_botoes


@app.route('/temp_sucata', methods = ['GET','POST'])
def temp_sucata():
    global text_botoes
    text_botoes = "Sucata Produzida"
    return text_botoes


@app.route('/temp_retalhado', methods = ['GET','POST'])
def temp_retalhado():
    global text_botoes
    text_botoes = "Retalho Produzido"
    return text_botoes


@app.route('/temp_produzido', methods = ['GET','POST'])
def temp_produzido():
    global text_botoes
    text_botoes = "Material Produzido"
    return text_botoes



@app.route('/temp_substituto', methods = ['GET','POST'])
def temp_substituto():
    global text_botoes
    text_botoes = "Substituto Enviado"
    return text_botoes


@app.route('/temp_retalho', methods = ['GET','POST'])
def temp_retalho():
    global text_botoes
    text_botoes = "Retalho Enviado"
    return text_botoes

@app.route('/temp_insumo', methods = ['GET','POST'])
def temp_insumo():
    global text_botoes
    text_botoes = "insumo Enviado"
    return text_botoes


@app.route('/op/<numero_op_visual>', methods = ['GET','POST'])
def op(numero_op_visual):
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    op = numero_op_visual
    item = request.form.get("item")
    setor = request.form.get("setor")
    operador = request.form.get("operador")
    descricao = request.form.get("descricao")
    op_qtd = request.form.get("op_qtd")
    ref = [op, item, descricao, op_qtd, setor, operador]
    mov_op = Estrutura_op.query.filter_by(op_referencia = op).all()  
    op_info = Ops_visual.query.filter_by(numero_op_visual = op).all()
    estrutura_op = Def_consulta_estrutura(item)
    operadores = Operadores.query.filter_by(setor = setor).all()
    
    return render_template("mov_op_visual.html", ref=ref, op_info=op_info, op=op, estrutura_op= estrutura_op, mov_op = mov_op, operadores = operadores, ope_pd = operador)



# ================================== LOTES ==============================================================


@app.route('/add_lote_mov_op', methods = ['GET','POST'])
def add_lote_mov_op():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    
    item = request.form.get("item")
    referencia = request.form.get("referencia")
    lote_visual = request.form.get("lote_visual")
    tipo = request.form.get("tipo_mov")
    numero_lote = request.form.get("numero_lote")
    quant = request.form.get("quantidade")
    qtd_parcial = request.form.get("qtd_parcial")
    id_lote = request.form.get("id")
    id_mov = request.form.get("id_mov")
    peso_parcial = request.form.get("peso_parcial")
    fino = request.form.get("fino")
    data_mov = datahora("data")
    operador = request.form.get("operador")
    
    if qtd_parcial == None:
        qtd_parcial = 0
        x = 0
    else:
        x = int(qtd_parcial)
        peso_parcial = int(peso_parcial)

    if quant == None:
        quant = 0
        y = 0
    else:
        y = int(quant)

    if fino == None:
        fino = 0
        fino_parcial = 0        

    if x <= y and x > 0:
        fino_parcial = float(fino)  * (x / y)
        
        add_lote_mov_op = Lotes_mov_op(referencia = referencia, tipo = tipo, item = item, lote_visual = lote_visual,
                                        numero_lote = numero_lote, quantidade = qtd_parcial, peso = peso_parcial,
                                        fino = fino_parcial, data_mov = data_mov, id_lote = id_lote, operador = operador) 

        db.session.add(add_lote_mov_op)
        db.session.commit()

        
        env_lote = Lote_visual.query.get(id_lote)
        
        env_lote.quantidade = y - x
        env_lote.peso = env_lote.peso - peso_parcial
        #local = request.form.get("local")
                
        db.session.commit()
    
        
        ajust_mov = Estrutura_op.query.get(id_mov)
        if ajust_mov.quantidade_real == None:
            ajust_mov.quantidade_real = int(qtd_parcial)
        else:
            ajust_mov.quantidade_real = ajust_mov.quantidade_real + int(qtd_parcial)

        if ajust_mov.peso == None:
            ajust_mov.peso = peso_parcial
        else:
            ajust_mov.peso = ajust_mov.peso + peso_parcial

        if ajust_mov.fino == None:
            ajust_mov.fino = fino_parcial
        else:
            ajust_mov.fino = ajust_mov.fino + fino_parcial

        db.session.commit()

        op_dados = Ops_visual.query.filter_by(numero_op_visual = referencia).all()
        for dados_op in op_dados:
            id_op = dados_op.id
        ajuste_op = Ops_visual.query.get(id_op)
        if tipo == "Enviar Insumo" or tipo == "Enviar Retalho" or tipo == "Enviar Retalho" or tipo == "Enviar item Substituto":
            if ajuste_op.peso_enviado == None:
                ajuste_op.peso_enviado = peso_parcial
            else:
                ajuste_op.peso_enviado = ajuste_op.peso_enviado + peso_parcial
                
            if ajuste_op.fino_enviado == None:
                ajuste_op.fino_enviado = fino_parcial
            else:
                ajuste_op.fino_enviado = ajuste_op.fino_enviado + fino_parcial
        else:
            if ajuste_op.peso_retornado == None:
                ajuste_op.peso_retornado = peso_parcial
            else:
                ajuste_op.peso_retornado = ajuste_op.peso_retornado + peso_parcial
            if ajuste_op.fino_retornado == None:
                ajuste_op.fino_retornado = fino_parcial
            else:
                ajuste_op.fino_retornado = ajuste_op.fino_retornado + fino_parcial


        if tipo == "Material Produzido":
            ajuste_op.quantidade_real = ajuste_op.quantidade_real + qtd_parcial

        db.session.commit()

        error = "Sucesso" 
        flash (f'Lote: {numero_lote} ,lançado na Ordem Com Sucesso', category='success')
                
    else:
        error = "Error"

        flash (f' Quantidade do Lote fora da Quantidade Disponivel')
    #return redirect(request.referrer)

    return lotes_mov_op(referencia, item)
    
@app.route('/add_lote_mov_op_prod', methods = ['GET','POST'])
def add_lote_mov_op_prod():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    
    item = request.form.get("item")
    referencia = request.form.get("referencia")
    #lote_visual = Def_numero_lote(referencia)
    tipo = request.form.get("tipo_mov")
    qtd_parcial = request.form.get("qtd_parcial")
    id = request.form.get("id")
    peso_parcial = request.form.get("peso_parcial")
    local = request.form.get("local_dest")
    data_mov = datahora("data")
    OP_Origem = request.form.get("OP_Origem")
    operador = request.form.get("operador")
    op_dados = Ops_visual.query.filter_by(numero_op_visual = referencia).all()
    for dados_op in op_dados:
        if operador == None or operador == "":
            operador = dados_op.operador
        id_op = dados_op.id
    um_visual = Def_cadastro_prod(item)[12]
    if um_visual == "GR":
        qtd_parcial = peso_parcial
        if Def_locais(local) == "Estoque":
            lote_peso ="Sim"
        else:
            lote_peso = "Não"    
    else:
        lote_peso = "Não"

    id_prod = Def_id_produto(item)
    fino_uni = Def_Caracter(id_prod)[0]

    if fino_uni == None:
        fino_uni = 0
        fino_parcial = 0
    else:
        fino_parcial = int(qtd_parcial.replace(".0","")) * float(fino_uni.replace(",","."))


    
    fino = fino_parcial
        
    qtd_parcial = int(qtd_parcial.replace(".0",""))

    if qtd_parcial == None:
        qtd_parcial = 0
        x = 0
    else:
        x = int(qtd_parcial)
        peso_parcial = int(peso_parcial)

    
    
    if x > 0:
        
        status_ajustes = Def_ajuste_estoque(item, qtd_parcial,"ENT", local, referencia, tipo, peso_parcial, "-", 1, lote_peso, operador)
        print("id_lote do add")
        print(status_ajustes) 
        id_lote = status_ajustes[7]
        lote_visual = status_ajustes[8]

        add_lote_mov_op = Lotes_mov_op(referencia = referencia, tipo = tipo, item = item, lote_visual = lote_visual,
                                        numero_lote = lote_visual, quantidade = qtd_parcial, peso = peso_parcial,
                                        fino = fino_parcial, data_mov = data_mov, id_lote = id_lote, operador = operador) 

        db.session.add(add_lote_mov_op)
        db.session.commit()

        
        
        
        ajust_mov = Estrutura_op.query.get(id)
        if ajust_mov.quantidade_real == None:
            ajust_mov.quantidade_real = int(qtd_parcial)
        else:
            ajust_mov.quantidade_real = ajust_mov.quantidade_real + int(qtd_parcial)

        if ajust_mov.peso == None:
            ajust_mov.peso = peso_parcial
        else:
            ajust_mov.peso = ajust_mov.peso + peso_parcial

        if ajust_mov.fino == None:
            ajust_mov.fino = fino_parcial
        else:
            ajust_mov.fino = ajust_mov.fino + fino_parcial

        db.session.commit()

        op_dados = Ops_visual.query.filter_by(numero_op_visual = referencia).all()
        for dados_op in op_dados:
            if operador == None:
                operador = dados_op.operador
            id_op = dados_op.id
        ajuste_op = Ops_visual.query.get(id_op)
        if tipo == "Enviar Insumo" or tipo == "Enviar Retalho" or tipo == "Enviar Retalho" or tipo == "Enviar item Substituto":
            if ajuste_op.peso_enviado == None:
                ajuste_op.peso_enviado = peso_parcial
            else:
                ajuste_op.peso_enviado = ajuste_op.peso_enviado + peso_parcial
                
            if ajuste_op.fino_enviado == None:
                ajuste_op.fino_enviado = fino_parcial
            else:
                ajuste_op.fino_enviado = ajuste_op.fino_enviado + fino_parcial
        else:
            if ajuste_op.peso_retornado == None:
                ajuste_op.peso_retornado = peso_parcial
            else:
                ajuste_op.peso_retornado = ajuste_op.peso_retornado + peso_parcial
            if ajuste_op.fino_retornado == None:
                ajuste_op.fino_retornado = fino_parcial
            else:
                ajuste_op.fino_retornado = ajuste_op.fino_retornado + fino_parcial


        if tipo == "Material Produzido":
            ajuste_op.quantidade_real = ajuste_op.quantidade_real + int(qtd_parcial)

        db.session.commit()

        error = "Sucesso" 
        flash (f'Lote: {lote_visual} ,lançado na Ordem Com Sucesso', category='success')
                
    else:
        error = "Error"

        flash (f' Quantidade do Lote fora da Quantidade Disponivel')
    return redirect(request.referrer)

    #return lotes_mov_op(referencia, item)





@app.route('/adicionar_lote', methods = ['GET','POST'])
def adicionar_lote():
    nova_estrutura = ""

    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    item = request.form.get("item")
    status = Def_item_ok(item)
    if status[0] == "ok":
        item = status[1]

    
        referencia = request.form.get("referencia")
        # lote = str(int(db.session.query(db.func.max(Lote.lote)).scalar() or 0) + 1)
        lote = Def_numero_lote(referencia)
        numero_lote = "".join([str(lote), "/", str(referencia) ])
        quantidade = request.form.get("quantidade")
        data_criacao = datahora("data")
        #data_validade = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')
        tipo = "visual"
        peso = 1
        fino = 0.050
        local = A1
        novo_lote = Lote_visual(referencia=referencia, tipo=tipo, lote_visual=lote, numero_lote=numero_lote, quantidade=quantidade, peso=peso, fino=fino, local=local, data_criacao=data_criacao, quant_inicial = quantidade)
        
        estrutura_op = Def_consulta_estrutura(item)

        if estrutura_op.get('ident') == None:
            for row in estrutura_op["itens"]:
                qtd_unitaria = float(row.get('quantProdMalha'))
                nova_estrutura = Estrutura_op(referencia=referencia, 
                item_estrutura=row.get("codProdMalha"), 
                descricao_item=row.get("descrProdMalha"),
                quantidade_item=float(quantidade) * float(qtd_unitaria))
                db.session.add(nova_estrutura) 

        
        db.session.add(novo_lote)
        db.session.commit()
        flash (f'Lote para o item {item} criado com sucesso', category='success')
    else:
        flash (f' Código: {item} - não cadastrado - ERRO={status}', category='success')

    
    return redirect(request.referrer)


@app.route('/adicionar_lote_geral', methods = ['GET','POST'])
def adicionar_lote_geral():
    
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    
    item = request.form.get("item")
    if item != None:
        status = Def_item_ok(item)

    
        if status[0] == "ok":
            item = status[1]
            referencia = request.form.get("referencia")
            
            quantidade = request.form.get("quantidade")
            quantidade = float(quantidade)
            tipo = request.form.get("tipo")
            peso = request.form.get("peso")
            local = request.form.get("local")
            
            operador = "Kels"
            obs = request.form.get("obs")
            if obs == None or obs == "":
                obs = "-"
            status_omie = Def_ajuste_estoque(item, quantidade,"ENT", local, referencia, tipo, peso, obs, 0,"Não", operador)
            
           # flash (f'Lote: {status_omie[6]} Lançado para o item: {item} = {status_omie[2]}, Quantidade Omie = {status_omie[5]} {um_omie}', category='success')
    else:
        flash (f'   Código: {item} = vazio / erro: {status}', category='danger')

    global itemgeral
    itemgeral = item  

    return redirect(url_for('estoque'))



@app.route('/deleta_lote', methods=['GET', 'POST'])
def deleta_lote():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    id = request.form.get("id")
    id_delete = Lote_visual.query.get(id)
    if id_delete == None:
        flash (f'Lote com id: {id}, não identificado -- Lote não Deletado!', category='success')
        return redirect(request.referrer)
    else:
        item = request.form.get("item")
        lote = request.form.get("lote_visual")
        referencia = request.form.get("referencia")
        quantidade = request.form.get("quantidade")
        peso = request.form.get("peso")
        quantidade = int(quantidade)
        obs = request.form.get("obs")
        tipo = "Visual"
        local = request.form.get("local")
        operador = "Kels"
        db.session.delete(id_delete)
        db.session.commit()

        omie = Def_ajuste_estoque(item, quantidade,"SAI", local, referencia, tipo, peso, obs, id,"Não", operador)
        status = omie[2]
        
        flash (f'Lote : {lote}/{referencia}, do item: {item} visual excluido com sucesso/ omie status: {status}', category='success')
        #consulta = Lote_visual.query.filter_by(item = item).all()

        #info = Def_cadastro_prod(item,A1)

        global itemgeral
        itemgeral = item  
    
    return redirect(url_for('estoque'))


@app.route('/lotes/<op_referencia>/<item_estrutura>', methods = ['GET','POST'])

def lotes_mov_op(op_referencia, item_estrutura):
    if request.form.get("descricao_item") == None:

        op_mov = Estrutura_op.query.filter_by(op_referencia = op_referencia, item_estrutura = item_estrutura).all()
        for dados_mov_op in op_mov:
            id_mov = dados_mov_op.id
        ajuste_op = Estrutura_op.query.get(id_mov)
        descricao_item = ajuste_op.descricao_item
        quantidade_item_total = ajuste_op.quantidade_real
        tipo_mov  = ajuste_op.tipo_mov
        peso_item_total  = ajuste_op.peso
        fino_item_total  = ajuste_op.fino
    else:
        descricao_item = request.form.get("descricao_item")
        quantidade_item_total = request.form.get("quantidade_item")
        tipo_mov = request.form.get("tipo_mov")
        peso_item_total = request.form.get("peso")
        fino_item_total = request.form.get("fino")
        id_mov = request.form.get("id_mov")

    Lotes_mov = Lotes_mov_op.query.order_by(Lotes_mov_op.id.desc()).filter_by(referencia = op_referencia,item = item_estrutura)
    lotes = Lote_visual.query.order_by(Lote_visual.id.desc()).filter_by(processado_op = 0, item = item_estrutura).filter(Lote_visual.quantidade > 0)
    op_dados = Ops_visual.query.filter_by(numero_op_visual = op_referencia).all()
    return render_template("lotes_mov_op.html", Lotes_mov = Lotes_mov, lotes = lotes, op_referencia = op_referencia, item_estrutura = item_estrutura,
                           descricao_item = descricao_item, quantidade_item_total = quantidade_item_total, op_dados = op_dados,
                           peso_item_total = peso_item_total, fino_item_total = fino_item_total, tipo_mov = tipo_mov, id_mov = id_mov)

@app.route('/lotes_prod/<op_referencia>/<item_estrutura>', methods = ['GET','POST'])
def lotes_mov_op_prod(op_referencia, item_estrutura):
    if request.form.get("descricao_item") == None:

        op_mov = Estrutura_op.query.filter_by(op_referencia = op_referencia, item_estrutura = item_estrutura).all()
        for dados_mov_op in op_mov:
            id_mov = dados_mov_op.id
        ajuste_op = Estrutura_op.query.get(id_mov)
        descricao_item = ajuste_op.descricao_item
        quantidade_item_total = ajuste_op.quantidade_real
        tipo_mov  = "Material Produzido"
        peso_item_total  = ajuste_op.peso
        fino_item_total  = ajuste_op.fino
    else:
        descricao_item = request.form.get("descricao_item")
        quantidade_item_total = request.form.get("quantidade_item")
        tipo_mov = request.form.get("tipo_mov")
        peso_item_total = request.form.get("peso")
        fino_item_total = request.form.get("fino")
        id_mov = request.form.get("id_mov")
    
    op_dados = Ops_visual.query.filter_by(numero_op_visual = op_referencia).all()
    Lotes_mov = Lotes_mov_op.query.order_by(Lotes_mov_op.id.desc()).filter_by(referencia = op_referencia,item = item_estrutura)
    #lotes = Lote_visual.query.order_by(Lote_visual.id.desc()).filter_by(processado_op = 0, item = item_estrutura)

    return render_template("lotes_mov_op_prod.html", Lotes_mov = Lotes_mov, op_referencia = op_referencia, item_estrutura = item_estrutura,
                           descricao_item = descricao_item, quantidade_item_total = quantidade_item_total, op_dados = op_dados,
                           peso_item_total = peso_item_total, fino_item_total = fino_item_total, tipo_mov = tipo_mov, id_mov = id_mov)







@app.route('/estrutura_op/<numero_op_visual>/<numero_lote>', methods = ['GET','POST'])
def estrutura_op(numero_op_visual, numero_lote):
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    op = numero_op_visual
    lote = numero_op_visual + "/" + numero_lote
    itens_movimentados = Movimentos_estoque.query.filter_by(op_referencia = op).all()   
    op_dados = Ops_visual.query.filter_by(numero_op_visual = op).all()

    mov_op = Estrutura_op.query.filter_by(op_referencia = op).all()  
      
    return render_template("estrutura_op.html", itens_movimentados=itens_movimentados, lote=lote, op=op, op_dados=op_dados, mov_op=mov_op)


@app.route('/encerra_op', methods=['GET', 'POST'])
def encerra_op():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    if request.method == 'POST':
        id = request.form.get('id')
        situacao = request.form.get('situacao')
        encerra = Ops_visual.query.get(id)  
        encerra.situação = situacao
        db.session.commit()
        if situacao == "Aberta":
            flash (f'Op Reaberta com sucesso', category='success')
        else:
            flash (f'Op Encerrada com sucesso', category='success')
    return redirect(url_for('ordens_producao_visual'))

@app.route('/add_mov_op', methods = ['GET','POST'])
def add_mov_op():
        
    item = request.form.get("item")
    if item != None:
        status = Def_item_ok(item)

    
        if status[0] == "ok":
            item = status[1]
            id_produto = status[2].get('id_produto')
            referencia = request.form.get("referencia")
            
            quantidade = request.form.get("quantidade_item")
            #quantidade = float(quantidade)
            #data_validade = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')
            tipo = text_botoes
            peso = 0
            fino = 0
            #fino = float(peso) * (float(tempfino[0].replace(",",".")) / float(tempfino[1].replace(",",".")) )
            descricao = status[2].get('descricao')            
            Def_mov_op(referencia, tipo, item, descricao, quantidade, peso, fino)
            
            flash (f'Seleção para o Item: {item}, lançado para uma quantidade total aproximada = {quantidade}', category='success')
    else:
        flash (f'   Código: {item} = vazio / erro: {status}', category='danger')

    
    return redirect(request.referrer)



@app.route('/deleta_lotes_mov_op', methods=['GET', 'POST'])

def deleta_lotes_mov_op():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    id = request.form.get("id")
    lotes_mov_op = Lotes_mov_op.query.get(id)
    id_lote = request.form.get('id_lote')
    referencia = request.form.get('referencia')
    qtd_parcial = request.form.get("quantidade")
    peso_parcial = request.form.get("peso")
    fino_parcial = request.form.get("fino")
    item = request.form.get("item")

    db.session.delete(lotes_mov_op)
    db.session.commit()
    
    
    env_lote = Lote_visual.query.get(id_lote)
    db.session.delete(env_lote)
    
    db.session.commit()
       


    ajust_mov_temp = Estrutura_op.query.filter_by(op_referencia = referencia, item_estrutura = item).all()
    for estru in ajust_mov_temp:
        id_estru = estru.id
    ajust_mov = Estrutura_op.query.get(id_estru)

    ajust_mov.quantidade_real = int(ajust_mov.quantidade_real) - int(qtd_parcial)
    ajust_mov.peso = int(ajust_mov.peso) - int(peso_parcial)
    ajust_mov.fino = int(ajust_mov.fino) - int(fino_parcial)

    db.session.commit()

    op_dados = Ops_visual.query.filter_by(numero_op_visual = referencia).all()
    for dados_op in op_dados:
       id_op = dados_op.id
    ajuste_op = Ops_visual.query.get(id_op)
    
    ajuste_op.peso_retornado = int(ajuste_op.peso_retornado) - int(peso_parcial)
    ajuste_op.fino_retornado = int(ajuste_op.fino_retornado) - int(fino_parcial)
    ajuste_op.quantidade_real = int(ajuste_op.quantidade_real) - int(qtd_parcial)

    db.session.commit()

    return redirect(request.referrer)



@app.route('/deleta_mov_op', methods=['GET', 'POST'])
def deleta_mov_op():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    id = request.form.get("id")
    estrutura_op = Estrutura_op.query.get(id)

    db.session.delete(estrutura_op)
    db.session.commit()   


    return redirect(request.referrer)



@app.route('/deleta_movimento_item', methods=['GET', 'POST'])
def deleta_movimento_item():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    id = request.form.get("id")
    movimento = Movimentos_estoque.query.get(id)

    db.session.delete(movimento)
    db.session.commit()   


    return redirect(request.referrer)




@app.route('/transferir_saldo_posicao', methods=['GET', 'POST'])
def transferir_saldo_posicao():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    
    if request.method == 'POST':
        transf_lote = Lote_visual.query.get(request.form.get('id'))
        id_lote = transf_lote.id
        transf_lote.local = request.form.get("local_dest")
        local_dest = request.form.get("local_dest")
        quan = request.form.get("quantidade")
        local = request.form.get("local")
        item = request.form.get("item")

        db.session.commit()
        
        status = Def_tranf_estoque(item, quan, local, local_dest, id_lote)


        flash (f'Lote transferido com sucesso, status: {status[2]}', category='success')

        global itemgeral
        itemgeral = item  

    return redirect(url_for('estoque'))



@app.route('/posicoes_estoque_omie', methods=['GET', 'POST'])
def posicoes_estoque_omie():
    if not current_user.is_authenticated:
        return redirect( url_for('login'))
    item = request.form.get("item")

    cadastro = Def_cadastro_prod(item)
    id_produto = cadastro[0]


 
    qtda1 = Def_consulta_estoque(id_produto,A1)
    qtdac = Def_consulta_estoque(id_produto,AC) 
    qtdse = Def_consulta_estoque(id_produto,SE)
    qtdcq = Def_consulta_estoque(id_produto,CQ)
    qtdas = Def_consulta_estoque(id_produto,AS)

    Tqtda1 = cadastro
    
    saldototal =  qtda1 + qtdac + qtdse + qtdcq + qtdas
    
    unidadeI = cadastro[3]

    convert =  Def_Convert_Unidade("Consulta", unidadeI)
    unidade = convert[0]
    fator = convert[2]
    qtda1 = qtda1 * fator
    qtdac = qtdac * fator 
    qtdse = qtdse * fator
    qtdcq = qtdcq * fator
    qtdas = qtdas * fator
    
    qtda1 = int(qtda1)
    qtdac = int(qtdac)
    qtdse = int(qtdse)
    qtdcq = int(qtdcq)
    qtdas = int(qtdas)

    qtdtol = qtda1 + qtdac + qtdse + qtdcq + qtdas

    if saldototal == 0:
        frase = "item de Sem Saldo em Estoque"
    else:
        saldototal = str(saldototal)
        saldototal = saldototal.replace(".",",")
        #frase = (f'Saldo Total do Item: {item} = {qtdtol:.0f} {unidade} _ _||_ _ Omie = {locale.format_string("%1.3f", saldototal, grouping=True)} {unidadeI}')
        frase = (f'Saldo Total do Item: {item} = {qtdtol:.0f} {unidade} _ _||_ _ Omie = {saldototal} {unidadeI}')
    return  render_template('posicoes_estoque.html', frase = frase, Tqtda1 = Tqtda1,
                             qtda1 = qtda1, qtdac = qtdac, qtdse = qtdse, qtdcq = qtdcq,
                              qtdas = qtdas, unidade = unidade)

#=============================definições do diego =================================#    

@app.route('/teste_diego', methods = ['GET','POST'])
def teste_diego():
    item = request.form.get('teste_item')
    
    teste = Def_cadastro_prod(item)
    
    id_produto = teste[0]
    if id_produto == None:
       id_produto = 0
    
    saldoFisico = Def_consulta_estoque(id_produto, A1)
    if saldoFisico == None:
       saldoFisico = 2
       
    caracter = Def_Caracter(id_produto)
    fino = caracter[0]
    peso = caracter[1]
    
    return render_template('teste.html',item = item, teste = teste, id_produto = id_produto,saldoFisico = saldoFisico, fino = fino, peso = peso)

# <=========================teste de saldo por ID===============================>
@app.route('/teste_saldo', methods = ['GET','POST'])
def teste_saldo():      
     
    id_prod = request.form.get('teste_saldo')
      
    saldoFisico = Def_consulta_estoque(id_prod, A1)
    if saldoFisico == None:
       saldoFisico = 3

       
    return render_template('saldo.html',id_prod = id_prod, saldoFisico = saldoFisico)


@app.route('/processar_faturamento', methods = ['GET','POST'])
def processar_faturamento():
    return ("o Processamento das Notas faturadas ainda esta sendo feito Manualmente")



@app.route('/processar_recebimento', methods = ['GET','POST'])
def processar_recebimento():
    return ("o Processamento de notas Recebidas ainda esta sendo feito Manualmente")

@app.route('/troca_unidade', methods = ['GET','POST'])
def troca_unidade():
    return ("a Troca de Unidade ainda esta sendo feito Manualmente")

@app.route('/rastreabilidade', methods = ['GET','POST'])
def rastreabilidade():
    op_rastreio = request.form.get('op_rastreio')
    consulta = Lote_visual.query.filter_by(referencia = op_rastreio).all()
    consulta_geral = Lote_visual.query.filter_by().all()

    return render_template('rastreabilidade.html',op_rastreio = op_rastreio, consulta = consulta, consulta_geral = consulta_geral )

@app.route('/op_cards', methods=['GET', 'POST'])
def op_cards():
    LoteVisualAlias = aliased(Lote_visual)
    
    # Consulta para somar as quantidades por código
    subquery = db.session.query(
        LoteVisualAlias.item,
        func.sum(LoteVisualAlias.quantidade).label('estoque')
    ).group_by(LoteVisualAlias.item).subquery()

    # Consulta para juntar os pedidos com as somas das quantidades de estoque
    pedidos = db.session.query(
        Pedido,
        subquery.c.estoque
    ).outerjoin(
        subquery, Pedido.codigo == subquery.c.item
    ).filter(
        Pedido.status2 == "Emitido"
    ).all()

    # Convertendo o resultado da consulta para adicionar o campo 'estoque' em cada pedido
    pedidos_com_estoque = []
    for pedido, estoque in pedidos:
        estoque = float(estoque/1000) if estoque is not None else 0.0
        pedido.estoque = estoque if estoque is not None else 0
        pedidos_com_estoque.append(pedido)

    return render_template('op_cards.html', pedidos=pedidos_com_estoque)

@app.route('/op_cards_teste', methods=['GET', 'POST'])
def op_cards_teste():
    LoteVisualAlias = aliased(Lote_visual)
    
    # Consulta para somar as quantidades por código
    subquery = db.session.query(
        LoteVisualAlias.item,
        func.sum(LoteVisualAlias.quantidade).label('estoque')
    ).group_by(LoteVisualAlias.item).subquery()

    # Consulta para juntar os pedidos com as somas das quantidades de estoque
    pedidos = db.session.query(
        Pedido,
        subquery.c.estoque
    ).outerjoin(
        subquery, Pedido.codigo == subquery.c.item
    ).filter(
        Pedido.status2 == "Emitido"
    ).all()

    # Convertendo o resultado da consulta para adicionar o campo 'estoque' em cada pedido
    pedidos_com_estoque = []
    for pedido, estoque in pedidos:
        estoque = float(estoque/1000) if estoque is not None else 0.0
        pedido.estoque = estoque if estoque is not None else 0
        pedidos_com_estoque.append(pedido)

    return render_template('op_cards_teste.html', pedidos=pedidos_com_estoque)

@app.route('/atualizar_status_pedido', methods=['POST'])
def atualizar_status_pedido():
    data = request.get_json()
    pedido = Pedido.query.get(data['pedidoId'])
    if pedido:
        pedido.Status = data['novoStatus']
        db.session.commit()
        return jsonify({'message': 'Status atualizado com sucesso!'}), 200
    else:
        return jsonify({'error': 'Pedido não encontrado'}), 404
    
@app.route('/add_pedido', methods=['POST'])
def add_pedido():
    if request.method == 'POST':
        pedido = request.form.get('pedido')
        descricao = request.form.get('descricao')
        cliente = request.form.get('cliente')
        codigo = request.form.get('codigo')
        data_entrega = request.form.get('data_entrega')
        obs_entrega = request.form.get('obs_entrega')
        dimensional = request.form.get('dimensional')
        quantidade = float(request.form.get('quantidade'))
        canto = request.form.get('canto')
        furo = request.form.get('furo')
        embalagem = request.form.get('embalagem')
        obs = request.form.get('obs')
        date = datahora("data")
        status_text = "Emitido"

        try:
            novo_pedido = Pedido(pedido=pedido,
            emissao=date,
            descricao=descricao,
            cliente=cliente,
            codigo=codigo,
            data_entrega=data_entrega,
            obs_entrega=obs_entrega,
            dimensional=dimensional,
            quantidade=quantidade,
            peso=0,
            peso_total=0,
            Status=status_text,
            material="",
            peso_material=0,
            amarrados=0,
            dimencional_real="",
            obs=obs,
            canto=canto,
            furo=furo,
            embalagem=embalagem,
            status2=status_text,
            qtd_faturada=0,
            packlist=0)

            db.session.add(novo_pedido)

            db.session.commit()
            flash('Pedido adicionado com sucesso!', 'success')
            #return jsonify({"success": True, "message": "Pedido adicionado com sucesso!"}), 200
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar pedido: {e}', 'danger')
            return jsonify({"success": False, "message": str(e)}), 500
            
        
    return redirect(url_for('pedidos'))

@app.route('/deletar_pedido', methods=['POST'])
def deletar_pedido():
    data = request.get_json()
    pedido_id = data.get('id')
    
    pedido = Pedido.query.get(pedido_id)
    if pedido:
        db.session.delete(pedido)
        try:
            db.session.commit()
            return jsonify(success=True)
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, message=str(e))
    return jsonify(success=False, message="Pedido não encontrado.")


@app.route('/ferramentas', methods=['GET', 'POST'])
def ferramentas():
    filtro_cod = request.form.get("filtro_cod", "").upper()
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)

    query = Ferramentas.query.order_by(Ferramentas.id.desc())

    if filtro_cod:
        query = query.filter(Ferramentas.dimensional.ilike(f"%{filtro_cod}%"))
    
    ferramentas = query.paginate(page=page, per_page=10)

    return render_template('Ferramentas.html', ferramentas=ferramentas)

@app.route('/estoque_cobre', methods=['GET', 'POST'])
def estoque_cobre():
    page = request.args.get('page', 1, type=int)
    filtro_cod = request.form.get('filtro_cod', '').upper()
    filtro_desc = request.form.get('filtro_desc', '').upper()

    if filtro_cod == "":
        filtro_cod = None

    if filtro_desc == "":
        filtro_desc = None

    query = Lote_visual.query.order_by(Lote_visual.id.desc()).filter_by(tipo="Setor_Cobre").filter(Lote_visual.quantidade > 0)

    if filtro_cod:
        query = query.filter_by(item=filtro_cod)

    cobre = query.paginate(page=page, per_page=10)

    for lote in cobre.items:
        desc = Def_cadastro_prod(lote.item)
        descricao = desc[5] if len(desc) > 5 else 'N/A'
        lote.descricao = descricao  # Adiciona a descrição ao lote

    if filtro_desc:
        # Filtra os itens já paginados com base na descrição
        cobre.items = [lote for lote in cobre.items if filtro_desc in lote.descricao.upper()]

    return render_template('Estoque_Cobre.html', cobre=cobre)



@app.route('/deletar_estoque_cobre', methods=['POST'])
def deletar_estoque_cobre():
    data = request.get_json()
    item_id = data.get('id')
    
    if not item_id:
        return jsonify({"success": False, "message": "ID do item não fornecido."}), 400

    try:
        item = Lote_visual.query.get(item_id)
        
        if not item:
            return jsonify({"success": False, "message": "Item não encontrado."}), 404

        db.session.delete(item)
        db.session.commit()
        
        Status_mov = Def_ajuste_estoque(item.item, item.quantidade,"SAI", "4084861665", item.referencia, "Visual", item.peso, "Cobre", 0,"Não","Kels")
        


        return jsonify({"success": True, "message": "Item excluído com sucesso."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao excluir item: {str(e)}"}), 500



@app.route('/pedidos', methods = ['GET','POST'])
def pedidos():

    #pedidos = Pedido.query.filter_by(status2 = "Emitido").all()
    
    filtro_pd = request.form.get("filtro_pd")
    filtro_cod = request.form.get("filtro_cod")
    
    if not current_user.is_authenticated:
     return redirect( url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    
    if filtro_pd == "":
        filtro_pd = None
    
    if filtro_cod == "":
        filtro_cod = None


    if filtro_pd != None:
        pedidos = Pedido.query.order_by(Pedido.pedido.desc()).filter_by(status2 = "Emitido", pedido = filtro_pd).paginate(page=page,per_page=10)
    else:
        if filtro_cod != None:
            pedidos = Pedido.query.order_by(Pedido.pedido.desc()).filter_by(status2 = "Emitido", codigo = filtro_cod).paginate(page=page,per_page=10)
        else:
            pedidos = Pedido.query.order_by(Pedido.pedido.desc()).filter_by(status2 = "Emitido").paginate(page=page,per_page=10)
    


    #pedidos = pedidos.query.filter_by(status2 = "Emitido").all()
        



    return render_template('pedidos.html',pedidos = pedidos)

@app.route('/get_pedido/<int:id>', methods=['GET'])
def get_pedido(id):
    pedido = Pedido.query.get(id)
    if pedido:
        return jsonify({
            'id': pedido.id,
            'pedido': pedido.pedido,
            'descricao': pedido.descricao,
            'cliente': pedido.cliente,
            'codigo': pedido.codigo,
            'data_entrega': pedido.data_entrega,
            'obs_entrega': pedido.obs_entrega,
            'dimensional': pedido.dimensional,
            'quantidade': pedido.quantidade,
            'canto': pedido.canto,
            'furo': pedido.furo,
            'embalagem': pedido.embalagem
        })
    return jsonify({'error': 'Pedido não encontrado'}), 404

@app.route('/alterar_pedido', methods=['POST'])
def alterar_pedido():
    data = request.form
    pedido_id = data.get('id')
    pedido = Pedido.query.get(pedido_id)
    
    if not pedido:
        return jsonify({'error': 'Pedido não encontrado'}), 404
    
    pedido.pedido = data.get('pedido')
    pedido.descricao = data.get('descricao')
    pedido.cliente = data.get('cliente')
    pedido.codigo = data.get('codigo')
    pedido.data_entrega = data.get('data_entrega')
    pedido.obs_entrega = data.get('obs_entrega')
    pedido.dimensional = data.get('dimensional')
    pedido.quantidade = data.get('quantidade')
    pedido.canto = data.get('canto')
    pedido.furo = data.get('furo')
    pedido.embalagem = data.get('embalagem')
    
    db.session.commit()
    flash('Pedido alterado com sucesso!', 'success')
    return redirect(url_for('pedidos'))


from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

@app.route('/pedidos_faturados', methods=['GET', 'POST'])
def pedidos_faturados():
    filtro_pd = request.form.get("filtro_pd")
    filtro_cod = request.form.get("filtro_cod")
    filtro_data_inicio = request.form.get("filtro_data_inicio")
    filtro_data_fim = request.form.get("filtro_data_fim")

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    tqtd = 0

    query = Pedido.query.order_by(Pedido.pedido.desc()).filter_by(status2="Faturado")

    if filtro_pd:
        query = query.filter(Pedido.pedido == filtro_pd)
    if filtro_cod:
        query = query.filter(Pedido.codigo == filtro_cod)
    if filtro_data_inicio and filtro_data_fim:
        try:
            data_inicio = datetime.strptime(filtro_data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(filtro_data_fim, '%Y-%m-%d')
            query = query.filter(Pedido.data_entrega.between(data_inicio.strftime('%d/%m/%y'), data_fim.strftime('%d/%m/%y')))
        except ValueError:
            flash('Formato de data inválido. Use o formato AAAA-MM-DD.', 'danger')

    pedidos = query.paginate(page=page, per_page=10)

    for row in pedidos.items:
        tqtd += row.quantidade

    tqtd = int(tqtd)

    return render_template('pedidos_faturados.html', pedidos=pedidos, tqtd=tqtd)

@app.route('/packlist', methods=['GET', 'POST'])
@login_required
def packlist():
    if request.method == 'POST':
        data = request.get_json()
        pedidos_ids = data['pedidos_ids']
        peso_liquido_total = sum([Pedido.query.get(pid).peso for pid in pedidos_ids])
        peso_bruto_total = sum([Pedido.query.get(pid).peso_total for pid in pedidos_ids])
        embalagem_total = sum([Pedido.query.get(pid).amarrados for pid in pedidos_ids])

        novo_packlist = Packlist(
            peso_liquido=peso_liquido_total,
            peso_bruto=peso_bruto_total,
            embalagem=embalagem_total,
            obs_entrega='',
            obs='',
            status='Emitido'
        )
        db.session.add(novo_packlist)
        db.session.commit()

        for pid in pedidos_ids:
            pedido = Pedido.query.get(pid)
            pedido.packlist = novo_packlist.packlist_id

        db.session.commit()
        return jsonify({'status': 'success', 'packlist_id': novo_packlist.packlist_id})

    packlists = Packlist.query.all()
    return render_template('packlist.html', packlists=packlists)


@app.route('/criar_packlist', methods=['POST'])
@login_required
def criar_packlist():
    data = request.json
    pedidos = data['pedidos']
    total_amarrados = data['total_amarrados']
    total_peso = data['total_peso']
    total_peso_bruto = data['total_peso_bruto']
    obs_entrega = data.get('obs_entrega')
    obs = data.get('obs')

    novo_packlist = Packlist(
        peso_liquido=total_peso,
        peso_bruto=total_peso_bruto,
        embalagem=total_amarrados,
        obs_entrega=obs_entrega,
        obs=obs
    )

    db.session.add(novo_packlist)
    db.session.commit()

    for pedido_id in pedidos:
        pedido = Pedido.query.get(pedido_id)
        pedido.packlist = novo_packlist.packlist
        db.session.commit()

    return jsonify({'message': 'Packing List criado com sucesso!'})




@app.route('/add_ferramentas', methods=['POST'])
def add_ferramentas():
    if not current_user.is_authenticated:
        flash('Você precisa estar logado para adicionar uma ferramenta.', 'danger')
        return redirect(url_for('login'))
    
    dimensional = request.form.get('dimensional')
    quantidade = request.form.get('quantidade')
    obs = request.form.get('obs')
    
    nova_ferramenta = Ferramentas(dimensional, quantidade, obs)
    
    try:
        db.session.add(nova_ferramenta)
        db.session.commit()
        flash('Ferramenta adicionada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar ferramenta: {str(e)}', 'danger')
    
    return redirect(url_for('ferramentas'))


@app.route('/deletar_ferramenta/<int:id>', methods=['POST'])
def deletar_ferramenta(id):
    if not current_user.is_authenticated:
        flash('Você precisa estar logado para deletar uma ferramenta.', 'danger')
        return redirect(url_for('login'))
    
    ferramenta = Ferramentas.query.get_or_404(id)
    
    try:
        db.session.delete(ferramenta)
        db.session.commit()
        flash('Ferramenta deletada com sucesso!', 'success')
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar ferramenta: {str(e)}', 'danger')
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/faturar_pedido', methods = ['GET','POST'])
def faturar_pedido():
    

    data = request.get_json()
    pedido_id = data.get('pedidoId')
    faturado_omie = data.get('faturado_omie')
    peso_faturado = data.get('peso_faturado')

    qtd_visual = peso_faturado
    qtd_visual = int(qtd_visual)
    qtd_visual = qtd_visual * 1000
    operador = "Valdemir"
    pedido = Pedido.query.get(pedido_id)



    
    if faturado_omie == True:
        print("faturado Omie")
        Status_mov = Def_ajuste_estoque(pedido.codigo, qtd_visual,"SAI", "4084861665", pedido.pedido, "Visual", pedido.peso, "Cobre", 0,"Não", operador)
        
        id_lote = Lote_visual.query.filter_by(item = pedido.codigo, tipo = "Setor_Cobre").all()
        
        for loop in id_lote:
            zerar_lote = Lote_visual.query.get(loop.id)
        
        qtd_visual = qtd_visual
        zerar_lote.quantidade = zerar_lote.quantidade - qtd_visual
        db.session.commit()



    else:
        print("Faturado Direto")
        Status_mov = Def_ajuste_estoque(pedido.codigo, qtd_visual,"SAI", "4084861665", pedido.pedido, "Visual", pedido.peso, "Cobre", 0,"Não", operador)
        
        id_lote = Lote_visual.query.filter_by(item = pedido.codigo, tipo = "Setor_Cobre").all()
        
        for loop in id_lote:
            zerar_lote = Lote_visual.query.get(loop.id)
        
        qtd_visual = qtd_visual
        zerar_lote.quantidade = zerar_lote.quantidade - qtd_visual
        db.session.commit()




    if pedido:
        
        

        pedido.Status = "Faturado"
        pedido.status2 = "Faturado"
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Pedido atualizado com sucesso!'})

    else:
        return jsonify({'status': 'error', 'message': 'Pedido não encontrado'})


@app.route('/add_saldo_cobre', methods=['POST'])
def add_saldo_cobre():
    data = request.get_json()
    codigo = data.get('codigo')
    quantidade = data.get('quantidade')
    referencia = data.get('referencia')
    operador = "Valdemir"
    #date = datahora("data") 


    try:
        Def_ajuste_estoque(codigo, quantidade,"ENT", "4084861665", referencia, "Setor_Cobre", quantidade, "Cobre", 0,"Não", operador)




        return jsonify({"success": True, "message": "Saldo adicionado com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500



@app.route('/update_pedido', methods = ['GET','POST'])
def update_pedido():
    #if not current_user.is_authenticated:
    #    return redirect( url_for('login'))
    
    print("teste1")
    data = request.get_json()  # Obter dados como JSON
    pedido_id = data['pedidoId']
    edit_item = Pedido.query.get(pedido_id)
    operador = "Valdemir"
 
    if edit_item:
        print("teste2")
        qtd_visual = data['data']['peso']
        qtd_visual = int(qtd_visual)
        qtd_visual = qtd_visual * 1000
        if edit_item.peso == "" or edit_item.peso == None:
            Status_mov = Def_ajuste_estoque(edit_item.codigo, qtd_visual,"ENT", "4084861665", edit_item.pedido, "Setor_Cobre", data['data']['peso'], "Cobre", 0,"Não")
            print(Status_mov, qtd_visual)
            Status_mov2 = Def_ajuste_estoque(data['data']['material'], data['data']['peso_material'],"SAI", "4084861665", edit_item.pedido, "Setor_Cobre", data['data']['peso_material'], "Cobre", 0,"Não", operador)
            print(Status_mov2, data['data']['peso_material'])
        print(edit_item.peso)

        id_lote = Lote_visual.query.filter_by(item = data['data']['material'], tipo = "Setor_Cobre").all()
        
        for loop in id_lote:
            zerar_lote = Lote_visual.query.get(loop.id)
        
        qtd_visual = data['data']['peso_material']
        zerar_lote.quantidade = zerar_lote.quantidade - qtd_visual
        db.session.commit()





        if data['data']['obs'] == "":
            observ="-"
        else:
            observ=data['data']['obs']

        if data['data']['dimencional_real'] =="":
            dimen = "-"
        else:
            dimen = data['data']['dimencional_real']    




        edit_item.peso = float(data['data']['peso'])
        edit_item.peso_total = float(data['data']['peso_total'])
        edit_item.material = data['data']['material']
        edit_item.peso_material = float(data['data']['peso_material'])
        edit_item.amarrados = data['data']['amarrados']
        edit_item.dimencional_real = dimen 
        edit_item.Status = "Qualidade"
        edit_item.obs = observ   # Certifique-se de que a chave 'obs' está correta no JSON

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Pedido atualizado com sucesso!'})
    
    

    return jsonify({'status': 'error', 'message': 'Pedido não encontrado'})

#----------------------gerar PDF pdf---------------------------------
@app.route('/imprimir_op', methods = ['GET','POST'])
def imprimir_op():
    print("imprimindo pdf...")

    op = request.form.get('referencia')
    mov_op = Estrutura_op.query.filter_by(op_referencia = op).all()
    op_info = Ops_visual.query.filter_by(numero_op_visual = op).all()
   
    filename = os.path.join(
            os.getcwd(),
            "static",
            "images","logo-iso.png")
    
 
    try:
        nome_pdf = "OrdemProdução"
        pdf = canvas.Canvas('{}.pdf'.format(nome_pdf))
        pdf.setTitle(nome_pdf)
        pdf.line(x1=20,y1=800,x2=550,y2=800)
        pdf.line(x1=186,y1=800,x2=186,y2=750)# vertical
        pdf.line(x1=395,y1=800,x2=395,y2=750)# vertical
        pdf.line(x1=20,y1=800,x2=20,y2=750)# vertical
        pdf.line(x1=550,y1=800,x2=550,y2=750)# vertical
        
        
        pdf.line(x1=20,y1=750,x2=550,y2=750)
        pdf.line(x1=20,y1=725,x2=550,y2=725)
        pdf.line(x1=20,y1=725,x2=20,y2=600)# vertical
        pdf.line(x1=186,y1=725,x2=186,y2=625)# vertical
        pdf.line(x1=395,y1=725,x2=395,y2=700)# vertical
        pdf.line(x1=395,y1=650,x2=395,y2=625)# vertical
        pdf.line(x1=550,y1=725,x2=550,y2=600)# vertical
        pdf.line(x1=20,y1=700,x2=550,y2=700)
        pdf.line(x1=20,y1=675,x2=550,y2=675)
        pdf.line(x1=20,y1=650,x2=550,y2=650)
        pdf.line(x1=20,y1=625,x2=550,y2=625)
        pdf.line(x1=20,y1=600,x2=550,y2=600)
        pdf.line(x1=20,y1=575,x2=20,y2=475)# vertical
        pdf.line(x1=130,y1=550,x2=130,y2=475)# vertical
        pdf.line(x1=186,y1=550,x2=186,y2=475)# vertical
        pdf.line(x1=310,y1=550,x2=310,y2=475)# vertical
        pdf.line(x1=430,y1=550,x2=430,y2=475)# vertical
        pdf.line(x1=550,y1=575,x2=550,y2=475)# vertical
        pdf.line(x1=20,y1=575,x2=550,y2=575)
        pdf.line(x1=20,y1=550,x2=550,y2=550)
        pdf.line(x1=20,y1=525,x2=550,y2=525)
        pdf.line(x1=20,y1=500,x2=550,y2=500)
        pdf.line(x1=20,y1=475,x2=550,y2=475)
        pdf.line(x1=20,y1=450,x2=550,y2=450)
        pdf.line(x1=20,y1=425,x2=550,y2=425)




        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(205,753, 'Ordem de Produção')
        pdf.drawImage(filename, x=25, y=749, width=150,height=42, mask='auto')
        pdf.setFont("Helvetica-Oblique", 7)
        pdf.drawString(475,10, 'Formulario: Ref.:OP003 01-02-2024')
        for info in op_info:
            cadastro = Def_cadastro_prod(info.item)
            pdf.setFont("Helvetica-Bold", 15)
            pdf.drawString(410,778,'{}'.format('Numero da Ordem'))
            pdf.drawString(450,758,'{}'.format(info.numero_op_visual))
            
            pdf.setFont("Helvetica-Oblique", 12)
            pdf.drawString(23,703,'{} : {}'.format('Pedido de Venda',info.piv))
            pdf.drawString(205,703,'{} : {}'.format('Setor',info.setor))
            pdf.drawString(410,703,'{} : {}'.format('Operador',info.operador))

            pdf.setFont("Helvetica-Oblique", 15)
            pdf.drawString(23,678,'{} : {}'.format('Item',info.item))
            pdf.setFont("Helvetica-Oblique", 8)
            pdf.drawString(205,678,'{} : {}'.format('Descrição',cadastro[5]))
            pdf.setFont("Helvetica-Oblique", 12)
            pdf.drawString(23,653,'{} : {}'.format('Liga Princial',cadastro[9]))
            pdf.drawString(205,653,'{} : {}'.format('Cliente',cadastro[7]))

            pdf.drawString(23,628,'{} : {}'.format('Codigo Cliente',cadastro[8]))
            pdf.drawString(205,628,'{} : {}'.format('Status',info.situação))
            pdf.drawString(410,628,'{} : {}'.format('Data',info.data_abertura))

            pdf.drawString(23,603,'{} : {}'.format('Descrição da Ordem ',info.descrição))

            pdf.setFont("Helvetica-Bold", 15)
            pdf.drawString(190,553, 'Totais da Ordem de Produção')

            pdf.setFont("Helvetica-Oblique", 12)

            pdf.drawString(23,528, 'Quantidades')
            
            pdf.drawString(205,528, 'Enviado')
            pdf.drawString(335,528, 'Retornado')
            pdf.drawString(450,528, 'Saldo')

            pdf.drawString(23,503,'{} : {}'.format('Estimada',info.quantidade))    
            pdf.drawString(23,478,'{} : {}'.format('Qtd. real',info.quantidade_real))
            pdf.drawString(140,503, 'Peso')
            pdf.drawString(140,478, 'Fino')
            
            pdf.drawString(205,503,'{}'.format(info.peso_enviado))
            pdf.drawString(205,478,'{}'.format(info.fino_enviado))
            pdf.drawString(335,503,'{}'.format(info.peso_retornado))
            pdf.drawString(335,478,'{}'.format(info.fino_retornado))
            pdf.drawString(450,503,'{}'.format(info.peso_enviado - info.peso_retornado))
            pdf.drawString(450,478,'{}'.format(info.fino_enviado - info.fino_retornado))




        pdf.drawString(23,428, 'Movimento')
        pdf.drawString(138,428, 'Código')
        pdf.drawString(253,428, 'Quantidade')
        pdf.drawString(358,428, 'Peso')
        pdf.drawString(463,428, 'Fino')


        

        y = 425
        x = 428 
        for mov in mov_op:
            x -= 25
            y -= 25
            pdf.drawString(23,x,'{}'.format(mov.tipo_mov))
            pdf.drawString(138,x,'{}'.format(mov.item_estrutura))
            pdf.drawString(253,x,'{}'.format(mov.quantidade_item))
            pdf.drawString(358,x,'{}'.format(mov.peso))
            pdf.drawString(463,x,'{}'.format(mov.fino))
            pdf.line(x1=20,y1=y,x2=550,y2=y)

        pdf.line(x1=20,y1=450,x2=20,y2=y)# vertical
        pdf.line(x1=135,y1=450,x2=135,y2=y)# vertical
        pdf.line(x1=250,y1=450,x2=250,y2=y)# vertical
        pdf.line(x1=355,y1=450,x2=355,y2=y)# vertical
        pdf.line(x1=460,y1=450,x2=460,y2=y)# vertical
        pdf.line(x1=550,y1=450,x2=550,y2=y)# vertical
        
        pdf.save()
        print('{}.pdf criado com sucesso!'.format(nome_pdf))
        
            

    except:
        print('Erro ao gerar {}.pdf'.format(nome_pdf))
    
    #workingdir = os.path.abspath(os.getcwd())
    #filepath = 'C:/temp/'
    filepath = ''
    #return send_from_directory(filepath, "OrdemProdução_"  + op + ".pdf")
    print(filepath, "OrdemProdução.pdf")
    return send_from_directory(filepath, "OrdemProdução.pdf")
#===================Fim de todas modificações de diego ==================#

#===================Todas definições do diego prodx==================#  


@app.route('/exportar_ferramentas')
def exportar_ferramentas():
    try:
        ferramentas = Ferramentas.query.all()
        
        data = {
            "Dimensional": [ferramenta.dimensional for ferramenta in ferramentas],
            "Quantidade": [ferramenta.quantidade for ferramenta in ferramentas],
            "Obs": [ferramenta.obs for ferramenta in ferramentas]
        }
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ferramentas')
            
            workbook  = writer.book
            worksheet = writer.sheets['Ferramentas']
            
            # Formatação para a primeira linha (header)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            # Formatação para as células de dados
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })
            
            # Aplica a formatação na primeira linha
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ajusta a largura das colunas
                worksheet.set_column(col_num, col_num, 20)
            
            # Aplica a formatação nas células de dados
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)
        
        return send_file(output, download_name='Ferramentas.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500    

@app.route('/exportar_estoque_excel')
def exportar_estoque_excel():
    try:
        estoque = Lote_visual.query.filter(Lote_visual.tipo == 'Setor_Cobre', Lote_visual.quantidade > 0).all()

        data = {
            "Item": [item.item for item in estoque],
            "Descrição": [Def_cadastro_prod(item.item)[5] for item in estoque],
            "Lote": [item.numero_lote for item in estoque],
            "Peso": [item.quantidade / 1000 for item in estoque],
            "Unid": ['KG' for item in estoque]
        }
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Estoque de Cobre')
            
            workbook  = writer.book
            worksheet = writer.sheets['Estoque de Cobre']
            
            # Formatação para a primeira linha (header)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            # Formatação para as células de dados
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })
            
            # Formatação para a segunda coluna (Descrição)
            descricao_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'left'
            })
            
            # Formatação para a quarta coluna (Peso) com 3 casas decimais
            peso_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center',
                'num_format': '0.000'
            })
            
            # Aplica a formatação na primeira linha
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ajusta a largura das colunas
                if col_num == 1:
                    worksheet.set_column(col_num, col_num, 60)
                else:
                    worksheet.set_column(col_num, col_num, 18)
            
            # Aplica a formatação nas células de dados
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    if col_num == 1:
                        worksheet.write(row_num, col_num, cell_data, descricao_format)
                    elif col_num == 3:
                        worksheet.write(row_num, col_num, cell_data, peso_format)
                    else:
                        worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)
        
        return send_file(output, download_name='Estoque_Cobre.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    

@app.route('/exportar_pedidos_excel')
def exportar_pedidos_excel():
    try:
        #pedidos = Pedido.query.all()
        pedidos = Pedido.query.filter_by(status2 = "Emitido").all()
        data = {
            "Pedido": [pedido.pedido for pedido in pedidos],
            "Status": [pedido.Status for pedido in pedidos],
            "Data Emissão": [pedido.emissao for pedido in pedidos],
            "Cliente": [pedido.cliente for pedido in pedidos],
            "Código Cliente": ["-" for pedido in pedidos],
            "Código": [pedido.codigo for pedido in pedidos],
            "Data Entrega": [pedido.data_entrega for pedido in pedidos],
            "Obs Entrega": [pedido.obs_entrega for pedido in pedidos],
            "Liga": ["Cobre" for pedido in pedidos],
            "Canto": [pedido.canto for pedido in pedidos],
            "Furo": [pedido.furo for pedido in pedidos],
            "Embalagem": [pedido.embalagem for pedido in pedidos],
            "Dimensional": [pedido.dimensional for pedido in pedidos],
            "Quantidade": [pedido.quantidade for pedido in pedidos],
            "Um": ["KG" for pedido in pedidos],
            "Descrição": [pedido.descricao for pedido in pedidos],
            "Observações": [pedido.obs for pedido in pedidos]
        }
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PedidosPendentes')
            
            workbook  = writer.book
            worksheet = writer.sheets['PedidosPendentes']
            
            # Formatação para a primeira linha (header)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            # Formatação para as células de dados
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })
            
            # Aplica a formatação na primeira linha
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ajusta a largura das colunas
                worksheet.set_column(col_num, col_num, 20)
            
            # Aplica a formatação nas células de dados
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)
        
        return send_file(output, download_name='PedidosPendentes.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/exportar_pedidos_faturados_excel')
def exportar_pedidos_faturados_excel():
    try:
        #pedidos = Pedido.query.all()
        pedidos = Pedido.query.filter_by(status2 = "Faturado").all()
        data = {
            "Pedido": [pedido.pedido for pedido in pedidos],
            "Status": [pedido.Status for pedido in pedidos],
            "Data Emissão": [pedido.emissao for pedido in pedidos],
            "Cliente": [pedido.cliente for pedido in pedidos],
            "Código Cliente": ["-" for pedido in pedidos],
            "Código": [pedido.codigo for pedido in pedidos],
            "Data Entrega": [pedido.data_entrega for pedido in pedidos],
            "Obs Entrega": [pedido.obs_entrega for pedido in pedidos],
            "Liga": ["Cobre" for pedido in pedidos],
            "Canto": [pedido.canto for pedido in pedidos],
            "Furo": [pedido.furo for pedido in pedidos],
            "Embalagem": [pedido.embalagem for pedido in pedidos],
            "Dimensional": [pedido.dimensional for pedido in pedidos],
            "Quantidade": [pedido.quantidade for pedido in pedidos],
            "Um": ["KG" for pedido in pedidos],
            "Descrição": [pedido.descricao for pedido in pedidos],
            "Observações": [pedido.obs for pedido in pedidos]
        }
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PedidosFaturados')
            
            workbook  = writer.book
            worksheet = writer.sheets['PedidosFaturados']
            
            # Formatação para a primeira linha (header)
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            # Formatação para as células de dados
            cell_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top',
                'border': 1,
                'align': 'center'
            })
            
            # Aplica a formatação na primeira linha
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Ajusta a largura das colunas
                worksheet.set_column(col_num, col_num, 20)
            
            # Aplica a formatação nas células de dados
            for row_num, row_data in enumerate(df.values, 1):
                for col_num, cell_data in enumerate(row_data):
                    worksheet.write(row_num, col_num, cell_data, cell_format)

        output.seek(0)
        
        return send_file(output, download_name='PedidosFaturados.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500





@app.route('/backup_restore')
@login_required
def backup_restore():
    return render_template('backup_restore.html')




def modify_sql_content(sql_content):
    lines = sql_content.splitlines()
    modified_lines = []
    for line in lines:
        if line.startswith("CREATE TABLE"):
            line = line.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
        if line.startswith("INSERT INTO"):
            line = line.replace("INSERT INTO", "INSERT IGNORE INTO")
        modified_lines.append(line)
    return "\n".join(modified_lines)

def format_value(value):
    if isinstance(value, str):
        return f"'{value.replace(';', ' ').replace("'", " ")}'"
    elif value is None:
        return 'NULL'
    elif isinstance(value, float):
        return f"{value:.3f}"
    return str(value)

@app.route('/backup_banco', methods=['GET'])
def backup_banco():
    try:
        db_url = app.config['URL_MYSQL']
        url = make_url(db_url)
        db_name = url.database
        user = url.username
        password = url.password
        host = url.host
        port = url.port or 3306

        connection = pymysql.connect(host=host, user=user, password=password, database=db_name, port=port)
        backup_file = io.BytesIO()
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table_statement = cursor.fetchone()[1] + ";\n"
            backup_file.write(create_table_statement.encode('utf-8'))

            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            for row in rows:
                formatted_values = ", ".join(format_value(value) for value in row)
                insert_statement = f"INSERT IGNORE INTO {table_name} VALUES ({formatted_values});\n"
                backup_file.write(insert_statement.encode('utf-8'))

        connection.close()
        backup_file.seek(0)
        modified_content = modify_sql_content(backup_file.getvalue().decode('utf-8'))

        backup_file = io.BytesIO()
        backup_file.write(modified_content.encode('utf-8'))
        backup_file.seek(0)

        return send_file(backup_file, as_attachment=True, download_name='backup.sql', mimetype='application/sql')
    except Exception as e:
        return f"Erro ao fazer o backup do banco de dados: {str(e)}", 500

@app.route('/restaurar_banco', methods=['POST'])
def restaurar_banco():
    banco = request.form.get("banco")
    if banco == "Banco Backup":
        caminhobanco = 'URL_MYSQL_novo'
    else:
        caminhobanco = 'URL_MYSQL'

    try:
        file = request.files['file']
        if not file or not file.filename.endswith('.sql'):
            flash('Arquivo inválido! Por favor, envie um arquivo .sql.', 'danger')
            return redirect(url_for('backup_restore'))

        db_url = os.getenv(caminhobanco)
        if not db_url:
            raise ValueError("URL_MYSQL não está configurada.")
        
        url = make_url(db_url)
        db_name = url.database
        user = url.username
        password = url.password
        host = url.host
        port = url.port or 3306

        connection = pymysql.connect(host=host, user=user, password=password, database=db_name, port=port)
        cursor = connection.cursor()

        sql_content = file.read().decode('utf-8')
        sql_statements = sql_content.split(';')

        for statement in sql_statements:
            if statement.strip():
                cursor.execute(statement)

        connection.commit()
        connection.close()

        flash('Banco de dados restaurado com sucesso!', 'success')
        return redirect(url_for('backup_restore'))
    except pymysql.MySQLError as e:
        return f"Erro ao restaurar o banco de dados: MySQL Error: {str(e)}", 500
    except Exception as e:
        return f"Erro ao restaurar o banco de dados: {str(e)}", 500




def Def_cadastro_prod(item):
   
   item = item
   if item == None:
        item = "CBA-4000"
   cadastros = Cadastro_itens.query.filter_by(item = item)
   for cadastro in cadastros:
       
        tipo = cadastro.uso
        unidade = cadastro.unidade
        id_produto = cadastro.id_produto
        valor_unitario = cadastro.valor_unitario
        descricao = cadastro.descricao
        cliente = cadastro.cliente
        codigo_cliente = cadastro.codigo_cliente
        liga = cadastro.material
        familia = cadastro.familia
        um_visual = cadastro.um_visual
        ncm = cadastro.ncm
        setor = cadastro.setor

        
   if id_produto == None:
        id_produto = "-"
   if tipo == None:
        tipo = "-"
   if unidade == None:
       unidade = "-"
   if descricao == None:
       descricao = "-"
   if cliente == None:
       cliente = "-"
   if liga == None:
        liga = "-"
   imagens = "-"
           #id_produto=0, tipo=1, imagens=2, unidade=3, valor_unitario=4, descricao=5, item=6, cliente=7, codigo_cliente=8, liga=9, ncm=10, familia=11, um_visual=12, setor=13  
   return [id_produto, tipo, imagens, unidade, valor_unitario, descricao, item, cliente, codigo_cliente, liga, ncm, familia, um_visual, setor]


def Def_cadastro_prod2(item):
   item = item

    #item = Lote_visual.query.get(item_id)
   data = {
                "call":"ConsultarProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                    "codigo": item
                        }
                ]}
   response = requests.post(url=url_produtos, json=data)
   cadastro = response.json()
    
   tipo = cadastro.get('tipoItem')
   if tipo == None:
       tipo = "-"
   else:

      if (tipo == "00") or (tipo == "01") or (tipo == "03") or (tipo == "04") or (tipo == "05") or (tipo == "06"):
        tipo = "Produtivo"
      else:
        tipo = "Não Produtivo"      
   
   unidade = cadastro.get('unidade')
   if unidade == None:
       unidade = "-"

   id_produto = cadastro.get('codigo_produto')
   if id_produto == None:
       id_produto = 0

   valor_unitario = cadastro.get('valor_unitario')
   if valor_unitario == None:
       valor_unitario = 0

   descricao = cadastro.get('descricao')
   if descricao == None:
       descricao = "-"
   item = cadastro.get('codigo')
   if item == None:
       item = "-"
    
   cliente = cadastro.get('marca')
   if cliente == None:
       cliente = "-"
   
   codigo_cliente = cadastro.get('obs_internas')
   if codigo_cliente == None:
       codigo_cliente = "-"
   
   liga = cadastro.get('modelo')
   if liga == None:
       liga = "-"
   
   imagens = cadastro.get('imagens')
   if imagens == None:
       imagens = "-"
   
   ncm = cadastro.get('ncm')
   if imagens == None:
       imagens = "-"
   
   return [id_produto, tipo, imagens, unidade, valor_unitario, descricao, item, cliente, codigo_cliente, liga, ncm]

def Def_consulta_estoque(id_produto, local):
    
   data = {
                "call":"PosicaoEstoque",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                      "codigo_local_estoque": local,
                      "id_prod": id_produto
                        }
                ]}
   response = requests.post(url=url_consulta_estoque, json=data)
   cadastro_saldo = response.json()

   saldoFisico = cadastro_saldo.get('saldo')
   if saldoFisico == None:
       saldoFisico = 0

    
   return saldoFisico   
#===================definição de ajuste de estoque ==================#

def Def_ajuste_estoque(item, quan, tipomov, local, referencia, tipo, peso, obs, id_lote, lote_peso, operador):
    
    #tipomov = "ENT"
    #tipo = Visual / Temporario   = Normal / Adiantado ou Setor_Cobre

    item = item
    estoque_movs = Config_Visual.query.get('Atualizar_omie')
    status_mov = estoque_movs.info
    cadastro = Def_cadastro_prod(item)
    
    tipo_produto = cadastro[1]
    if tipo_produto == None:
        tipo_produto = "-"
                
    unidade = cadastro[3]
    if unidade == None:
        unidade = "-"

    id_produto = cadastro[0]
    if id_produto == None:
        id_produto = 0
    
    if tipomov == "SAI":
        tipom = "Saida"
        mot = "OPS"
        
    else:
        tipom = "Entrada"
        mot = "OPE"

    convert = Def_Convert_Unidade(tipom, unidade)
    
    valor_unitario = cadastro[4]
    print(quan)
    quan_omie = int(quan) * convert[1]
    
    if valor_unitario == None:
        valor_unitario = 0.0001
    else:
        valor_unitario * quan_omie

    if valor_unitario == 0:
        valor_unitario = 0.0001 
    
    
    
    if tipo_produto == "Produtivo":
        if status_mov == "Omie":
            data2 = {
                    "call":"IncluirAjusteEstoque",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param":[{
                                "codigo_local_estoque": local,
                                "id_prod": id_produto,
                                "data": datahora("data"),
                                "quan": quan_omie,
                                "obs": "Ajuste feito pelo Sistema Visual",
                                "origem": "AJU",
                                "tipo": tipomov,
                                "motivo": mot,
                                "valor": valor_unitario
                            }
                    ]}
            response = requests.post(url=url_ajuste_estoque, json=data2)
            ajuste = response.json()

            status = ajuste.get('codigo_status')
            id_movest = ajuste.get('id_movest')
            id_ajuste = ajuste.get('id_ajuste')
        else:
            status = "Estoque Desabilitado"
            id_movest = 0
            id_ajuste = 0  
    else:
        status = "Não Produtivo"
        id_movest = 0
        id_ajuste = 0 
    
    if status == None:
        status = "erro"
        id_movest = 0
        id_ajuste = 0 
    elif status == "0":
        status = "ok"
        id_movest = 0
        id_ajuste = 0 


    quantidade = int(quan)
    data_criacao = datahora("data")
    tempfino = Def_Caracter(id_produto)
    
    if tempfino[0] == None:
            fino = 0
            quantidade = int(quan)
            print("point 2")
    else:
        fino = float(peso) * (float(tempfino[0].replace(",",".")) / float(tempfino[1].replace(",",".")) )
        fino = int(fino)

    print("point 1")
    if tipomov == "ENT":
        if lote_peso == "Não":
            lote = Def_numero_lote(referencia)
            numero_lote =  "".join([str(lote), "/", str(referencia) ])
        
    
        
            # Configuração do logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)




            try:
                novo_lote = Lote_visual(
                referencia=referencia, 
                tipo=tipo, 
                item=item, 
                lote_visual=lote, 
                numero_lote=numero_lote, 
                quantidade=quan, 
                peso=peso, 
                fino=fino, 
                local=local, 
                obs=obs, 
                data_criacao=data_criacao, 
                processado_op=0, 
                quant_inicial=quan,
                operador=operador
                )
            
                db.session.add(novo_lote)
                db.session.commit()
                
                id_lote = novo_lote.id
                if id_lote == None:
                    id_lote = 0
                quantidade = int(quan)
                logger.info("Dados salvos com sucesso no Lote_visual.")
                print("Dados salvos com sucesso no Lote_visual.")
                #return {"status": "success", "message": "Dados salvos com sucesso."}
                

            except Exception as e:
                db.session.rollback()
                logger.error("Erro ao salvar os dados no Lote_visual: %s", e)
                print("Erro ao salvar os dados no Lote_visual: %s", e)
                returnt = {"status": "error", "message": "Erro ao salvar os dados.", "details": str(e)}
                print(returnt)
        elif lote_peso == "Sim":
            lote = 1    
            numero_lote =  "".join([str(lote), "/", str(referencia) ])
            
            # Configuração do logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)




            try:
                
                 lote_visual = Lote_visual.query.filter_by(item=item, lote_visual=lote, referencia = referencia).first()
                 if lote_visual:

                    lote_visual.quantidade = lote_visual.quantidade + quan
                    lote_visual.peso = lote_visual.peso + peso
                    lote_visual.fino = lote_visual.fino + fino
                     
                    db.session.commit()
                 else:
                     novo_lote = Lote_visual(
                     referencia=referencia, 
                     tipo=tipo, 
                     item=item, 
                     lote_visual=lote, 
                     numero_lote=numero_lote, 
                     quantidade=quan, 
                     peso=peso, 
                     fino=fino, 
                     local=local, 
                     obs=obs, 
                     data_criacao=data_criacao, 
                     processado_op=0, 
                     quant_inicial=quan,
                     operador=operador
                     )
                
                     db.session.add(novo_lote)
                     db.session.commit()
                    
                     id_lote = novo_lote.id
                     if id_lote == None:
                        id_lote = 0
                     quantidade = int(quan)
                     logger.info("Dados salvos com sucesso no Lote_visual.")
                     print("Dados salvos com sucesso no Lote_visual.")
                     #return {"status": "success", "message": "Dados salvos com sucesso."}
                    

            except Exception as e:
                db.session.rollback()
                logger.error("Erro ao salvar os dados no Lote_visual: %s", e)
                print("Erro ao salvar os dados no Lote_visual: %s", e)
                returnt = {"status": "error", "message": "Erro ao salvar os dados.", "details": str(e)}
                print(returnt)
        else:
                
                lote_visual = Lote_visual.query.filter_by(item=item, lote_visual=lote, referencia = referencia).first()
                if lote_visual:
                    lote_visual.quantidade = lote_visual.quantidade - quan
                    lote_visual.peso = lote_visual.peso - peso
                    lote_visual.fino = lote_visual.fino - fino
                     
                    db.session.commit()
 




    else:
        quantidade = neg(quan)
        lote = Def_numero_lote(referencia)
        numero_lote =  "".join([str(lote), "/", str(referencia) ])

    movs_status = Def_movimento_estoque(item, tipom, lote, referencia, quantidade, local, obs, id_movest,  id_ajuste, status_mov, id_lote)
    print("id_lote")
    print(id_lote)
    return [id_produto, tipo, status, unidade, valor_unitario, quan_omie, numero_lote, id_lote, lote]


#===================definição de transferencia de estoque ==================#

def Def_tranf_estoque(item, quan, local, local_dest, id_lote):
    item = item
    estoque_omie = Config_Visual.query.get('Atualizar_omie') 
    
    cadastro = Def_cadastro_prod(item)

    tipo = cadastro[1]
    if tipo == None:
        tipo = "-"
                
    unidade = cadastro[3]
    if unidade == None:
        unidade = "-"

    id_produto = cadastro[0]
    if id_produto == None:
        id_produto = 0

    valor_unitario = cadastro[4]
    if valor_unitario == None:
        valor_unitario =  0.0001

    if valor_unitario == 0:
        valor_unitario = 0.0001

    convert = Def_Convert_Unidade("Entrada", unidade)
    quantidade = quan    
    quan = float(quan) * convert[1]
    quan = int(quan)
    status_mov = estoque_omie.info
    if tipo == "Produtivo":
        if status_mov == "Omie":
            data = {
                    "call":"IncluirAjusteEstoque",
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "param":[{
                                "codigo_local_estoque": local,
                                "id_prod": id_produto,
                                "data": datahora("data"),
                                "quan": quan,
                                "obs": "Ajuste feito pelo Vipro.AI",
                                "origem": "AJU",
                                "tipo": "TRF",
                                "motivo": "TRF",
                                "valor": valor_unitario,
                                "codigo_local_estoque_destino": local_dest
                                }
                    ]}
            response = requests.post(url=url_ajuste_estoque, json=data)
            ajuste = response.json()

            status = ajuste.get('codigo_status')
            id_movest = ajuste.get('id_movest')
            id_ajuste = ajuste.get('id_ajuste')
        else:
            status = "Estoque Desabilitado"

    else:
        status = "Não Produtivo"
    
    if status == None:
        status = "erro"
    elif status == "0":
        status = "ok"
    
    dados_lote = Lote_visual.query.get(id_lote)
    lote = dados_lote.lote_visual
    referencia = dados_lote.referencia
    obs = "Transferencia de Setor"
    quantidade = int(quantidade)
    quan_neg = neg(quantidade)
    tipom = "Saida"
    Def_movimento_estoque(item, tipom, lote, referencia, quan_neg, local, obs, id_movest,  id_ajuste, status_mov, id_lote)
    
    tipom = "Entrada"
    Def_movimento_estoque(item, tipom, lote, referencia, quantidade, local_dest, obs, id_movest,  id_ajuste, status_mov, id_lote)
    return [id_produto, tipo, status, unidade, valor_unitario]
   
#================definição de movimento de ops================#
def Def_mov_op(op_referencia, tipo_mov, item_estrutura, descricao_item, quantidade_item, peso, fino):

    quantidade_real = 0
    
    mov = Estrutura_op(op_referencia = op_referencia, tipo_mov = tipo_mov, item_estrutura = item_estrutura, descricao_item = descricao_item, quantidade_item = quantidade_item, peso = peso, fino = fino, quantidade_real = quantidade_real)
    db.session.add(mov)
    db.session.commit()

    return redirect(request.referrer)
    
#================definição de converção de Unidade================#
def Def_Convert_Unidade(tipom, unidade):
    fatoromie = 1
    fatorvisual = 1

    if tipom == "Entrada":
      if unidade == "MIL":
          unidadef = "PC"
          fatoromie = 1 / 1000
          fatorvisual = 1

      if unidade == "PC":
          unidadef = "PC"
          fatoromie = 1
          fatorvisual = 1

      if unidade == "UN":
          unidadef = "PC"
          fatoromie = 1
          fatorvisual = 1

      if unidade == "KG":
          unidadef = "GR"
          fatoromie = 1 / 1000
          fatorvisual = 1
        
    if tipom == "Saida":
      if unidade == "MIL":
          unidadef = "PC"
          fatoromie = 1 / 1000
          fatorvisual = 1
         
      if unidade == "PC":
          unidadef = "PC"
          fatoromie = 1
          fatorvisual = 1

      if unidade == "UN":
          unidadef = "PC"
          fatoromie = 1
          fatorvisual = 1

      if unidade == "KG":
          unidadef = "GR"
          fatoromie = 1 / 1000
          fatorvisual = 1

    if tipom == "Consulta":
      
      if unidade == "PC":
          unidadef = "PC"
          fatoromie = 1
          fatorvisual = 1

      if unidade == "UN":
          unidadef = "PC"
          fatoromie = 1
          fatorvisual = 1

      if unidade == "KG":
          unidadef = "GR"
          fatoromie = 1 # não usa
          fatorvisual = 1000
      
      if unidade == "MIL":
          unidadef = "PC"
          fatoromie = 1 # não usa
          fatorvisual = 1000
      else:
        unidadef = "PC"
        fatoromie = 1 # não usa
        fatorvisual = 1

          

    
    return [unidadef, fatoromie, fatorvisual]

#===================definição de caracteristicas =================#
def Def_Caracter(idprod):
 data = {
                "call":"ConsultarCaractProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                         "nCodProd": idprod,
                         "cCodIntProd": "",
                         "nCodCaract": 3638913624,
                         "cCodIntCaract": ""
                                          }
                ]}
 response = requests.post(url=url_caracter, json=data)
 fino = response.json()
 data2 = {
                "call":"ConsultarCaractProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                         "nCodProd": idprod,
                         "cCodIntProd": "",
                         "nCodCaract": 4086784228,
                         "cCodIntCaract": ""
                                          }
                ]}
 response = requests.post(url=url_caracter, json=data2)
 unitario = response.json()

 peso_fino = fino.get('cConteudo')
 peso_unitario = unitario.get('cConteudo')

    


 return [peso_fino, peso_unitario]

def Def_Caracter_alt(idprod, fino, peso):
 data = {
                "call":"AlterarCaractProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                         "nCodProd": idprod,
                         "cCodIntProd": "",
                         "nCodCaract": 3638913624,
                         "cCodIntCaract": "",
                         "cConteudo": fino,
                         "cExibirItemNF": "N",
                         "cExibirItemPedido": "N",
                         "cExibirOrdemProd": "N"
                         }
                        ]}
 response = requests.post(url=url_caracter, json=data)
 status_fino = response.json()
 data2 = {
                "call":"AlterarCaractProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                         "nCodProd": idprod,
                         "cCodIntProd": "",
                         "nCodCaract": 4086784228,
                         "cCodIntCaract": "",
                         "cConteudo": peso,
                         "cExibirItemNF": "N",
                         "cExibirItemPedido": "N",
                         "cExibirOrdemProd": "N"
                         }
                        ]}
 response = requests.post(url=url_caracter, json=data2)
 status_unitario = response.json()
 ffino = status_fino.get('cDesStatus')
 fpeso = status_unitario.get('cDesStatus')
 
 return f"Status {ffino} - {fpeso}"
#=====================alterar estrutura====================#
def Def_alterar_estrutura(item):
    id = Def_id_produto(item)

    data = {
            "call":"AlterarEstrutura",
            "app_key": app_key,
            "app_secret": app_secret,
            "param":[{
                    "idProduto": id,
                        "itemMalhaAlterar": [
                        {
                        "idMalha": 2430284968,
                        "idProdMalha": 2424594641,
                        "quantProdMalha": 0.05524,
                        "obsProdMalha": "Estrutura alterada por Calculo de OP 2"
                        }
                    ]
                    }
            ]}
    response = requests.post(url=url_estrutura, json=data)
    estrutura = response.json()
        
    return estrutura


#===================Consulta de estrutura==================#
def Def_consulta_estrutura(item):
    #item = request.form.get("item")
    
        data = {
                "call":"ConsultarEstrutura",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                    "codProduto": item
                        }
                ]}
        response = requests.post(url=url_estrutura, json=data)
        estrutura = response.json()
        
        return estrutura
#===================numero de op==================#

def Def_numero_op():

 numero = Sequencia_op.query.get('ops_numero') 
 numero_op = numero.valor + 1
 numero.valor = numero.valor + 1
 numero.valor_anterior = numero.valor - 1
 db.session.commit()
 
 return numero_op
#===================numero de lote==================#

def Def_numero_lote(op):
    if Sequencia_lote.query.get(op) == None:
        mod_numero = Sequencia_lote(op_visual= op, valor = 1, valor_anterior = 0)
        db.session.add(mod_numero)
        db.session.commit()
        valor = 1
    else: 
        numero = Sequencia_lote.query.get(op)
        valor = numero.valor + 1
        numero.valor = numero.valor + 1
        numero.valor_anterior = numero.valor - 1
        db.session.commit()

    return valor
#===================validar Código=======================#

def Def_item_ok(item):
   item_M = item.upper()     
   data = {
                "call":"ConsultarProduto",
                "app_key": app_key,
                "app_secret": app_secret,
                "param":[{
                    "codigo": item_M
                        }
                ]}
   response = requests.post(url=url_produtos, json=data)
   cadastro = response.json()
   retorno = cadastro.get('codigo')
   if retorno == item_M:
       ok="ok"
   else:
       ok="não cadastrado"
       
   return [ok, item_M, cadastro]
#===================Definição de movimento de estoque==================#

def Def_movimento_estoque(item, tipo, lote_visual, referencia, quantidade, local, obs, id_movest,  id_ajuste, status_mov, id_lote):
        
    data_atual = datahora("data")
    hora_atual = datahora("hora")
    usuario = current_user.name
    novo_movimento = Movimentos_estoque(item = item, tipo = tipo,
                                        lote_visual = lote_visual,
                                        referencia = referencia, 
                                        quantidade = quantidade,
                                        local = local, obs = obs,
                                        data_movimento = data_atual,
                                        hora_movimento = hora_atual,
                                        usuario = usuario,
                                        id_movest = id_movest,
                                        id_ajuste = id_ajuste,
                                        status_mov = status_mov,
                                        id_lote = id_lote)
    db.session.add(novo_movimento)  
    db.session.commit()
         
    return redirect(request.referrer)

#===================fim das definições do diego ==================#
def Def_locais(id_local):
        
        
    if id_local == "2436985075":
        local = "Estoque"
    elif id_local == "2511785274":
        local = "Acabamento"
    elif id_local == "4084861665":
        local = "Setor Cobre"
    elif id_local == "4085565942":
        local = "Qualidade"
    elif id_local == "4085566100":
        local = "Seleção"
    elif id_local == "4085566245":
        local = "Embalagem"
    elif id_local == "4085566344":
        local = "MKM"

    return local
#===================testes temporarios do diego ==================#
# @app.route('/temp')
# def temp_prod():
#  return f" descrição = {Def_cadastro_prod('CBA-4000',A1)[5]} saldo = {Def_cadastro_prod('CBA-4000',A1)[2]}"

# @app.route('/temp2')
# def temp_ajust():
#  return f" id_produto = {Def_ajuste_estoque('TESTE1235',33,'ENT',AC)[0]} status = {Def_ajuste_estoque('TESTE1235',33,'ENT',AS)[2]} erro = {Def_ajuste_estoque('TESTE1235',33,'ENT',AS)[5]}"

@app.route('/temp3')
def estrut_ajust():
 return f" id_produto = {Def_alterar_estrutura('CBA-4000')} - "

@app.route('/temp4')
def estrut_consult():
 return f" id_produto = {Def_consulta_estrutura('CBA-4000')} - "


#===================definições simples do diego ==================#
def Def_id_produto(item):
 return Def_cadastro_prod(item)[0]

def Def_tipo(item):
 return Def_cadastro_prod(item)[1]

def Def_unidade(item):
 dados = Def_cadastro_prod(item)
 unidade_omie = dados[3]
 unidade = Def_Convert_Unidade("Consulta", unidade_omie)[0]
 return [unidade, unidade_omie]

def Def_valor_unitario(item):
 return Def_cadastro_prod(item)[4]

def Def_descricao(item):
 return Def_cadastro_prod(item)[5]

 











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
 
# abaixo a logica para salvar no banco de dados


def Def_salva_dados_excel():
    df = pd.read_excel('uploaded_file.xlsx') #recupera os dados do excel e salva na variavel df pode ser mantido como está
    
    
    data_atual = datahora("data")
    hora_atual = datahora("hora")
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
        setor = setor
        operador = operador
        quantidade_real = quantidade_real


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
            hora_abertura=hora_abertura,
            setor = setor,
            operador = operador,
            quantidade_real = quantidade_real

        )

        db.session.add(novo_item)

        print(f'Lançando no banco: {dados_do_excel}')      
    

    db.session.commit()
   
#===================Fim upload excel ==================#

@app.route('/indicadores')
def indicadores():
    site_externo = 'https://graf-kels.up.railway.app/'
    
    return redirect(site_externo)










if __name__ == "__main__":
    
    db.create_all()
    db.session.commit()

    app.run(port=3333, debug=True)

 