import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from .models import db, User, Cancha, Reserva
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from app import mail
from flask import current_app
from markupsafe import Markup
from uuid import uuid4
from sqlalchemy import func
from collections import defaultdict

main = Blueprint('main', __name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))

def generar_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-confirmar')

def enviar_email_confirmacion(usuario_email):
    token = generar_token(usuario_email)
    link = url_for('main.confirmar_email', token=token, _external=True)

    msg = Message('Confirma tu correo', recipients=[usuario_email])
    msg.body = f'Hola, por favor confirmá tu correo visitando: {link}'  # opcional para clientes que no acepten HTML

    msg.html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
        <h2>¡Bienvenido/a!</h2>
        <p>Gracias por registrarte. Para confirmar tu cuenta, hacé clic en el siguiente botón:</p>
        <a href="{link}" style="
            display: inline-block;
            padding: 12px 24px;
            margin-top: 20px;
            font-size: 16px;
            color: white;
            background-color: #28a745;
            text-decoration: none;
            border-radius: 6px;
        ">Confirmar Email</a>
        <p style="margin-top: 30px; font-size: 12px; color: gray;">
            Si no solicitaste este registro, podés ignorar este mensaje.
        </p>
    </body>
    </html>
    """
    msg.charset = 'utf-8'
    mail.send(msg)


def enviar_email_reserva(usuario_email, cancha, fecha, hora):
    msg = Message('Confirmación de Reserva', recipients=[usuario_email])
    msg.body = f"""
Hola, tu reserva ha sido confirmada:

📍 Cancha: {cancha}
📅 Fecha: {fecha.strftime('%d/%m/%Y')}
⏰ Hora: {hora}

