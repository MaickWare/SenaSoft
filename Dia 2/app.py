from flask import Flask, render_template, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo_secret_key_2024'

# Datos de ejemplo (deben estar definidos antes de las rutas)
bicicletas_ejemplo = [
    {
        'id': 1,
        'modelo': 'Ruta 500',
        'marca': 'Trek',
        'tipo': 'carrera',
        'color': 'Rojo',
        'estado': 'disponible',
        'precio_hora': 5000,
        'imagen_url': '/static/images/bike1.jpg',
        'descripcion': 'Bicicleta de carrera profesional, ideal para competencias.',
        'latitud': 4.653332,
        'longitud': -74.083653,
        'direccion': 'Centro de Bogotá'
    },
    {
        'id': 2,
        'modelo': 'Montaña XC',
        'marca': 'Specialized',
        'tipo': 'montaña',
        'color': 'Verde',
        'estado': 'disponible',
        'precio_hora': 4500,
        'imagen_url': '/static/images/bike2.jpg',
        'descripcion': 'Bicicleta de montaña con suspensión delantera.',
        'latitud': 4.648283,
        'longitud': -74.107889,
        'direccion': 'Chapinero'
    },
    {
        'id': 3,
        'modelo': 'Urban 300',
        'marca': 'Giant',
        'tipo': 'urbana',
        'color': 'Azul',
        'estado': 'alquilada',
        'precio_hora': 3000,
        'imagen_url': '/static/images/bike3.jpg',
        'descripcion': 'Bicicleta urbana cómoda para la ciudad.',
        'latitud': 4.609710,
        'longitud': -74.081750,
        'direccion': 'Teusaquillo'
    },
    {
        'id': 4,
        'modelo': 'Híbrida Pro',
        'marca': 'Scott',
        'tipo': 'hibrida',
        'color': 'Negro',
        'estado': 'disponible',
        'precio_hora': 4000,
        'imagen_url': '/static/images/bike4.jpg',
        'descripcion': 'Bicicleta versátil para diferentes terrenos.',
        'latitud': 4.625277,
        'longitud': -74.069992,
        'direccion': 'Usaquén'
    }
]

usuarios_ejemplo = [
    {
        'id': 1,
        'nombre': 'Juan Pérez',
        'email': 'juan@ejemplo.com',
        'tipo': 'usuario',
        'telefono': '3124567890',
        'documento': '123456789'
    },
    {
        'id': 2,
        'nombre': 'Administrador SENA',
        'email': 'admin@sena.edu.co',
        'tipo': 'admin',
        'telefono': '3216549870',
        'documento': '987654321'
    }
]

alquileres_ejemplo = [
    {
        'id': 1,
        'usuario_id': 1,
        'bicicleta_id': 3,
        'fecha_inicio': '2024-01-15 10:30:00',
        'horas_alquiler': 3,
        'costo_total': 9000,
        'estado': 'activo'
    }
]

@app.route('/')
def index():
    return render_template('index.html', bicicletas=bicicletas_ejemplo[:4])

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/bicicletas')
def bicicletas():
    tipo_filtro = request.args.get('tipo', '')
    if tipo_filtro:
        bicicletas_filtradas = [b for b in bicicletas_ejemplo if b['tipo'] == tipo_filtro and b['estado'] == 'disponible']
    else:
        bicicletas_filtradas = [b for b in bicicletas_ejemplo if b['estado'] == 'disponible']
    
    return render_template('bicicletas.html', bicicletas=bicicletas_filtradas, tipo_filtro=tipo_filtro)

@app.route('/bicicleta/<int:id>')
def detalle_bicicleta(id):
    bicicleta = next((b for b in bicicletas_ejemplo if b['id'] == id), None)
    if not bicicleta:
        return render_template('404.html'), 404
    return render_template('detalle_bicicleta.html', bicicleta=bicicleta)

@app.route('/alquilar/<int:bicicleta_id>')
def alquilar_bicicleta(bicicleta_id):
    bicicleta = next((b for b in bicicletas_ejemplo if b['id'] == bicicleta_id), None)
    if not bicicleta:
        return render_template('404.html'), 404
    return render_template('alquilar.html', bicicleta=bicicleta)

@app.route('/mis-alquileres')
def mis_alquileres():
    return render_template('mis_alquileres.html', alquileres=alquileres_ejemplo)

@app.route('/perfil')
def perfil():
    usuario = usuarios_ejemplo[0]
    return render_template('perfil.html', usuario=usuario)

@app.route('/localizacion')
def localizacion():
    return render_template('localizacion.html', bicicletas=bicicletas_ejemplo)

@app.route('/admin')
def admin():
    total_bicicletas = len(bicicletas_ejemplo)
    bicicletas_disponibles = len([b for b in bicicletas_ejemplo if b['estado'] == 'disponible'])
    total_usuarios = len(usuarios_ejemplo)
    alquileres_activos = len([a for a in alquileres_ejemplo if a['estado'] == 'activo'])
    
    return render_template('admin/admin.html', 
                         total_bicicletas=total_bicicletas,
                         bicicletas_disponibles=bicicletas_disponibles,
                         total_usuarios=total_usuarios,
                         alquileres_activos=alquileres_activos)

@app.route('/admin/usuarios')
def admin_usuarios():
    return render_template('admin/admin_usuarios.html', usuarios=usuarios_ejemplo)

@app.route('/admin/bicicletas')
def admin_bicicletas():
    return render_template('admin/admin_bicicletas.html', bicicletas=bicicletas_ejemplo)

@app.route('/admin/alquileres')
def admin_alquileres():
    return render_template('admin/admin_alquileres.html', alquileres=alquileres_ejemplo)

@app.route('/reportes')
def reportes():
    ingresos_mensuales = 125000
    bicicletas_populares = [
        ('Trek', 'Ruta 500', 15),
        ('Specialized', 'Montaña XC', 12),
        ('Giant', 'Urban 300', 8),
        ('Scott', 'Híbrida Pro', 6)
    ]
    
    return render_template('reportes.html', 
                         ingresos_mensuales=ingresos_mensuales,
                         bicicletas_populares=bicicletas_populares)

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_servidor(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)