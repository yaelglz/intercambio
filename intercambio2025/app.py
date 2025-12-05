from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Usuario, Regalo, Mensaje
import random
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui-cambiar-en-produccion'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///intercambio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Jefes de familia permitidos
JEFES_FAMILIA = ['Fátima', 'Conka', 'María', 'Guadalupe', 'Lourdes', 'Mónica', 'Beatriz', 'Martín', 'Pablo']

# Opciones de navidad en Tepoztlán
NAVIDAD_TEPOZTLAN_OPCIONES = ['Sí', 'No']

@app.route('/')
def index():
    """Página principal - Registro de usuarios"""
    return render_template('index.html', jefes_familia=JEFES_FAMILIA, navidad_tepoztlan_opciones=NAVIDAD_TEPOZTLAN_OPCIONES)

@app.route('/registro', methods=['POST'])
def registro():
    """Registra un nuevo usuario"""
    nombre = request.form.get('nombre', '').strip()
    presupuesto_min = request.form.get('presupuesto_min', '')
    presupuesto_max = request.form.get('presupuesto_max', '')
    jefe_familia = request.form.get('jefe_familia', '')
    navidad_tepoztlan = request.form.get('navidad_tepoztlan', '')
    
    # Validaciones
    if not nombre:
        flash('Por favor ingresa tu nombre', 'error')
        return redirect(url_for('index'))
    
    if not presupuesto_min or not presupuesto_max:
        flash('Por favor ingresa el rango de presupuesto', 'error')
        return redirect(url_for('index'))
    
    try:
        presupuesto_min = float(presupuesto_min)
        presupuesto_max = float(presupuesto_max)
    except ValueError:
        flash('El presupuesto debe ser un número válido', 'error')
        return redirect(url_for('index'))
    
    if presupuesto_min >= presupuesto_max:
        flash('El presupuesto mínimo debe ser menor al máximo', 'error')
        return redirect(url_for('index'))
    
    if jefe_familia not in JEFES_FAMILIA:
        flash('Por favor selecciona un jefe de familia válido', 'error')
        return redirect(url_for('index'))
    
    if navidad_tepoztlan not in NAVIDAD_TEPOZTLAN_OPCIONES:
        flash('Por favor responde si pasarás Navidad en Tepoztlán', 'error')
        return redirect(url_for('index'))
    
    # Verificar si el usuario ya existe
    usuario_existente = Usuario.query.filter_by(nombre=nombre).first()
    if usuario_existente:
        flash(f'El usuario {nombre} ya está registrado. Usa otro nombre o consulta tu información.', 'error')
        return redirect(url_for('index'))
    
    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        nombre=nombre,
        presupuesto_min=presupuesto_min,
        presupuesto_max=presupuesto_max,
        jefe_familia=jefe_familia,
        navidad_tepoztlan=navidad_tepoztlan
    )
    
    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        session['usuario_id'] = nuevo_usuario.id
        flash(f'¡Registro exitoso, {nombre}!', 'success')
        return redirect(url_for('ver_santa'))
    except Exception as e:
        db.session.rollback()
        flash('Error al registrar usuario. Intenta nuevamente.', 'error')
        return redirect(url_for('index'))

@app.route('/sorteo')
def sorteo():
    """Página para realizar el sorteo"""
    usuarios = Usuario.query.all()
    usuarios_sin_santa = [u for u in usuarios if u.santa_claus_id is None]
    usuarios_con_santa = [u for u in usuarios if u.santa_claus_id is not None]
    
    return render_template('sorteo.html', 
                         usuarios=usuarios, 
                         usuarios_sin_santa=usuarios_sin_santa,
                         usuarios_con_santa=usuarios_con_santa)