¡Gracias por usar nuestro sistema SGD-Web!
"""
    msg.charset = 'utf-8'
    mail.send(msg)

def agrupar_reservas(reservas):
    agrupadas = {}

    for r in reservas:
        clave = (r.user, r.cancha, r.fecha)  # guardamos objetos, no solo IDs
        if clave not in agrupadas:
            agrupadas[clave] = []
        if r.hora and ":" in r.hora:
            agrupadas[clave].append(r.hora)

    resultado = []
    for (user, cancha, fecha), horas in agrupadas.items():
        horas_filtradas = [h for h in horas if h and ":" in h]
        horas_ordenadas = sorted(horas_filtradas, key=lambda h: int(h.split(":")[0])) if horas_filtradas else []

        if len(horas_ordenadas) >= 12:
            hora_str = "Día completo"
        elif len(horas_ordenadas) > 1:
            hora_str = ", ".join(horas_ordenadas)
        else:
            hora_str = horas_ordenadas[0] if horas_ordenadas else "-"

        resultado.append({
            "user": user,
            "cancha": cancha,
            "fecha": fecha,
            "horas": hora_str
        })

    return resultado

@main.route('/')
def index():        
    canchas = Cancha.query.all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('index.html', canchas=canchas, user=user)

@main.route('/login', methods=['GET', 'POST'])
def login():    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.bloqueado:
            return render_template('login.html', error="Tu cuenta está bloqueada. Contacta con administración.")
        if user:
            if not user.confirmado:
                flash(Markup(f"No confirmaste tu cuenta. <a href='{url_for('main.reenviar_confirmacion', email=user.email)}' class='alert-link'>Reenviar correo</a>"))
                return redirect(url_for('main.login'))

            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                flash("Sesión iniciada correctamente")
                
                if user.is_admin or user.is_staff:
                    return redirect(url_for('main.admin'))
                else:
                    return redirect(url_for('main.index'))
        
    return render_template('login.html')

@main.route('/admin/usuario/<int:user_id>.json')
def admin_get_usuario(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
    return jsonify({
        'success': True,
        'id': user.id,
        'nombre': user.nombre,
        'apellido': user.apellido,
        'telefono': user.telefono or '',
        'email': user.email,
        'confirmado': bool(user.confirmado),
        'is_admin': bool(user.is_admin),
        'is_staff': bool(user.is_staff),
        'bloqueado': bool(user.bloqueado)
    })

@main.route('/admin/filtrar_reservas')
def filtrar_reservas():
    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            reservas_raw = Reserva.query.filter(Reserva.fecha == fecha).order_by(Reserva.hora).all()
        except ValueError:
            reservas_raw = []
    else:
        reservas_raw = Reserva.query.order_by(Reserva.fecha.desc()).all()

    reservas = agrupar_reservas(reservas_raw)
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('admin_reservas_parciales.html', reservas=reservas, user=user)

@main.route('/admin/bloquear_usuario/<int:user_id>', methods=['POST'])
def admin_bloquear_usuario(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    admin = User.query.get(session['user_id'])
    if not admin or not admin.is_admin:
        return jsonify({'success': False, 'message': 'Acceso denegado'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    user.bloqueado = not bool(user.bloqueado)
    db.session.commit()
    return jsonify({'success': True, 'bloqueado': bool(user.bloqueado)})

@main.route('/admin/editar_usuario/<int:user_id>', methods=['POST'])
def admin_editar_usuario(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    admin = User.query.get(session['user_id'])
    if not admin or not admin.is_admin:
        return jsonify({'success': False, 'message': 'Acceso denegado'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    user.nombre = request.form.get('nombre', user.nombre)
    user.apellido = request.form.get('apellido', user.apellido)
    user.telefono = request.form.get('telefono', user.telefono)
    email_nuevo = request.form.get('email', user.email)
    if email_nuevo:
        user.email = email_nuevo
    user.confirmado = True if request.form.get('confirmado') == 'on' else False
    user.is_admin = True if request.form.get('is_admin') == 'on' else False
    user.is_staff = True if request.form.get('is_staff') == 'on' else False
    user.bloqueado = True if request.form.get('bloqueado') == 'on' else False

    db.session.commit()
    return jsonify({'success': True, 'message': 'Usuario actualizado correctamente'})

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':        
        email = request.form['email']
        hashed_pw = generate_password_hash(request.form['password'])

        if User.query.filter_by(email=email).first():
            flash('Ese correo ya está registrado. Inicia sesión o recuperá tu cuenta.')
            return redirect(url_for('main.register'))
        new_user = User(
            nombre=request.form['nombre'],
            apellido=request.form['apellido'],
            telefono=request.form['telefono'],
            email=request.form['email'],
            password=hashed_pw,is_admin=False,
            confirmado=False
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Usuario registrado correctamente')
        enviar_email_confirmacion(new_user.email)
        flash('Te enviamos un correo para confirmar tu cuenta. Revisa tu bandeja.')        
    return render_template('register.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not (user.is_admin or user.is_staff):
        return redirect(url_for('main.index'))

        
    canchas = Cancha.query.all()
    usuarios = User.query.all()
    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            reservas = Reserva.query.filter(Reserva.fecha == fecha).order_by(Reserva.hora).all()
        except ValueError:
            reservas = Reserva.query.order_by(Reserva.fecha.desc()).all()
    else:
        reservas_raw = Reserva.query.order_by(Reserva.fecha.desc()).all()
        reservas = agrupar_reservas(reservas_raw)

    return render_template('admin.html', canchas=canchas, user=user, reservas=reservas,usuarios=usuarios)

@main.route('/confirmar/<token>')
def confirmar_email(token):
    try:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='email-confirmar', max_age=3600)  # 1 hora
    except Exception:
        return 'El enlace expiró o es inválido.'

    user = User.query.filter_by(email=email).first()
    if user is None:
        return 'Usuario no encontrado.'

    if user.confirmado:
        flash('Tu cuenta ya estaba confirmada. Iniciá sesión.')
        return redirect(url_for('main.login'))

    user.confirmado = True
    db.session.commit()
    flash('Tu cuenta fue confirmada exitosamente. Ahora podés iniciar sesión.')
    return redirect(url_for('main.login'))


@main.route('/reenviar_confirmacion/<email>')
def reenviar_confirmacion(email):
    user = User.query.filter_by(email=email).first()
    if user and not user.confirmado:
        enviar_email_confirmacion(user.email)
        flash('Te reenviamos el correo de confirmación.')
    else:
        flash('Este correo ya fue confirmado o no existe.')
    return redirect(url_for('main.login'))

@main.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generar_token(user.email)
            link = url_for('main.reestablecer_password', token=token, _external=True)
            msg = Message('Recuperación de Contraseña', recipients=[email])
            msg.body = f'Hacé clic en el siguiente enlace para reestablecer tu contraseña:\n\n{link}'
            msg.charset = 'utf-8'
            mail.send(msg)
            flash('Te enviamos un correo para restablecer tu contraseña.')
        else:
            flash('No se encontró ese correo.')
        return redirect(url_for('main.login'))

    return render_template('recuperar.html')

@main.route('/reestablecer/<token>', methods=['GET', 'POST'])
def reestablecer_password(token):
    try:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='email-confirmar', max_age=3600)
    except Exception:
        return 'El enlace expiró o no es válido.'

    user = User.query.filter_by(email=email).first()
    if not user:
        return 'Usuario no encontrado.'

    if request.method == 'POST':
        nueva_password = request.form['password']
        user.password = generate_password_hash(nueva_password)
        db.session.commit()
        flash('Contraseña restablecida con éxito. Ahora podés iniciar sesión.')
        return redirect(url_for('main.login'))

    return render_template('reestablecer.html')

@main.route('/api/canchas')
def api_canchas():
    canchas = Cancha.query.all()
    return jsonify([
        {"id": c.id, "title": c.nombre}
        for c in canchas
    ])

@main.route('/api/reservas')
def api_reservas():
    reservas = Reserva.query.all()
    return jsonify([
        {
            'title': f"Reservado - {r.user_id}",
            'start': f"{r.fecha}T{r.hora}",
            'end': f"{r.fecha}T{(datetime.strptime(r.hora, '%H:%M') + timedelta(hours=1)).strftime('%H:%M')}",
            'resourceId': r.cancha_id,
            'color': '#ff4d4d'
        }
        for r in reservas
    ])


@main.route('/reservas', methods=['GET', 'POST'])
def reservas():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])    
    canchas = Cancha.query.all()

    if request.method == 'POST':
        cancha_id = request.form.get('cancha_id')
        if not cancha_id:
            flash("Debes seleccionar una cancha.")
            return redirect(url_for('main.reservas'))

        cancha = Cancha.query.get(cancha_id)
        if not cancha:
            flash("Cancha no encontrada.")
            return redirect(url_for('main.reservas'))
        
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        hora = request.form['hora']

        reserva = Reserva(
            user_id=session['user_id'],
            cancha_id=cancha.id,
            fecha=fecha,
            hora=hora )
        db.session.add(reserva)
        db.session.commit()
        
        enviar_email_reserva(user.email, cancha.nombre, fecha, hora)
        flash('Reserva creada con éxito. Se envió una confirmación a tu correo.')

    reservas_usuario_raw = Reserva.query.filter_by(user_id=user.id).order_by(Reserva.fecha.desc()).all()
    reservas_usuario = agrupar_reservas(reservas_usuario_raw)

    return render_template('reservas.html', user=user, canchas=canchas, reservas=reservas_usuario)


@main.route('/admin/reserva_manual', methods=['POST'])
def reserva_manual():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    admin = User.query.get(session['user_id'])
    if not (admin.is_admin or admin.is_staff):
        return jsonify({'success': False, 'message': 'Acceso denegado'})

    try:
        HORAS_TODAS = [            
            '14:00','15:00','16:00','17:00','18:00','19:00',
            '20:00','21:00','22:00','23:00','00:00','01:00'
        ]
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form.get('telefono')
        email = request.form['email']
        cancha_id = request.form['cancha_id']
        if not cancha_id:
            return jsonify({'success': False, 'message': 'Debes seleccionar una cancha válida.'})
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        tipo = request.form['tipo_reserva']

        # Buscar o crear usuario
        correo_ficticio = f"{nombre.lower()}_{apellido.lower()}_{uuid4().hex[:5]}@sincorreo.com"
        user = User.query.filter_by(email=email).first() if email else None
        if not user:
            user = User(
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
                email=email or correo_ficticio,
                password=generate_password_hash("temporal123"),
                confirmado=True
            )
            db.session.add(user)
            db.session.commit()

        # Reservas
        horas_creadas = []
        if tipo == "una":
            hora = request.form['hora']
            db.session.add(Reserva(user_id=user.id, cancha_id=cancha_id, fecha=fecha, hora=hora))
            horas_creadas.append(hora)

        elif tipo == "varias":
            horas = request.form.getlist('horas[]')
            for h in horas:
                db.session.add(Reserva(user_id=user.id, cancha_id=cancha_id, fecha=fecha, hora=h))
            horas_creadas.extend(horas)

        elif tipo == "dia":
            reservas_existentes = Reserva.query.filter_by(cancha_id=cancha_id, fecha=fecha).all()
            horas_ocupadas = {r.hora for r in reservas_existentes}

            # 🚫 Caso 1: si ya hay todas las horas ocupadas → ya hay un día completo reservado
            if len(horas_ocupadas) >= len(HORAS_TODAS):
                return jsonify({'success': False, 'message': 'Ese día ya está reservado completamente.'})

            # 🚫 Caso 2: si hay aunque sea 1 hora ocupada → no permitir reservar el día completo
            if horas_ocupadas:
                return jsonify({'success': False, 'message': 'Ese día ya tiene reservas y no se puede reservar completo.'})

            # ✅ Caso válido → reservar todas las horas
            for h in HORAS_TODAS:
                db.session.add(Reserva(user_id=user.id, cancha_id=cancha_id, fecha=fecha, hora=h))

            db.session.commit()
            return jsonify({'success': True, 'message': f'Reserva creada para {nombre} {apellido} (Día completo)'})


        db.session.commit()
        return jsonify({'success': True, 'message': f'Reserva creada para {nombre} {apellido} ({", ".join(horas_creadas)})'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})



@main.route('/admin/agregar_cancha', methods=['POST'])
def agregar_cancha():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('main.index'))

    nombre = request.form['nombre']
    detalle= request.form['detalle']    
    cancha = Cancha(nombre=nombre, detalle=detalle)
    db.session.add(cancha)
    db.session.commit()
    return redirect(url_for('main.admin'))

@main.route('/admin/eliminar_cancha/<int:id>')
def eliminar_cancha(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('main.index'))

    cancha = Cancha.query.get(id)
    db.session.delete(cancha)
    db.session.commit()
    return redirect(url_for('main.admin'))

@main.route('/admin/eliminar_reserva/<int:id>', methods=['POST'])
def eliminar_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('main.index'))

    reserva = Reserva.query.get(id)
    if reserva:
        db.session.delete(reserva)
        db.session.commit()
        flash('Reserva eliminada correctamente.')
    else:
        flash('Reserva no encontrada.')

    return redirect(url_for('main.admin'))

@main.route('/admin/eliminar_reserva_grupo/<int:user_id>/<int:cancha_id>/<fecha>', methods=['POST'])
def eliminar_reserva_grupo(user_id, cancha_id, fecha):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    admin = User.query.get(session['user_id'])
    if not admin.is_admin:
        return redirect(url_for('main.index'))

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        reservas = Reserva.query.filter_by(user_id=user_id, cancha_id=cancha_id, fecha=fecha_dt).all()
        for r in reservas:
            db.session.delete(r)
        db.session.commit()
        flash("Reservas eliminadas con éxito.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error eliminando reservas: {str(e)}")

    return redirect(url_for('main.admin'))

@main.route('/reservas/eliminar/<int:user_id>/<int:cancha_id>/<fecha>', methods=['POST'])
def eliminar_reserva_usuario(user_id, cancha_id, fecha):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    # Solo puede eliminar sus propias reservas
    if session['user_id'] != user_id:
        flash("No tenés permisos para eliminar esta reserva.")
        return redirect(url_for('main.reservas'))

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        reservas = Reserva.query.filter_by(user_id=user_id, cancha_id=cancha_id, fecha=fecha_dt).all()
        for r in reservas:
            db.session.delete(r)
        db.session.commit()
        flash("Reserva eliminada con éxito.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la reserva: {str(e)}")

    return redirect(url_for('main.reservas'))

@main.route('/horas_disponibles', methods=['POST'])
def horas_disponibles():
    data = request.get_json()
    cancha_id = data.get("cancha_id")
    fecha_str = data.get("fecha")

    HORAS_TODAS = [
                   '14:00','15:00','16:00','17:00','18:00','19:00',
                   '20:00','21:00','22:00','23:00','00:00','01:00']
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify(HORAS_TODAS)  # si viene mal, devolver todo ocupado
    
    reservas = Reserva.query.filter_by(cancha_id=cancha_id, fecha=fecha).all()
    horas_ocupadas = {datetime.strptime(r.hora, "%H:%M").strftime("%H:%M") for r in reservas}


    # 🚫 Si todas las horas están ocupadas → devolver todas como ocupadas
    if len(horas_ocupadas) >= len(HORAS_TODAS):
        return jsonify(HORAS_TODAS)
    

    return jsonify(list(horas_ocupadas))

@main.route('/admin/editar_cancha/<int:id>', methods=['POST'])
def editar_cancha(id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('main.index'))

    cancha = Cancha.query.get_or_404(id)
    cancha.nombre = request.form['nombre']
    cancha.detalle = request.form['detalle']
    db.session.commit()
    flash('Cancha actualizada correctamente.')
    return redirect(url_for('main.admin'))

@main.route('/admin/usuarios_tbody')
def usuarios_tbody():
    
    usuarios = User.query.order_by(User.id.desc()).all()
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('partials/usuarios_tbody.html', usuarios=usuarios, user=user)


@main.route('/admin/reservas_tbody')
def admin_reservas_tbody():

    reservas_raw = Reserva.query.all()
    reservas = agrupar_reservas(reservas_raw)
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('partials/reservas_tbody.html', reservas=reservas, user=user)


@main.route('/admin/buscar_usuario')
def buscar_usuario():
    termino = request.args.get('termino', '').strip()
    if not termino:
        return jsonify({})

    usuario = User.query.filter(
        func.lower(func.concat(User.nombre, ' ', User.apellido)).like(f"%{termino.lower()}%")
    ).first()

    if usuario:
        return jsonify({
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'telefono': usuario.telefono,
            'email': usuario.email
        })

    return jsonify({})

@main.route('/agenda')
def agenda():
    return render_template('agenda.html')