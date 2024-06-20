from config import db
from flask_login import UserMixin
from datetime import datetime
from pytz import timezone



class Ops_visual(db.Model):
    __tablename__='ops_visual'

    id = db.Column(db.Integer, primary_key=True)   
    numero_op_visual = db.Column(db.String(50),unique=True)
    piv = db.Column(db.Integer)
    situação = db.Column(db.String(50))
    item = db.Column(db.String(50))
    descrição = db.Column(db.String(255))
    quantidade = db.Column(db.Integer)
    peso_enviado = db.Column(db.Integer)
    peso_retornado = db.Column(db.Integer)
    fino_enviado = db.Column(db.Integer)
    fino_retornado = db.Column(db.Integer)
    data_abertura = db.Column(db.String(255))
    hora_abertura = db.Column(db.String(255))
    setor = db.Column(db.String(255))
    operador = db.Column(db.String(255))
    quantidade_real = db.Column(db.Integer)
    



    def __init__(self, numero_op_visual, piv, situação, item, descrição, quantidade, peso_enviado, peso_retornado, fino_enviado, fino_retornado, data_abertura, hora_abertura, setor, operador, quantidade_real):
        
        self.numero_op_visual = numero_op_visual
        self.piv = piv
        self.situação = situação
        self.item = item
        self.descrição = descrição
        self.quantidade = quantidade
        self.peso_enviado = peso_enviado
        self.peso_retornado = peso_retornado
        self.fino_enviado = fino_enviado
        self.fino_retornado = fino_retornado
        self.data_abertura = data_abertura
        self.hora_abertura = hora_abertura
        self.setor = setor
        self.operador = operador
        self.quantidade_real =quantidade_real

    def __repr__(self):
        return 'Ops: {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}' .format(self.id, self.numero_op_visual, self.piv, self.situação, self.item, self.descrição, 
                                                                    self.quantidade, self.peso_enviado, self.peso_retornado, self.fino_enviado, self.fino_retornado, self.data_abertura, self.setor, self.operador, self.quantidade_real)


class Lote_visual(db.Model):
    __tablename__='lote_visual'

    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    item = db.Column(db.String(50), nullable=False)
    lote_visual = db.Column(db.String(50), nullable=False)
    numero_lote = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Integer, nullable=False)
    fino = db.Column(db.Float)
    local = db.Column(db.String(50), nullable=False)
    obs = db.Column(db.String(250))
    data_criacao = db.Column(db.String(250), nullable=False)
    processado_op = db.Column(db.Integer)
    quant_inicial = db.Column(db.Integer, nullable=False)
    operador = db.Column(db.String(50))
        
    
    def __init__(self, referencia, tipo, item, lote_visual, numero_lote, quantidade, peso, fino, local, obs, data_criacao, processado_op, quant_inicial, operador):
        
        self.referencia = referencia
        self.tipo = tipo
        self.item = item
        self.lote_visual = lote_visual
        self.numero_lote = numero_lote
        self.quantidade = quantidade
        self.peso = peso
        self.fino = fino
        self.local = local
        self.obs = obs
        self.data_criacao = data_criacao
        self.processado_op = processado_op
        self.quant_inicial = quant_inicial
        self.operador = operador
        

    def __repr__(self):
        return f"Lote_visual(id={self.id}, referencia={self.referencia}, tipo={self.tipo},  item={self.item}, lote_visual={self.lote_visual}, numero_lote={self.numero_lote}, quantidade={self.quantidade}, peso={self.peso}, fino = {self.fino}, local = {self.local}, obs = {self.obs}, data_criacao = {self.data_criacao}, processado_op = {self.processado_op}, quant_inicial = {self.quant_inicial}, operador = {self.operador})"

class Estrutura_op(db.Model):
    __tablename__='estrutura_op'

    id = db.Column(db.Integer, primary_key=True)
    op_referencia = db.Column(db.Integer, nullable=False)
    tipo_mov = db.Column(db.String(50)) 
    item_estrutura = db.Column(db.String(50))
    descricao_item = db.Column(db.String(255))
    quantidade_item = db.Column(db.Float)
    quantidade_real = db.Column(db.Integer)
    peso = db.Column(db.Float)
    fino = db.Column(db.Float)
    

    
    def __init__(self, op_referencia, tipo_mov, item_estrutura, descricao_item, 
                quantidade_item, quantidade_real, peso, fino):  

        self.op_referencia = op_referencia
        self.tipo_mov = tipo_mov
        self.item_estrutura = item_estrutura
        self.descricao_item = descricao_item
        self.quantidade_item = quantidade_item
        self.quantidade_real = quantidade_real
        self.peso = peso
        self.fino = fino
       

    def __repr__(self):
        return 'estrutura_op: {} - {} - {} - {} - {} - {} - {} - {}' .format(self.op_referencia, self.tipo_mov, self.item_estrutura, self.descricao_item, self.quantidade_item, self.quantidade_real, self.peso, self.fino)


