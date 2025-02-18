from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
from flaskext.mysql import MySQL
from datetime import datetime
import qrcode
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = "neocelasio"

# Conexión a la base de datos
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'testcrud'
mysql.init_app(app)

# Configuración de carpetas
folder = os.path.join('uploads')
app.config['folder'] = folder

@app.route('/uploads/<picturename>')
def uploads(picturename):
    return send_from_directory(app.config['folder'], picturename)

# Ruta principal
@app.route('/')
def index():
    sql = "SELECT * FROM `usuarios`;"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    usuarios = cursor.fetchall()
    conn.commit()
    return render_template('usuarios/index.html', usuarios=usuarios)

# Eliminar usuario
@app.route('/destroy/<int:id>')
def destroy(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT foto FROM usuarios WHERE id=%s", (id,))
    fila = cursor.fetchall()
    if fila:
        os.remove(os.path.join(app.config['folder'], fila[0][0]))
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conn.commit()
    return redirect('/')

# Editar usuario
@app.route('/edit/<int:id>')
def edit(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (id,))
    usuarios = cursor.fetchall()
    conn.commit()
    return render_template('usuarios/edit.html', usuarios=usuarios)

@app.route('/update', methods=['POST'])
def update():
    _name = request.form['name']
    _lastname = request.form['lastname']
    _mail = request.form['mail']
    _telefono = request.form['telefono']
    _fecha_inicio = request.form['fecha_inicio']
    _fecha_fin = request.form['fecha_fin']
    _fecha_renovacion = request.form['fecha_renovacion']
    _picture = request.files['picture']
    id = request.form['ID']

    sql = """
        UPDATE `usuarios` 
        SET nombre=%s, apellido=%s, correo=%s, telefono=%s, fecha_inicio=%s, fecha_fin=%s, fecha_renovacion=%s 
        WHERE ID=%s;
    """
    datos = (_name, _lastname, _mail, _telefono, _fecha_inicio, _fecha_fin, _fecha_renovacion, id)
    conn = mysql.connect()
    cursor = conn.cursor()

    now = datetime.now()
    time = now.strftime("%Y%H%M%S")

    if _picture.filename != '':
        newNamePicture = time + _picture.filename
        _picture.save("uploads/" + newNamePicture)
        cursor.execute("SELECT foto FROM usuarios WHERE id=%s", (id,))
        fila = cursor.fetchall()
        os.remove(os.path.join(app.config['folder'], fila[0][0]))
        cursor.execute("UPDATE usuarios SET foto=%s WHERE id=%s", (newNamePicture, id))
        conn.commit()

    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/')

# Crear usuario
@app.route('/create')
def create():
    return render_template('usuarios/create.html')

@app.route('/store', methods=['POST'])
def storage():
    _name = request.form['name']
    _lastname = request.form['lastname']
    _mail = request.form['mail']
    _telefono = request.form['telefono']
    _fecha_inicio = request.form['fecha_inicio']
    _fecha_fin = request.form['fecha_fin']
    _fecha_renovacion = request.form['fecha_renovacion']
    _picture = request.files['picture']

    if not all([_name, _lastname, _mail, _telefono, _fecha_inicio, _fecha_fin, _fecha_renovacion, _picture]):
        flash('Recuerda llenar todos los campos')
        return redirect(url_for('create'))

    now = datetime.now()
    time = now.strftime("%Y%H%M%S")

    if _picture.filename != '':
        newNamePicture = time + _picture.filename
        _picture.save("uploads/" + newNamePicture)

    sql = """
        INSERT INTO `usuarios` (`id`, `nombre`, `apellido`, `correo`, `telefono`, `foto`, `fecha_inicio`, `fecha_fin`, `fecha_renovacion`) 
        VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    datos = (_name, _lastname, _mail, _telefono, newNamePicture, _fecha_inicio, _fecha_fin, _fecha_renovacion)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/')

# Generar QR para un usuario
# Generar QR para un usuario
@app.route('/generate_qr/<int:id>')
def generate_qr(id):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Solo obtenemos los campos necesarios para el QR
    cursor.execute("SELECT id, fecha_inicio, fecha_fin, fecha_renovacion FROM usuarios WHERE id=%s", (id,))
    usuario = cursor.fetchone()
    conn.commit()

    if not usuario:
        flash("Usuario no encontrado")
        return redirect('/')

    # Crear el QR con los datos seleccionados
    info_qr = (
        f"ID: {usuario[0]}\n"
        f"Fecha de Inicio: {usuario[1]}\n"
        f"Fecha de Fin: {usuario[2]}\n"
        f"Fecha de Renovación: {usuario[3]}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(info_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    byte_io = BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)

    # Enviar la imagen QR al cliente
    return send_file(
        byte_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'qr_usuario_{id}.png'
    )


if __name__ == '__main__':
    app.run(debug=True)