@app.route('/realizar_sorteo', methods=['POST'])
def realizar_sorteo():
    """Realiza el sorteo respetando las restricciones usando algoritmo de emparejamiento"""
    usuarios = Usuario.query.all()
    
    if len(usuarios) < 2:
        flash('Se necesitan al menos 2 usuarios para realizar el sorteo', 'error')
        return redirect(url_for('sorteo'))
    
    # Limpiar asignaciones anteriores
    for usuario in usuarios:
        usuario.santa_claus_id = None
    db.session.commit()
    
    # Verificar que es posible realizar el sorteo
    # Cada usuario debe tener al menos un candidato válido
    for usuario in usuarios:
        candidatos_posibles = [u for u in usuarios 
                              if u.id != usuario.id 
                              and u.jefe_familia != usuario.jefe_familia]
        if not candidatos_posibles:
            flash(f'Error: No se puede realizar el sorteo. El usuario {usuario.nombre} no tiene candidatos válidos (todos tienen el mismo jefe de familia).', 'error')
            return redirect(url_for('sorteo'))
    
    # Algoritmo mejorado: crear matriz de candidatos y usar backtracking
    def encontrar_asignacion(usuarios_list, asignaciones_actuales, indice):
        """Función recursiva para encontrar una asignación válida"""
        if indice >= len(usuarios_list):
            return True
        
        usuario_actual = usuarios_list[indice]
        # Obtener candidatos válidos que no estén ya asignados
        candidatos = [u for u in usuarios_list 
                     if u.id != usuario_actual.id 
                     and u.jefe_familia != usuario_actual.jefe_familia
                     and u.id not in asignaciones_actuales.values()]
        
        # Mezclar candidatos para aleatoriedad
        random.shuffle(candidatos)
        
        for candidato in candidatos:
            asignaciones_actuales[usuario_actual.id] = candidato.id
            if encontrar_asignacion(usuarios_list, asignaciones_actuales, indice + 1):
                return True
            # Backtrack
            del asignaciones_actuales[usuario_actual.id]
        
        return False
    
    # Intentar encontrar una asignación válida (máximo 100 intentos)
    asignaciones = {}
    exito = False
    for intento in range(100):
        usuarios_mezclados = usuarios.copy()
        random.shuffle(usuarios_mezclados)
        asignaciones = {}
        if encontrar_asignacion(usuarios_mezclados, asignaciones, 0):
            exito = True
            break
    
    if not exito:
        flash('Error: No se pudo realizar el sorteo después de múltiples intentos. Verifica que haya suficientes usuarios de diferentes jefes de familia.', 'error')
        return redirect(url_for('sorteo'))
    
    # Asignar
    for usuario_id, santa_id in asignaciones.items():
        usuario = Usuario.query.get(usuario_id)
        usuario.santa_claus_id = santa_id
    
    try:
        db.session.commit()
        flash('¡Sorteo realizado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al realizar el sorteo. Intenta nuevamente.', 'error')
    
    return redirect(url_for('sorteo'))

@app.route('/ver_santa')
def ver_santa():
    """Página para que el usuario vea su Santa Claus y proponga regalos"""
    usuario_id = session.get('usuario_id')
    nombre = request.args.get('nombre', '').strip()
    
    # Si hay nombre en la URL, buscar usuario
    if nombre and not usuario_id:
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario:
            usuario_id = usuario.id
            session['usuario_id'] = usuario_id
    
    if not usuario_id:
        return render_template('buscar_usuario.html')
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('index'))
    
    # Obtener Santa Claus
    santa_claus = None
    if usuario.santa_claus_id:
        santa_claus = Usuario.query.get(usuario.santa_claus_id)
    
    # Verificar si ya propuso regalos
    regalos = Regalo.query.filter_by(usuario_id=usuario_id).first()
    
    # Obtener mensajes del Santa Claus (remitente) al usuario (destinatario)
    mensajes_santa = []
    if santa_claus:
        mensajes_santa = Mensaje.query.filter_by(
            remitente_id=santa_claus.id,
            destinatario_id=usuario_id
        ).order_by(Mensaje.fecha_envio.desc()).all()
        # Marcar mensajes como leídos
        for mensaje in mensajes_santa:
            if not mensaje.leido:
                mensaje.leido = True
        db.session.commit()
    
    # Obtener mensajes del usuario (remitente) al Santa Claus (destinatario)
    mensajes_usuario = []
    if santa_claus:
        mensajes_usuario = Mensaje.query.filter_by(
            remitente_id=usuario_id,
            destinatario_id=santa_claus.id
        ).order_by(Mensaje.fecha_envio.desc()).all()
    
    return render_template('ver_santa.html', 
                         usuario=usuario, 
                         santa_claus=santa_claus,
                         regalos=regalos,
                         mensajes_santa=mensajes_santa,
                         mensajes_usuario=mensajes_usuario)

