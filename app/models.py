from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    confirmado = db.Column(db.Boolean, default=False)    
    bloqueado = db.Column(db.Boolean, default=False, nullable=False)
    is_staff = db.Column(db.Boolean, default=False)

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

    user = db.relationship('User', backref='reservas')
    cancha = db.relationship('Cancha', backref='reservas')

