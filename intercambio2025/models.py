from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    presupuesto_min = db.Column(db.Float, nullable=False)
    presupuesto_max = db.Column(db.Float, nullable=False)
    jefe_familia = db.Column(db.String(50), nullable=False)
    navidad_tepoztlan = db.Column(db.String(50), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    santa_claus_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    regalos = db.relationship('Regalo', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.nombre}>'

class Regalo(db.Model):
    __tablename__ = 'regalos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    opcion1 = db.Column(db.String(200), nullable=False)
    opcion2 = db.Column(db.String(200), nullable=False)
    opcion3 = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Regalo usuario_id={self.usuario_id}>'

class Mensaje(db.Model):
    __tablename__ = 'mensajes'
    
    id = db.Column(db.Integer, primary_key=True)
    remitente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    leido = db.Column(db.Boolean, default=False)
    
    # Relaciones
    remitente = db.relationship('Usuario', foreign_keys=[remitente_id], backref='mensajes_enviados')
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref='mensajes_recibidos')
    
    def __repr__(self):
        return f'<Mensaje de {self.remitente_id} a {self.destinatario_id}>'

