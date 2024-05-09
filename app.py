import requests
from sqlalchemy import desc
from flask import Flask, render_template, flash, redirect, url_for, request, session, jsonify, json, send_from_directory
from datetime import date, datetime, timedelta, timezone
from models.models import Ops_visual, Movimentos_estoque, Estrutura_op, User, Lote_visual, Lotes_mov_op, Sequencia_op, Sequencia_lote, Config_Visual, Pedido
from models.forms import LoginForm, RegisterForm
from flask_login import login_user, logout_user, current_user
from config import app, db, app_key, app_secret, bcrypt, login_manager
from operator import neg
from reportlab.pdfgen import canvas
#import time
import re
import os
import pandas as pd


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

    dados = Def_cadastro_prod(item)
    
    return  render_template('itens.html',  dados = dados  )


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
    unidade = Def_unidade(item)[0]
    
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
@app.route('/ordens_producao_visual', methods = ['GET','POST'])
def ordens_producao_visual():


    filtro_op = request.form.get("filtro_op")
    filtro_cod = request.form.get("filtro_cod")
    
    if not current_user.is_authenticated:
     return redirect( url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    
    if filtro_op == "":
        filtro_op = None
    
    if filtro_cod == "":
        filtro_cod = None


    if filtro_op != None:
        dados = Ops_visual.query.order_by(Ops_visual.numero_op_visual.desc()).filter_by(numero_op_visual = filtro_op).paginate(page=page,per_page=10)
    else:
        if filtro_cod != None:
            dados = Ops_visual.query.order_by(Ops_visual.numero_op_visual.desc()).filter_by(item = filtro_cod).paginate(page=page,per_page=10)
        else:
            dados = Ops_visual.query.order_by(Ops_visual.numero_op_visual.desc()).paginate(page=page,per_page=10)    
    
    
    return render_template('ordens_producao_visual.html', itens = dados)

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
    #lotes = Lote_visual.query.filter_by(referencia = op).all()   
    op_info = Ops_visual.query.filter_by(numero_op_visual = op).all()
    estrutura_op = Def_consulta_estrutura(item)
    
    return render_template("mov_op_visual.html", ref=ref, op_info=op_info, op=op, estrutura_op= estrutura_op, mov_op = mov_op)



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
                                        fino = fino_parcial, data_mov = data_mov, id_lote = id_lote) 

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
    lote_visual = Def_numero_lote(referencia)
    tipo = request.form.get("tipo_mov")
    qtd_parcial = request.form.get("qtd_parcial")
    id = request.form.get("id")
    peso_parcial = request.form.get("peso_parcial")
    local = request.form.get("local_dest")
    data_mov = datahora("data")
    OP_Origem = request.form.get("OP_Origem")

    id_prod = Def_id_produto(item)
    fino_uni = Def_Caracter(id_prod)[0]
    fino_parcial = int(qtd_parcial.replace(",0","")) * float(fino_uni.replace(",","."))
    fino = fino_parcial
        
    
    if qtd_parcial == None:
        qtd_parcial = 0
        x = 0
    else:
        x = int(qtd_parcial)
        peso_parcial = int(peso_parcial)

    
    
    if x > 0:

        novo_lote = Lote_visual(referencia=referencia, tipo=tipo, item=item, lote_visual=lote_visual, numero_lote=lote_visual, quantidade=qtd_parcial, peso=peso_parcial, fino=fino, local=local, obs="", data_criacao=data_mov, processado_op = OP_Origem, quant_inicial = qtd_parcial)
                
        db.session.add(novo_lote)
        db.session.commit()
        id_lote = novo_lote.id
        add_lote_mov_op = Lotes_mov_op(referencia = referencia, tipo = tipo, item = item, lote_visual = lote_visual,
                                        numero_lote = lote_visual, quantidade = qtd_parcial, peso = peso_parcial,
                                        fino = fino_parcial, data_mov = data_mov, id_lote = id_lote) 

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
            
            obs = request.form.get("obs")
            um_omie = Def_unidade(item)[1]
            id_lote = 0 
            status_omie = Def_ajuste_estoque(item, quantidade,"ENT", local, referencia, tipo, peso, obs, id_lote)
            
            flash (f'Lote: {status_omie[6]} Lançado para o item: {item} = {status_omie[2]}, Quantidade Omie = {status_omie[5]} {um_omie}', category='success')
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
        db.session.delete(id_delete)
        db.session.commit()

        omie = Def_ajuste_estoque(item, quantidade,"SAI", local, referencia, tipo, peso, obs, id)
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
    lotes = Lote_visual.query.order_by(Lote_visual.id.desc()).filter_by(processado_op = 0, item = item_estrutura)

    return render_template("lotes_mov_op.html", Lotes_mov = Lotes_mov, lotes = lotes, op_referencia = op_referencia, item_estrutura = item_estrutura,
                           descricao_item = descricao_item, quantidade_item_total = quantidade_item_total,
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

    Lotes_mov = Lotes_mov_op.query.order_by(Lotes_mov_op.id.desc()).filter_by(referencia = op_referencia,item = item_estrutura)
    #lotes = Lote_visual.query.order_by(Lote_visual.id.desc()).filter_by(processado_op = 0, item = item_estrutura)

    return render_template("lotes_mov_op_prod.html", Lotes_mov = Lotes_mov, op_referencia = op_referencia, item_estrutura = item_estrutura,
                           descricao_item = descricao_item, quantidade_item_total = quantidade_item_total,
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
    quant = request.form.get("quantidade")

    db.session.delete(lotes_mov_op)
    db.session.commit()
    
    
    env_lote = Lote_visual.query.get(id_lote)
    env_lote.quantidade = env_lote.quantidade + int(quant)
    
    
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

@app.route('/op_cards', methods = ['GET','POST'])
def op_cards():

    pedidos = Pedido.query.filter_by().all()
    
    return render_template('op_cards.html',pedidos = pedidos)

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


@app.route('/update_pedido', methods=['POST'])
def update_pedido():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    data = request.get_json()  # Obter dados como JSON
    pedido_id = data['pedidoId']
    edit_item = Pedido.query.get(pedido_id)
 
    if edit_item:
        edit_item.peso = data['data']['peso']
        edit_item.peso_total = data['data']['peso_total']
        edit_item.material = data['data']['material']
        edit_item.peso_material = data['data']['peso_material']
        edit_item.amarrados = data['data']['amarrados']
        edit_item.dimencional_real = data['data']['dimencional_real']
        edit_item.Status = "Qualidade"
        edit_item.obs = data['data']['obs']  # Certifique-se de que a chave 'obs' está correta no JSON

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

def Def_cadastro_prod(item):
   item = item

    
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

def Def_ajuste_estoque(item, quan, tipomov, local, referencia, tipo, peso, obs, id_lote):
        

        
        #tipomov = "ENT"
        #tipo = Visual / Temporario   = Normal / Adiantado

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
                                    "obs": "Ajuste feito pelo Vipro.AI",
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
        lote = Def_numero_lote(referencia)
        data_criacao = datahora("data")
        numero_lote =  "".join([str(lote), "/", str(referencia) ])
        tempfino = Def_Caracter(id_produto)
        if tempfino[0] == None:
                fino = 0
                quantidade = int(quan)
        else:
            if tipomov == "ENT":
                fino = float(peso) * (float(tempfino[0].replace(",",".")) / float(tempfino[1].replace(",",".")) )
                fino = int(fino)
                novo_lote = Lote_visual(referencia=referencia, tipo=tipo, item=item, lote_visual=lote, numero_lote=numero_lote, quantidade=quan, peso=peso, fino=fino, local=local, obs=obs, data_criacao=data_criacao, processado_op=0, quant_inicial = quan)
                
                db.session.add(novo_lote)
                db.session.commit()
                id_lote = novo_lote.id
                if id_lote == None:
                    id_lote = 0
                quantidade = int(quan)
    
            else:
                quantidade = neg(quan)

        Def_movimento_estoque(item, tipom, lote, referencia, quantidade, local, obs, id_movest,  id_ajuste, status_mov, id_lote)
        return [id_produto, tipo, status, unidade, valor_unitario, quan_omie, numero_lote]

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
    return redirect(url_for('upload_excel'))




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

 