@app.route('/buscar_usuario', methods=['POST'])
def buscar_usuario():
    """Busca un usuario por nombre"""
    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        flash('Por favor ingresa tu nombre', 'error')
        return redirect(url_for('ver_santa'))
    
    usuario = Usuario.query.filter_by(nombre=nombre).first()
    if not usuario:
        flash('Usuario no encontrado. Verifica tu nombre.', 'error')
        return redirect(url_for('ver_santa'))
    
    session['usuario_id'] = usuario.id
    return redirect(url_for('ver_santa'))

@app.route('/proponer_regalos', methods=['POST'])
def proponer_regalos():
    """Guarda las 3 opciones de regalo del usuario"""
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        flash('Por favor inicia sesión primero', 'error')
        return redirect(url_for('ver_santa'))
    
    opcion1 = request.form.get('opcion1', '').strip()
    opcion2 = request.form.get('opcion2', '').strip()
    opcion3 = request.form.get('opcion3', '').strip()
    
    if not opcion1 or not opcion2 or not opcion3:
        flash('Por favor completa las 3 opciones de regalo', 'error')
        return redirect(url_for('ver_santa'))
    
    # Verificar si ya existe
    regalo_existente = Regalo.query.filter_by(usuario_id=usuario_id).first()
    if regalo_existente:
        # Actualizar
        regalo_existente.opcion1 = opcion1
        regalo_existente.opcion2 = opcion2
        regalo_existente.opcion3 = opcion3
    else:
        # Crear nuevo
        nuevo_regalo = Regalo(
            usuario_id=usuario_id,
            opcion1=opcion1,
            opcion2=opcion2,
            opcion3=opcion3
        )
        db.session.add(nuevo_regalo)
    
    try:
        db.session.commit()
        flash('¡Opciones de regalo guardadas exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al guardar las opciones. Intenta nuevamente.', 'error')
    
    return redirect(url_for('ver_santa'))

@app.route('/ver_regalos')
def ver_regalos():
    """Página para que el Santa Claus vea las opciones de regalo"""
    usuario_id = session.get('usuario_id')
    nombre = request.args.get('nombre', '').strip()
    
    # Si hay nombre en la URL, buscar usuario
    if nombre and not usuario_id:
        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario:
            usuario_id = usuario.id
            session['usuario_id'] = usuario_id
    
    if not usuario_id:
        return render_template('buscar_santa.html')
    
    santa_claus = Usuario.query.get(usuario_id)
    if not santa_claus:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('index'))
    
    # Buscar usuarios que tienen a este usuario como Santa Claus
    usuarios_asignados = Usuario.query.filter_by(santa_claus_id=usuario_id).all()
    
    # Obtener regalos y mensajes de cada usuario asignado
    usuarios_con_regalos = []
    for usuario in usuarios_asignados:
        regalos = Regalo.query.filter_by(usuario_id=usuario.id).first()
        
        # Obtener mensajes del Santa Claus al usuario
        mensajes_santa = Mensaje.query.filter_by(
            remitente_id=usuario_id,
            destinatario_id=usuario.id
        ).order_by(Mensaje.fecha_envio.desc()).all()
        
        # Obtener mensajes del usuario al Santa Claus
        mensajes_usuario = Mensaje.query.filter_by(
            remitente_id=usuario.id,
            destinatario_id=usuario_id
        ).order_by(Mensaje.fecha_envio.desc()).all()
        
        usuarios_con_regalos.append({
            'usuario': usuario,
            'regalos': regalos,
            'mostrar_nombre': usuario.navidad_tepoztlan == 'No',  # Mostrar nombre si NO pasa Navidad en Tepoztlán
            'mensajes_santa': mensajes_santa,
            'mensajes_usuario': mensajes_usuario
        })
    
    return render_template('ver_regalos.html', 
                         santa_claus=santa_claus,
                         usuarios_con_regalos=usuarios_con_regalos)

