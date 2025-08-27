from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bicicletas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'demo_secret_key_2024'

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default='usuario')  
    telefono = db.Column(db.String(15))
    documento = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    alquileres = db.relationship('Alquiler', backref='usuario', lazy=True)
    eventos_participantes = db.relationship('Participante', backref='usuario', lazy=True)

class Bicicleta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)    
    color = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='disponible')
    precio_hora = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(200), default='/static/images/bike-default.jpg')
    descripcion = db.Column(db.Text)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    direccion = db.Column(db.String(200))
    
    alquileres = db.relationship('Alquiler', backref='bicicleta', lazy=True)

class Alquiler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    bicicleta_id = db.Column(db.Integer, db.ForeignKey('bicicleta.id'), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime)
    horas_alquiler = db.Column(db.Integer, nullable=False)
    costo_total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='activo')

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    lugar = db.Column(db.String(100), nullable=False)
    participantes = db.relationship('Participante', backref='evento', lazy=True)

class Participante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=False)

@app.route('/')
def index():
    bicicletas = Bicicleta.query.filter_by(estado='disponible').limit(4).all()
    return render_template('index.html', bicicletas=bicicletas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.password, password):
            session['user_id'] = usuario.id
            session['user_nombre'] = usuario.nombre
            session['user_tipo'] = usuario.tipo
            
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        telefono = request.form.get('telefono')
        documento = request.form.get('documento')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('register'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password=hashed_password,
            telefono=telefono,
            documento=documento
        )
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Registro exitoso. Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/bicicletas')
def bicicletas():
    tipo_filtro = request.args.get('tipo', '')
    if tipo_filtro:
        bicicletas = Bicicleta.query.filter_by(tipo=tipo_filtro, estado='disponible').all()
    else:
        bicicletas = Bicicleta.query.filter_by(estado='disponible').all()
    
    return render_template('bicicletas.html', bicicletas=bicicletas, tipo_filtro=tipo_filtro)

@app.route('/reportes')
def reportes():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))
    
    total_bicicletas = Bicicleta.query.count()
    bicicletas_disponibles = Bicicleta.query.filter_by(estado='disponible').count()
    total_usuarios = Usuario.query.count()
    alquileres_activos = Alquiler.query.filter_by(estado='activo').count()
    
    primer_dia_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ingresos_mensuales_query = db.session.query(db.func.sum(Alquiler.costo_total)).filter(
        Alquiler.fecha_fin >= primer_dia_mes,
        Alquiler.estado == 'finalizado'
    ).scalar()
    ingresos_mensuales = ingresos_mensuales_query if ingresos_mensuales_query else 0

    bicicletas_populares_query = db.session.query(
        Bicicleta.marca,
        Bicicleta.modelo,
        db.func.count(Alquiler.bicicleta_id).label('veces_alquilada')
    ).join(Alquiler).group_by(Bicicleta.id).order_by(db.desc('veces_alquilada')).limit(5).all()
    
    return render_template('reportes.html', 
                         total_bicicletas=total_bicicletas,
                         bicicletas_disponibles=bicicletas_disponibles,
                         total_usuarios=total_usuarios,
                         alquileres_activos=alquileres_activos,
                         ingresos_mensuales=ingresos_mensuales,
                         bicicletas_populares=bicicletas_populares_query)

@app.route('/bicicleta/<int:id>')
def detalle_bicicleta(id):
    bicicleta = Bicicleta.query.get_or_404(id)
    return render_template('detalle_bicicleta.html', bicicleta=bicicleta)

