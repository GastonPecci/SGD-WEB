from . import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    ultimo_premio = db.Column(db.DateTime, nullable=True)
    contador_reservas = db.Column(db.Integer, default=0, nullable=False)
    telefono = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    confirmado = db.Column(db.Boolean, default=False)    
    bloqueado = db.Column(db.Boolean, default=False, nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    session_token = db.Column(db.String(255), nullable=True)
    

class Cancha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)   
    detalle = db.Column(db.String(200), nullable=True) 

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cancha_id = db.Column(db.Integer, db.ForeignKey('cancha.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    tipo_reserva = db.Column(db.String(20), default="normal")  
    user = db.relationship('User', backref=db.backref('reservas', lazy=True))
    cancha = db.relationship('Cancha', backref=db.backref('reservas', lazy=True))

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)
    precio = db.Column(db.Float, nullable=False)  # 💲 nuevo campo para calcular monto

class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    monto = db.Column(db.Float, nullable=False)  # 💲 total de la venta
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

     
    producto = db.relationship('Producto', backref=db.backref('ventas', lazy=True))
