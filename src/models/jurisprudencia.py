from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Jurisprudencia(db.Model):
    __tablename__ = 'jurisprudencia'
    
    id = db.Column(db.Integer, primary_key=True)
    tribunal = db.Column(db.String(10), nullable=False)  # STF, STJ, TST, TSE, STM, TJSP
    numero_processo = db.Column(db.String(100), nullable=False)
    relator = db.Column(db.String(200))
    data_julgamento = db.Column(db.Date)
    data_publicacao = db.Column(db.Date)
    ementa = db.Column(db.Text)
    acordao = db.Column(db.Text)
    tags = db.Column(db.Text)  # palavras-chave separadas por vírgula
    url_origem = db.Column(db.String(500))
    data_coleta = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Jurisprudencia {self.tribunal} - {self.numero_processo}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tribunal': self.tribunal,
            'numero_processo': self.numero_processo,
            'relator': self.relator,
            'data_julgamento': self.data_julgamento.isoformat() if self.data_julgamento else None,
            'data_publicacao': self.data_publicacao.isoformat() if self.data_publicacao else None,
            'ementa': self.ementa,
            'acordao': self.acordao,
            'tags': self.tags,
            'url_origem': self.url_origem,
            'data_coleta': self.data_coleta.isoformat() if self.data_coleta else None
        }

class Enunciado(db.Model):
    __tablename__ = 'enunciados'
    
    id = db.Column(db.Integer, primary_key=True)
    orgao = db.Column(db.String(20), nullable=False)  # FONAJE, CNJ
    tipo = db.Column(db.String(20), nullable=False)  # CIVEL, CRIMINAL, FAZENDA_PUBLICA
    numero = db.Column(db.Integer, nullable=False)
    texto = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    data_aprovacao = db.Column(db.Date)
    data_coleta = db.Column(db.DateTime, default=datetime.utcnow)
    url_origem = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<Enunciado {self.orgao} {self.tipo} - {self.numero}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'orgao': self.orgao,
            'tipo': self.tipo,
            'numero': self.numero,
            'texto': self.texto,
            'observacoes': self.observacoes,
            'data_aprovacao': self.data_aprovacao.isoformat() if self.data_aprovacao else None,
            'data_coleta': self.data_coleta.isoformat() if self.data_coleta else None,
            'url_origem': self.url_origem
        }

class SentencaUsuario(db.Model):
    __tablename__ = 'sentencas_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(200), nullable=False)
    texto_extraido = db.Column(db.Text, nullable=False)
    caracteristicas_estilo = db.Column(db.Text)  # JSON com características do estilo
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SentencaUsuario {self.nome_arquivo}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_arquivo': self.nome_arquivo,
            'texto_extraido': self.texto_extraido,
            'caracteristicas_estilo': self.caracteristicas_estilo,
            'data_upload': self.data_upload.isoformat() if self.data_upload else None
        }

