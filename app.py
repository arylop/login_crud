from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "mi_clave_login_crud_2026"

# BASE DE DATOS
def conectar():
    conexion = sqlite3.connect("usuarios.db")
    conexion.row_factory = sqlite3.Row
    return conexion

def crear_tabla():
    conexion = conectar()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            contrasena TEXT NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()

crear_tabla()

# DISEÑO GENERAL Y CSS
BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login CRUD</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #eaf0f8;
    color: #263449;
    text-align: center;
}

header {
    background: #263f68;
    color: white;
    padding: 25px;
}

main {
    padding: 30px 15px;
    min-height: 70vh;
}

.tarjeta {
    background: white;
    width: 90%;
    max-width: 450px;
    margin: 20px auto;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 4px 15px #0002;
}

.grande {
    max-width: 900px;
}

h2 {
    color: #263f68;
}

label {
    display: block;
    text-align: left;
    margin-top: 15px;
}

input {
    width: 100%;
    padding: 12px;
    margin-top: 7px;
    border: 1px solid #b9c5d5;
    border-radius: 7px;
}

button, .boton {
    display: inline-block;
    background: #315c91;
    color: white;
    border: none;
    padding: 12px 18px;
    margin: 12px 5px;
    border-radius: 7px;
    text-decoration: none;
    cursor: pointer;
}

button:hover, .boton:hover {
    background: #193d6b;
}

.eliminar {
    background: #b43e48;
}

.salir {
    background: #a63c47;
}

