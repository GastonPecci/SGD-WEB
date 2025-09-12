from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    if not User.query.filter_by(email='sgdweb25@gmail.com').first():
        admin = User(
            nombre='Admin',
            email='sgdweb25@gmail.com',
            password=generate_password_hash('sgdweb1,2,3'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✔ Admin creado')
    else:
        print('Admin ya existe')