@app.route('/buscar_santa', methods=['POST'])
def buscar_santa():
    """Busca un Santa Claus por nombre"""
    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        flash('Por favor ingresa tu nombre', 'error')
        return redirect(url_for('ver_regalos'))
    
    usuario = Usuario.query.filter_by(nombre=nombre).first()
    if not usuario:
        flash('Usuario no encontrado. Verifica tu nombre.', 'error')
        return redirect(url_for('ver_regalos'))
    
    session['usuario_id'] = usuario.id
    return redirect(url_for('ver_regalos'))

@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    """Envía un mensaje anónimo entre Santa Claus y su asignado"""
    remitente_id = session.get('usuario_id')
    if not remitente_id:
        flash('Por favor inicia sesión primero', 'error')
        return redirect(url_for('index'))
    
    destinatario_id = request.form.get('destinatario_id', '')
    mensaje_texto = request.form.get('mensaje', '').strip()
    
    if not destinatario_id:
        flash('Error: destinatario no especificado', 'error')
        return redirect(url_for('ver_regalos'))
    
    try:
        destinatario_id = int(destinatario_id)
    except ValueError:
        flash('Error: destinatario inválido', 'error')
        return redirect(url_for('ver_regalos'))
    
    if not mensaje_texto:
        flash('Por favor escribe un mensaje', 'error')
        return redirect(url_for('ver_regalos'))
    
    # Verificar que el remitente y destinatario están relacionados (Santa-asignado)
    remitente = Usuario.query.get(remitente_id)
    destinatario = Usuario.query.get(destinatario_id)
    
    if not remitente or not destinatario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('ver_regalos'))
    
    # Verificar relación: remitente es Santa del destinatario O destinatario es Santa del remitente
    relacion_valida = (destinatario.santa_claus_id == remitente_id) or (remitente.santa_claus_id == destinatario_id)
    
    if not relacion_valida:
        flash('No puedes enviar mensajes a este usuario', 'error')
        return redirect(url_for('ver_regalos'))
    
    # Crear mensaje
    nuevo_mensaje = Mensaje(
        remitente_id=remitente_id,
        destinatario_id=destinatario_id,
        mensaje=mensaje_texto
    )
    
    try:
        db.session.add(nuevo_mensaje)
        db.session.commit()
        flash('¡Mensaje enviado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al enviar el mensaje. Intenta nuevamente.', 'error')
    
    # Redirigir según desde dónde se envió
    if destinatario.santa_claus_id == remitente_id:
        # Remitente es Santa, redirigir a ver_regalos
        return redirect(url_for('ver_regalos'))
    elif remitente.santa_claus_id == destinatario_id:
        # Remitente es asignado, redirigir a ver_santa
        return redirect(url_for('ver_santa'))
    else:
        # Fallback: redirigir según el remitente
        return redirect(url_for('ver_regalos'))

@app.route('/limpiar_sorteo', methods=['POST'])
def limpiar_sorteo():
    """Limpia todas las asignaciones del sorteo"""
    usuarios = Usuario.query.all()
    for usuario in usuarios:
        usuario.santa_claus_id = None
    db.session.commit()
    flash('Sorteo limpiado exitosamente', 'success')
    return redirect(url_for('sorteo'))

@app.route('/eliminar_usuario/<int:usuario_id>', methods=['POST'])
def eliminar_usuario(usuario_id):
    """Elimina un usuario del intercambio"""
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('sorteo'))
    
    nombre_usuario = usuario.nombre
    
    # Limpiar referencias de santa_claus_id que apuntan a este usuario
    usuarios_con_santa = Usuario.query.filter_by(santa_claus_id=usuario_id).all()
    for u in usuarios_con_santa:
        u.santa_claus_id = None
    
    # Los regalos se eliminarán automáticamente por cascade
    # Eliminar el usuario
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuario {nombre_usuario} eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el usuario. Intenta nuevamente.', 'error')
    
    return redirect(url_for('sorteo'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