@app.route('/alquilar/<int:bicicleta_id>', methods=['GET', 'POST'])
def alquilar(bicicleta_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para alquilar una bicicleta', 'warning')
        return redirect(url_for('login'))
    
    bicicleta = Bicicleta.query.get_or_404(bicicleta_id)
    
    if bicicleta.estado != 'disponible':
        flash('Esta bicicleta no está disponible para alquiler', 'danger')
        return redirect(url_for('bicicletas'))
    
    if request.method == 'POST':
        horas = int(request.form.get('horas'))
        
        costo_total = bicicleta.precio_hora * horas
    
        nuevo_alquiler = Alquiler(
            usuario_id=session['user_id'],
            bicicleta_id=bicicleta_id,
            horas_alquiler=horas,
            costo_total=costo_total,
            fecha_fin=datetime.utcnow() + timedelta(hhours=horas)
        )
        
        bicicleta.estado = 'alquilada'
        
        db.session.add(nuevo_alquiler)
        db.session.commit()
        
        flash(f'Alquiler realizado con éxito. Costo total: ${costo_total:.2f}', 'success')
        return redirect(url_for('mis_alquileres'))
    
    return render_template('alquilar.html', bicicleta=bicicleta)

@app.route('/mis-alquileres')
def mis_alquileres():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver sus alquileres', 'warning')
        return redirect(url_for('login'))
    
    alquileres = Alquiler.query.filter_by(usuario_id=session['user_id']).order_by(Alquiler.fecha_inicio.desc()).all()
    return render_template('mis_alquileres.html', alquileres=alquileres)

@app.route('/api/finalizar-alquiler/<int:alquiler_id>', methods=['POST'])
def finalizar_alquiler_api(alquiler_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    alquiler = Alquiler.query.get(alquiler_id)
    if not alquiler:
        return jsonify({'error': 'Alquiler no encontrado'}), 404

    if alquiler.usuario_id != session['user_id'] and session.get('user_tipo') != 'admin':
        return jsonify({'error': 'No tiene permisos para finalizar este alquiler'}), 403

    if alquiler.estado == 'activo':
        alquiler.estado = 'finalizado'
        alquiler.fecha_fin = datetime.utcnow()
        
        bicicleta = Bicicleta.query.get(alquiler.bicicleta_id)
        if bicicleta:
            bicicleta.estado = 'disponible'
        
        db.session.commit()
        return jsonify({'message': 'Alquiler finalizado con éxito'}), 200
    else:
        return jsonify({'error': 'El alquiler ya ha sido finalizado o no está activo'}), 400

@app.route('/localizacion')
def localizacion():
    bicicletas = Bicicleta.query.filter_by(estado='disponible').all()
    bicicletas_data = [
        {
            'id': bici.id,
            'modelo': bici.modelo,
            'marca': bici.marca,
            'tipo': bici.tipo,
            'latitud': bici.latitud,
            'longitud': bici.longitud,
            'direccion': bici.direccion,
            'estado': bici.estado
        } for bici in bicicletas if bici.latitud and bici.longitud
    ]
    return render_template('localizacion.html', bicicletas=bicicletas_data)

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        flash('Debe iniciar sesión para ver su perfil', 'warning')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['user_id'])
    return render_template('perfil.html', usuario=usuario)

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))
    
    total_bicicletas = Bicicleta.query.count()
    bicicletas_disponibles = Bicicleta.query.filter_by(estado='disponible').count()
    total_usuarios = Usuario.query.count()
    alquileres_activos = Alquiler.query.filter_by(estado='activo').count()
    
    return render_template('admin/admin.html', 
                         total_bicicletas=total_bicicletas,
                         bicicletas_disponibles=bicicletas_disponibles,
                         total_usuarios=total_usuarios,
                         alquileres_activos=alquileres_activos)

@app.route('/admin/bicicletas')
def admin_bicicletas():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))
    
    bicicletas = Bicicleta.query.all()
    return render_template('admin/admin_bicicletas.html', bicicletas=bicicletas)

@app.route('/admin/usuarios')
def admin_usuarios():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))
    
    usuarios = Usuario.query.all()
    return render_template('admin/admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/alquileres')
def admin_alquileres():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))
    
    alquileres = Alquiler.query.order_by(Alquiler.fecha_inicio.desc()).all()
    return render_template('admin/admin_alquileres.html', alquileres=alquileres)

@app.route('/admin/bicicletas/nueva', methods=['GET', 'POST'])
def nueva_bicicleta():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        modelo = request.form.get('modelo')
        marca = request.form.get('marca')
        tipo = request.form.get('tipo')
        color = request.form.get('color')
        precio_hora = float(request.form.get('precio_hora'))
        descripcion = request.form.get('descripcion')
        latitud = request.form.get('latitud')
        longitud = request.form.get('longitud')
        direccion = request.form.get('direccion')
        imagen_url = request.form.get('imagen_url')

        nueva_bici = Bicicleta(
            modelo=modelo,
            marca=marca,
            tipo=tipo,
            color=color,
            precio_hora=precio_hora,
            descripcion=descripcion,
            latitud=latitud,
            longitud=longitud,
            direccion=direccion,
            imagen_url=imagen_url
        )

        db.session.add(nueva_bici)
        db.session.commit()
        flash('Bicicleta creada exitosamente', 'success')
        return redirect(url_for('admin_bicicletas'))

    return render_template('admin/nueva_bicicleta.html')

@app.route('/admin/bicicletas/editar/<int:id>', methods=['GET', 'POST'])
def editar_bicicleta(id):
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    bicicleta = Bicicleta.query.get_or_404(id)

    if request.method == 'POST':
        bicicleta.modelo = request.form.get('modelo')
        bicicleta.marca = request.form.get('marca')
        bicicleta.tipo = request.form.get('tipo')
        bicicleta.color = request.form.get('color')
        bicicleta.precio_hora = float(request.form.get('precio_hora'))
        bicicleta.descripcion = request.form.get('descripcion')
        bicicleta.latitud = request.form.get('latitud')
        bicicleta.longitud = request.form.get('longitud')
        bicicleta.direccion = request.form.get('direccion')
        bicicleta.imagen_url = request.form.get('imagen_url')

        db.session.commit()
        flash('Bicicleta actualizada exitosamente', 'success')
        return redirect(url_for('admin_bicicletas'))

    return render_template('admin/editar_bicicleta.html', bicicleta=bicicleta)