class Lotes_mov_op(db.Model):
    __tablename__='lotes_mov_op'

    id = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    item = db.Column(db.String(50), nullable=False)
    lote_visual = db.Column(db.String(50), nullable=False)
    numero_lote = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Integer, nullable=False)
    fino = db.Column(db.Integer)
    data_mov = db.Column(db.String(250), nullable=False)
    id_lote = db.Column(db.Integer)
    operador = db.Column(db.String(50))
    
    def __init__(self, referencia, tipo, item, lote_visual, numero_lote, quantidade, peso, fino, data_mov, id_lote, operador):
        
        self.referencia = referencia
        self.tipo = tipo
        self.item = item
        self.lote_visual = lote_visual
        self.numero_lote = numero_lote
        self.quantidade = quantidade
        self.peso = peso
        self.fino = fino
        self.data_mov = data_mov
        self.id_lote = id_lote
        self.operador = operador
        

    def __repr__(self):
        return f"Lote_visual(id={self.id}, referencia={self.referencia}, tipo={self.tipo},  item={self.item}, lote_visual={self.lote_visual}, numero_lote={self.numero_lote}, quantidade={self.quantidade}, peso={self.peso}, fino = {self.fino}, data_mov = {self.data_mov}, id_lote = {self.id_lote}, operador = {self.operador})"




class Sequencia_op(db.Model):
    __tablename__='sequencia_op'
    
    tabela_campo = db.Column(db.String(50), primary_key=True)
    valor = db.Column(db.Integer, nullable=False)
    valor_anterior = db.Column(db.Integer, nullable=False)

    def __init__(self, tabela_campo, valor, valor_anterior):

        self.tabela_campo = tabela_campo
        self.valor = valor
        self.valor_anterior = valor_anterior
    
    def __repr__(self):
        return 'sequencia: {} - {} - {}' .format(self.tabela_campo, self.valor, self.valor_anterior) 


class Sequencia_lote(db.Model):
    __tablename__='sequencia_lote'
    
    op_visual = db.Column(db.String(50), primary_key=True)
    valor = db.Column(db.Integer, nullable=False)
    valor_anterior = db.Column(db.Integer, nullable=False)

    def __init__(self, op_visual, valor, valor_anterior):

        self.op_visual = op_visual
        self.valor = valor
        self.valor_anterior = valor_anterior
    
    def __repr__(self):
        return 'sequencia: {} - {} - {}' .format(self.op_visual, self.valor, self.valor_anterior) 

class Config_Visual(db.Model):
    __tablename__='config_visual'
    
    config = db.Column(db.String(50), primary_key=True)
    info = db.Column(db.String(50), nullable=False)
    
    def __init__(self, config, info):

        self.config = config
        self.info = info
        
    def __repr__(self):
        return 'sequencia: {} - {} - {}' .format(self.config, self.info) 



class Movimentos_estoque(db.Model):
    __tablename__='Movimentos_estoque'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    lote_visual = db.Column(db.String(50))
    referencia = db.Column(db.String(50))
    quantidade = db.Column(db.Integer)
    local = db.Column(db.String(50))
    obs = db.Column(db.String(250))
    data_movimento = db.Column(db.String(255))
    hora_movimento = db.Column(db.String(255))
    usuario = db.Column(db.String(90))
    id_movest = db.Column(db.BigInteger)
    id_ajuste = db.Column(db.BigInteger)
    status_mov = db.Column(db.String(50))
    id_lote = db.Column(db.Integer)
    

    def __init__(self, item, tipo, lote_visual, referencia,
                 quantidade, local, obs,  data_movimento, hora_movimento,
                 usuario, id_movest, id_ajuste, status_mov, id_lote):  

        self.item = item
        self.tipo = tipo
        self.lote_visual = lote_visual
        self.referencia = referencia
        self.quantidade = quantidade
        self.local = local
        self.obs = obs
        self.data_movimento = data_movimento
        self.hora_movimento = hora_movimento
        self.usuario = usuario
        self.id_movest = id_movest
        self.id_ajuste = id_ajuste
        self.status_mov = status_mov
        self.id_lote = id_lote


    def __repr__(self):
        return 'Movimentos_estoque: {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}' .format(self.id, self.item, self.tipo, self.lote_visual,self.referencia, 
                self.quantidade, self.local, self.obs, self.data_movimento, self.hora_movimento, self.usuario, self.id_movest, self.id_ajuste, self.status_mov, self.id_lote)



class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    def __init__(self, email, password, name):
        self.email = email
        self.password = password
        self.name = name

        
    def __repr__(self):
        return "<User %r>" % self.email