a {
    color: #315c91;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

th, td {
    border: 1px solid #ccd5e0;
    padding: 10px;
}

th {
    background: #315c91;
    color: white;
}

.mensaje {
    background: #d8eddf;
    padding: 12px;
    margin: 10px auto;
    max-width: 450px;
    border-radius: 8px;
}

footer {
    background: #263f68;
    color: white;
    padding: 15px;
}

@media(max-width: 600px) {
    .grande {
        overflow-x: auto;
    }
    table {
        font-size: 12px;
    }
}
</style>
</head>

<body>
<header>
    <h1>LOGIN CRUD</h1>
    <p>Sistema de registro de usuarios</p>
</header>

<main>
    {% for mensaje in get_flashed_messages() %}
        <div class="mensaje">{{ mensaje }}</div>
    {% endfor %}

    {{ contenido|safe }}
</main>

<footer>
    Proyecto escolar - 2026
</footer>
</body>
</html>
"""

# FUNCION PARA MOSTRAR PANTALLAS
def mostrar(contenido):
    return render_template_string(BASE, contenido=contenido)

# PROTEGER SESION
def requiere_login(funcion):
    @wraps(funcion)
    def verificar(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return verificar

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        contrasena = request.form["contrasena"]

        conexion = conectar()
        usuario = conexion.execute(
            "SELECT * FROM usuarios WHERE nombre = ?",
            (nombre,)
        ).fetchone()
        conexion.close()

        if usuario and check_password_hash(
            usuario["contrasena"], contrasena
        ):
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            return redirect(url_for("bienvenida"))

        flash("Usuario o contraseña incorrectos")

    contenido = """
    <div class="tarjeta">
        <h2>Iniciar sesión</h2>

        <form method="POST">
            <label>Usuario:</label>
            <input type="text" name="nombre" required>

            <label>Contraseña:</label>
            <input type="password" name="contrasena" required>

            <button type="submit">ACCEDER</button>
        </form>

        <p>¿Eres nuevo usuario?</p>
        <a class="boton" href="/registro">Crear cuenta</a>
    </div>
    """
    return mostrar(contenido)

# ALTA DE USUARIO
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        correo = request.form["correo"].strip()
        contrasena = request.form["contrasena"]

        if not nombre or not correo or not contrasena:
            flash("Completa todos los campos")
            return redirect(url_for("registro"))

        conexion = conectar()

        try:
            clave = generate_password_hash(contrasena)

            conexion.execute("""
                INSERT INTO usuarios
                (nombre, correo, contrasena)
                VALUES (?, ?, ?)
            """, (nombre, correo, clave))

            conexion.commit()
            flash("Usuario agregado correctamente")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("El usuario o correo ya existe")

        finally:
            conexion.close()

    contenido = """
    <div class="tarjeta">
        <h2>Alta de usuario</h2>

        <form method="POST">
            <label>Nombre de usuario:</label>
            <input type="text" name="nombre" required>

            <label>Correo:</label>
            <input type="email" name="correo" required>

            <label>Contraseña:</label>
            <input type="password" name="contrasena" required>

            <button type="submit">AGREGAR USUARIO</button>
        </form>

        <a href="/">Regresar al login</a>
    </div>
    """
    return mostrar(contenido)

# BIENVENIDA
@app.route("/bienvenida")
@requiere_login
def bienvenida():

    contenido = """
    <div class="tarjeta">
        <h2>¡Bienvenido(a)!</h2>

        <h3>{{ nombre }}</h3>

        <p>Has iniciado sesión correctamente.</p>

        <a class="boton" href="/usuarios">
            Administrar usuarios
        </a>

        <a class="boton salir" href="/salir">
            Cerrar sesión
        </a>
    </div>
    """

    pagina = render_template_string(
        contenido,
        nombre=session["usuario_nombre"]
    )

    return mostrar(pagina)

# CONSULTAR USUARIOS (READ)
@app.route("/usuarios")
@requiere_login
def usuarios():

    conexion = conectar()
    lista = conexion.execute(
        "SELECT id, nombre, correo FROM usuarios"
    ).fetchall()
    conexion.close()

    contenido = """
    <div class="tarjeta grande">
        <h2>Administración de usuarios</h2>

        <a class="boton" href="/registro">
            Agregar usuario
        </a>

        <table>
            <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Correo</th>
                <th>Acciones</th>
            </tr>

            {% for usuario in usuarios %}
            <tr>
                <td>{{ usuario.id }}</td>
                <td>{{ usuario.nombre }}</td>
                <td>{{ usuario.correo }}</td>
                <td>
                    <a href="/editar/{{ usuario.id }}">
                        Editar
                    </a>

                    <form method="POST"
                    action="/eliminar/{{ usuario.id }}"
                    onsubmit="return confirm('¿Eliminar usuario?')">

                        <button class="eliminar">
                            Eliminar
                        </button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>

        <a href="/bienvenida">Regresar</a>
    </div>
    """

    pagina = render_template_string(
        contenido, usuarios=lista
    )

    return mostrar(pagina)

# ACTUALIZAR USUARIO (UPDATE)
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@requiere_login
def editar(id):

    conexion = conectar()

    usuario = conexion.execute(
        "SELECT * FROM usuarios WHERE id = ?", (id,)
    ).fetchone()

    if usuario is None:
        conexion.close()
        return "Usuario no encontrado", 404

    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        correo = request.form["correo"].strip()

        if not nombre or not correo:
            conexion.close()
            flash("Completa todos los campos")
            return redirect(url_for("editar", id=id))

        try:
            conexion.execute("""
                UPDATE usuarios
                SET nombre = ?, correo = ?
                WHERE id = ?
            """, (nombre, correo, id))

            conexion.commit()

            if session["usuario_id"] == id:
                session["usuario_nombre"] = nombre

            flash("Usuario actualizado correctamente")
            return redirect(url_for("usuarios"))

        except sqlite3.IntegrityError:
            flash("El nombre o correo ya existe")

        finally:
            conexion.close()

        return redirect(url_for("editar", id=id))

    conexion.close()

    contenido = """
    <div class="tarjeta">
        <h2>Actualizar usuario</h2>

        <form method="POST">
            <label>Nombre de usuario:</label>
            <input type="text" name="nombre"
                   value="{{ usuario.nombre }}" required>

            <label>Correo:</label>
            <input type="email" name="correo"
                   value="{{ usuario.correo }}" required>

            <button type="submit">GUARDAR CAMBIOS</button>
        </form>

        <a href="/usuarios">Cancelar</a>
    </div>
    """

    pagina = render_template_string(
        contenido, usuario=usuario
    )

    return mostrar(pagina)

# ELIMINAR USUARIO (DELETE)
@app.route("/eliminar/<int:id>", methods=["POST"])
@requiere_login
def eliminar(id):

    if session["usuario_id"] == id:
        flash("No puedes eliminar tu propia cuenta mientras estás conectado")
        return redirect(url_for("usuarios"))

    conexion = conectar()

    conexion.execute(
        "DELETE FROM usuarios WHERE id = ?", (id,)
    )

    conexion.commit()
    conexion.close()

    flash("Usuario eliminado correctamente")

    return redirect(url_for("usuarios"))

# CERRAR SESION
@app.route("/salir")
def salir():

    session.clear()

    return redirect(url_for("login"))

# EJECUTAR PROGRAMA
if __name__ == "__main__":
    app.run(debug=True)