@app.route('/admin/bicicletas/eliminar/<int:id>', methods=['POST'])
def eliminar_bicicleta(id):
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    bicicleta = Bicicleta.query.get_or_404(id)
    db.session.delete(bicicleta)
    db.session.commit()
    flash('Bicicleta eliminada exitosamente', 'success')
    return redirect(url_for('admin_bicicletas'))

@app.route('/admin/eventos/nuevo', methods=['GET', 'POST'])
def nuevo_evento():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        fecha = request.form.get('fecha')
        lugar = request.form.get('lugar')

        nuevo_evento = Evento(
            titulo=titulo,
            descripcion=descripcion,
            fecha=datetime.strptime(fecha, '%Y-%m-%dT%H:%M'),
            lugar=lugar
        )

        db.session.add(nuevo_evento)
        db.session.commit()
        flash('Evento creado exitosamente', 'success')
        return redirect(url_for('admin_eventos'))

    return render_template('admin/nuevo_evento.html')

@app.route('/admin/eventos')
def admin_eventos():
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    eventos = Evento.query.all()
    return render_template('admin/eventos.html', eventos=eventos)

@app.route('/admin/eventos/eliminar/<int:id>', methods=['POST'])
def eliminar_evento(id):
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        flash('Acceso restringido. Se requieren permisos de administrador.', 'danger')
        return redirect(url_for('index'))

    evento = Evento.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento eliminado exitosamente', 'success')
    return redirect(url_for('admin/eventos.html'))

@app.route('/eventos')
def lista_eventos():
    eventos = Evento.query.all()
    return render_template('eventos.html', eventos=eventos)

@app.route('/eventos/registrar/<int:evento_id>', methods=['POST'])
def registrar_evento(evento_id):
    if 'user_id' not in session:
        flash('Debe iniciar sesión para registrarse en un evento', 'warning')
        return redirect(url_for('login'))

    # Verificar si ya está registrado
    if Participante.query.filter_by(usuario_id=session['user_id'], evento_id=evento_id).first():
        flash('Ya estás registrado en este evento', 'info')
        return redirect(url_for('lista_eventos'))

    nuevo_participante = Participante(
        usuario_id=session['user_id'],
        evento_id=evento_id
    )

    db.session.add(nuevo_participante)
    db.session.commit()
    flash('Te has registrado exitosamente en el evento', 'success')
    return redirect(url_for('lista_eventos'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Usuario.query.filter_by(email='admin@sena.edu.co').first():
            admin_user = Usuario(
                nombre='Administrador SENA',
                email='admin@sena.edu.co',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                tipo='admin',
                telefono='1234567890',
                documento='123456789'
            )
            db.session.add(admin_user)
        
        if Bicicleta.query.count() == 0:
            bicicletas_ejemplo = [
                Bicicleta(
                    modelo='Ruta 500',
                    marca='Trek',
                    tipo='carrera',
                    color='Rojo',
                    precio_hora=5000,
                    descripcion='Bicicleta de carrera profesional, ideal para competencias y entrenamiento.',
                    latitud='4.625277',
                    longitud='-74.069992',
                    direccion='Usaquén',
                    imagen_url='/static/images/bike1.png'
                ),
                Bicicleta(
                    modelo='Montaña XC',
                    marca='Specialized',
                    tipo='montaña',
                    color='Verde',
                    precio_hora=4500,
                    descripcion='Bicicleta de montaña con suspensión delantera, perfecta para senderos.',
                    latitud='4.625277',
                    longitud='-74.069992',
                    direccion='Usaquén',
                    imagen_url='/static/images/bike2.png'
                ),
                Bicicleta(
                    modelo='Urban 300',
                    marca='Giant',
                    tipo='urbana',
                    color='Azul',
                    precio_hora=3000,
                    descripcion='Bicicleta urbana cómoda para desplazamientos en la ciudad.',
                    latitud='4.625277',
                    longitud='-74.069992',
                    direccion='Usaquén',
                    imagem_url='/static/images/bike3.png'
                ),
                Bicicleta(
                    modelo='Híbrida Pro',
                    marca='Scott',
                    tipo='hibrida',
                    color='Negro',
                    precio_hora=4000,
                    descripcion='Bicicleta híbrida versátil para diferentes tipos de terreno.',
                    latitud='4.625277',
                    longitud='-74.069992',
                    direccion='Usaquén',
                    imagem_url='/static/images/bike4.png'
                )
            ]
            
            for bicicleta in bicicletas_ejemplo:
                db.session.add(bicicleta)
    
        db.session.commit()

    app.run(debug=True)