class Pedido(db.Model):
    __tablename__='pedido'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pedido = db.Column(db.String(50)) 
    emissao = db.Column(db.String(250), nullable=False)
    descricao = db.Column(db.String(255))
    cliente = db.Column(db.String(255))
    codigo = db.Column(db.String(50))
    data_entrega = db.Column(db.String(250), nullable=False)
    obs_entrega = db.Column(db.String(255))
    dimensional = db.Column(db.String(255))
    quantidade = db.Column(db.Float)
    peso = db.Column(db.Float)
    peso_total = db.Column(db.Float)
    Status = db.Column(db.String(50), default='Emitido')
    material = db.Column(db.String(50), default='01CU800')
    peso_material = db.Column(db.Float)
    amarrados = db.Column(db.Integer)
    dimencional_real = db.Column(db.String(255))
    obs = db.Column(db.String(250))
    canto = db.Column(db.String(50))
    furo = db.Column(db.String(50))
    embalagem = db.Column(db.String(250))
    status2 = db.Column(db.String(50), default='Emitido')
    qtd_faturada = db.Column(db.Float)
    packlist = db.Column(db.Integer)
   
    
    

    
    def __init__(self, pedido, emissao, descricao, cliente, codigo, data_entrega,
                 obs_entrega, dimensional, quantidade, peso, peso_total, Status,
                 material, peso_material, amarrados, dimencional_real, obs, canto, furo, embalagem, status2, qtd_faturada, packlist):

        self.pedido = pedido
        self.emissao = emissao
        self.descricao = descricao
        self.cliente = cliente
        self.codigo = codigo
        self.data_entrega = data_entrega
        self.obs_entrega = obs_entrega
        self.dimensional = dimensional
        self.quantidade = quantidade
        self.peso = peso
        self.peso_total = peso_total
        self.Status = Status
        self.material = material
        self.peso_material = peso_material
        self.amarrados = amarrados
        self.dimencional_real = dimencional_real
        self.obs = obs
        self.canto = canto
        self.furo = furo
        self.embalagem = embalagem
        self.status2 = status2
        self.qtd_faturada = qtd_faturada
        self.packlist = packlist
      

    def __repr__(self):
        return 'pedido: {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}' .format(self.id, self.pedido, self.emissao,
                                                                                                          self.descricao, self.cliente, self.codigo, self.data_entrega,
                                                                                                          self.obs_entrega, self.dimensional, self.quantidade, self.peso,
                                                                                                          self.peso_total, self.Status, self.material, self.peso_material,
                                                                                                          self.amarrados, self.dimencional_real, self.obs, self.canto,
                                                                                                          self.furo, self.embalagem, self.status2, self.qtd_faturada, self.packlist)



class Ferramentas(db.Model):
    __tablename__='ferramentas'

    id = db.Column(db.Integer, primary_key=True)
    dimensional = db.Column(db.String(250), unique=True)
    quantidade = db.Column(db.Float)
    obs = db.Column(db.String(250))
    
    def __init__(self, dimensional, quantidade, obs):

        
        self.dimensional = dimensional
        self.quantidade = quantidade
        self.obs = obs


    def __repr__(self):
        return 'Ferramentas: {} - {} - {} - {}' .format(self.id, self.dimensional, self.quantidade, self.obs) 

class Validacao(db.Model):
    __tablename__='validacao'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(100), unique=True)
    telas = db.Column(db.String(250))
    validacao_1 = db.Column(db.String(250))
    validacao_2 = db.Column(db.String(250))
    validacao_3 = db.Column(db.String(250))
    validacao_4 = db.Column(db.String(250))
    validacao_5 = db.Column(db.String(250))
    validacao_6 = db.Column(db.String(250))
    validacao_7 = db.Column(db.String(250))
    validacao_8 = db.Column(db.String(250))
    validacao_9 = db.Column(db.String(250))
    validacao_10 = db.Column(db.String(250))


    def __init__(self, usuario, telas, validacao_1, validacao_2, validacao_3, validacao_4, validacao_5,
                  validacao_6, validacao_7, validacao_8, validacao_9, validacao_10):

        
        self.usuario = usuario
        self.telas = telas
        self.validacao_1 = validacao_1
        self.validacao_2 = validacao_2
        self.validacao_3 = validacao_3
        self.validacao_4 = validacao_4
        self.validacao_5 = validacao_5
        self.validacao_6 = validacao_6
        self.validacao_7 = validacao_7
        self.validacao_8 = validacao_8
        self.validacao_9 = validacao_9
        self.validacao_10 = validacao_10


    def __repr__(self):
        return 'Validacao: {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}' .format(self.id, self.usuario, self.telas, self.validacao_1, self.validacao_2, self.validacao_3, self.validacao_4, self.validacao_5, self.validacao_6, self.validacao_7, self.validacao_8, self.validacao_9, self.validacao_10) 


class Packlist(db.Model):
    __tablename__='packlist'
    
    packlist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    peso_liquido = db.Column(db.Integer, nullable=False)
    peso_bruto = db.Column(db.Integer, nullable=False)
    embalagem = db.Column(db.String(250))
    obs_entrega = db.Column(db.String(255))
    obs = db.Column(db.String(255))
    status2 = db.Column(db.String(50))

   
    def __init__(self, peso_liquido, peso_bruto, embalagem, obs_entrega, obs, status2):

        self.peso_liquido = peso_liquido
        self.peso_bruto = peso_bruto
        self.embalagem = embalagem
        self.obs_entrega = obs_entrega
        self.obs = obs
        self.status2 = status2
    
    def __repr__(self):
        return 'Packlist: {} - {} - {} - {} - {} - {} - {}' .format(self.packlist_id, self.peso_liquido, self.peso_bruto,
                                                                self.embalagem, self.obs_entrega, self.obs, self.status2) 


class Cadastro_itens(db.Model):
    __tablename__='cadastro_itens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(250), nullable=False)
    cliente = db.Column(db.String(50))
    material = db.Column(db.String(50))
    peso = db.Column(db.Float)
    fino = db.Column(db.Float)
    unidade = db.Column(db.String(5))
    uso = db.Column(db.String(50)) #produtivo ou não produtivo
    data_alteracao = db.Column(db.String(255))
    obs = db.Column(db.String(255))
    id_produto = db.Column(db.String(10))
    um_visual = db.Column(db.String(2))
    codigo_cliente = db.Column(db.String(50))
    ncm = db.Column(db.String(10))
    familia = db.Column(db.String(50))
    setor = db.Column(db.String(50))
    valor_unitario = db.Column(db.Float)


    def __init__(self, item, descricao, cliente, material, peso, fino, unidade,
                 uso, data_alteracao, obs, id_produto, um_visual, codigo_cliente,
                 ncm, familia, setor, valor_unitario):

        self.item = item
        self.descricao = descricao
        self.cliente = cliente
        self.material = material
        self.peso = peso
        self.fino = fino
        self.unidade = unidade
        self.uso = uso
        self.data_alteracao = data_alteracao
        self.obs = obs
        self.id_produto = id_produto
        self.um_visual = um_visual
        self.codigo_cliente = codigo_cliente
        self.ncm = ncm
        self.familia = familia
        self.setor = setor
        self.valor_unitario = valor_unitario

    def __repr__(self):
        return 'Cadastro_itens: {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}' .format(self.id, self.item, self.descricao, self.material,
                                                                                    self.peso, self.fino, self.unidade, self.uso,
                                                                                    self.data_alteracao, self.obs, self.id_produto,
                                                                                    self.um_visual, self.codigo_cliente, self.ncm,
                                                                                    self.familia, self.setor, self.valor_unitario) 
    


class Setores(db.Model):
    __tablename__='setores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    setor = db.Column(db.String(50), unique=True)
    meta_fino = db.Column(db.Float)
    meta_retalho = db.Column(db.Float)
    meta_sucata = db.Column(db.Float)
    meta_falha = db.Column(db.Float)
    meta_selecao = db.Column(db.Float)
    meta_retrabalho = db.Column(db.Float)
    meta_setup = db.Column(db.Float)
    
    def __init__(self, setor, meta_fino, meta_retalho, meta_sucata, meta_falha, meta_selecao, meta_retrabalho, meta_setup):

        
        self.setor = setor
        self.meta_fino = meta_fino
        self.meta_retalho = meta_retalho
        self.meta_sucata = meta_sucata
        self.meta_falha = meta_falha
        self.meta_selecao = meta_selecao
        self.meta_retrabalho = meta_retrabalho
        self.meta_setup = meta_setup

    def __repr__(self):
        return 'Setores: {} - {} - {} - {} - {} - {} - {}  - {} - {}' .format(self.id, self.setor, self.meta_fino, self.meta_retalho, self.meta_sucata, self.meta_falha, self.meta_selecao, self.meta_retrabalho, self.meta_setup) 


class Operadores(db.Model):
    __tablename__='operadores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operador = db.Column(db.String(50))
    setor = db.Column(db.String(50))
    
    class Meta:
        unique_together = ('operador', 'setor',)
    
    def __init__(self, operador, setor):

        
        self.operador = operador
        self.setor = setor


    def __repr__(self):
        return 'Operadores: {} - {} - {}' .format(self.id, self.operador, self.setor) 


class Familia(db.Model):
    __tablename__='familia'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    familia = db.Column(db.String(50), unique=True)
    
    def __init__(self, familia):

        
        self.familia = familia


    def __repr__(self):
        return 'Familia: {} - {}' .format(self.id, self.familia) 
