from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path

# -------------------------------------------------------------------
# CONFIGURACIÓN DE FLASK
# -------------------------------------------------------------------
app = Flask(__name__)

# La clave se usa para guardar el carrito en la sesión del navegador.
# En producción conviene ponerla en una variable de entorno.
app.config["SECRET_KEY"] = "between-friends-clave-cambiar-en-produccion"

# La base queda junto a app.py, por lo que funciona aunque ejecutes
# Flask desde otra carpeta.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "BaseDatosMateo (otra copia).db"


# -------------------------------------------------------------------
# FUNCIONES PARA LA BASE DE DATOS
# -------------------------------------------------------------------
def get_db():
    """Abre una conexión SQLite y permite acceder a las columnas por nombre."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Comprueba que existan las tablas que necesita la aplicación.

    La base que recibimos ya tiene cliente, productos y pedido(relacion).
    También agregamos categoria y descripcion a productos si todavía no
    existen. Esto permite que Comidas/Postres/Bebidas puedan filtrarse
    correctamente sin romper una base anterior.
    """
    conn = get_db()

    # Creamos las tablas si la base viniera vacía o incompleta.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cliente (
            numeroTel TEXT PRIMARY KEY,
            nombreCliente TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY,
            nombreProduc TEXT,
            precio REAL,
            categoria TEXT DEFAULT 'promos',
            descripcion TEXT DEFAULT '',
            imagen TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS "pedido(relacion)" (
            numPedido INTEGER PRIMARY KEY AUTOINCREMENT,
            telefono TEXT,
            idProduc INTEGER,
            cantidad INTEGER
        )
    """)

    # La base entregada no tenía categoría ni descripción.
    # Se agregan solamente si todavía no existen.
    columnas = {
        fila["name"]
        for fila in conn.execute("PRAGMA table_info(productos)").fetchall()
    }

    if "categoria" not in columnas:
        conn.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'promos'")

    if "descripcion" not in columnas:
        conn.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def obtener_productos(categoria=None):
    """Devuelve los productos de una categoría; si no se indica, devuelve todos."""
    conn = get_db()

    if categoria:
        productos = conn.execute(
            """
            SELECT id, nombreProduc, precio, categoria, descripcion, imagen
            FROM productos
            WHERE LOWER(COALESCE(categoria, '')) = LOWER(?)
            ORDER BY id
            """,
            (categoria,)
        ).fetchall()
    else:
        productos = conn.execute(
            """
            SELECT id, nombreProduc, precio, categoria, descripcion, imagen
            FROM productos
            ORDER BY id
            """
        ).fetchall()

    conn.close()
    return productos


def obtener_producto(producto_id):
    """Busca un producto por ID."""
    conn = get_db()
    producto = conn.execute(
        """
        SELECT id, nombreProduc, precio, categoria, descripcion, imagen
        FROM productos
        WHERE id = ?
        """,
        (producto_id,)
    ).fetchone()
    conn.close()
    return producto


# -------------------------------------------------------------------
# FUNCIONES DEL CARRITO
# -------------------------------------------------------------------
def carrito_actual():
    """
    Devuelve el carrito guardado en sesión.

    Se guarda como:
        {"1": 2, "5": 1}
    donde la clave es el ID del producto y el valor es la cantidad.
    """
    return session.get("carrito", {})


def cantidad_carrito():
    """Calcula cuántas unidades hay en total dentro del carrito."""
    return sum(carrito_actual().values())


# -------------------------------------------------------------------
# RUTAS PRINCIPALES
# -------------------------------------------------------------------
@app.route("/")
def inicio():
    """Página inicial de la aplicación."""
    return render_template("inicio.html")


@app.route("/promos")
def promos():
    """Página de promociones."""
    productos = obtener_productos("promos")
    return render_template("promos.html", productos=productos, carrito_cantidad=cantidad_carrito())


@app.route("/comidas")
def comidas():
    """Página de comidas."""
    productos = obtener_productos("comidas")
    return render_template("comidas.html", productos=productos, carrito_cantidad=cantidad_carrito())


@app.route("/postres")
def postres():
    """Página de postres."""
    productos = obtener_productos("postres")
    return render_template("postres.html", productos=productos, carrito_cantidad=cantidad_carrito())


@app.route("/bebidas")
def bebidas():
    """Página de bebidas."""
    productos = obtener_productos("bebidas")
    return render_template("bebidas.html", productos=productos, carrito_cantidad=cantidad_carrito())


@app.route("/info")
def info():
    """Página con las instrucciones de uso."""
    return render_template("info.html", carrito_cantidad=cantidad_carrito())


@app.route("/carrito")
def carrito():
    """Muestra los productos que actualmente están en el carrito."""
    carrito = carrito_actual()
    items = []
    total = 0

    # Recuperamos cada producto desde SQLite para mostrar nombre y precio.
    for producto_id, cantidad in carrito.items():
        producto = obtener_producto(int(producto_id))

        # Si un producto fue eliminado de la base, simplemente no se muestra.
        if producto is None:
            continue

        subtotal = (producto["precio"] or 0) * cantidad
        total += subtotal

        items.append({
            "producto": producto,
            "cantidad": cantidad,
            "subtotal": subtotal
        })

    return render_template(
        "carrito.html",
        items=items,
        total=total,
        carrito_cantidad=cantidad_carrito()
    )


# -------------------------------------------------------------------
# RUTAS PARA MODIFICAR EL CARRITO
# -------------------------------------------------------------------
@app.post("/agregar/<int:producto_id>")
def agregar_al_carrito(producto_id):
    """Agrega una unidad del producto indicado al carrito."""
    producto = obtener_producto(producto_id)

    if producto is None:
        flash("El producto no existe.", "error")
        return redirect(request.referrer or url_for("promos"))

    carrito = carrito_actual()
    clave = str(producto_id)
    carrito[clave] = carrito.get(clave, 0) + 1

    session["carrito"] = carrito
    session.modified = True

    flash(f"{producto['nombreProduc']} fue añadido al carrito.", "success")
    return redirect(request.referrer or url_for("promos"))


@app.post("/carrito/quitar/<int:producto_id>")
def quitar_del_carrito(producto_id):
    """Resta una unidad; si llega a cero, elimina el producto."""
    carrito = carrito_actual()
    clave = str(producto_id)

    if clave in carrito:
        carrito[clave] -= 1

        if carrito[clave] <= 0:
            del carrito[clave]

    session["carrito"] = carrito
    session.modified = True

    return redirect(url_for("carrito"))


@app.post("/carrito/vaciar")
def vaciar_carrito():
    """Elimina todos los productos del carrito."""
    session["carrito"] = {}
    session.modified = True
    return redirect(url_for("carrito"))


# -------------------------------------------------------------------
# FINALIZAR PEDIDO
# -------------------------------------------------------------------
@app.post("/finalizar-pedido")
def finalizar_pedido():
    """
    Guarda el cliente y cada línea del pedido en SQLite.

    El formulario envía nombre y teléfono. El número de pedido se genera
    automáticamente mediante AUTOINCREMENT.
    """
    carrito = carrito_actual()

    if not carrito:
        flash("El carrito está vacío.", "error")
        return redirect(url_for("carrito"))

    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()

    if not nombre or not telefono:
        flash("Completá nombre y teléfono para confirmar el pedido.", "error")
        return redirect(url_for("carrito"))

    conn = get_db()

    # Guardamos o actualizamos los datos del cliente.
    conn.execute(
        """
        INSERT INTO cliente (numeroTel, nombreCliente)
        VALUES (?, ?)
        ON CONFLICT(numeroTel)
        DO UPDATE SET nombreCliente = excluded.nombreCliente
        """,
        (telefono, nombre)
    )

    # Cada producto del carrito se guarda como una línea del pedido.
    for producto_id, cantidad in carrito.items():
        if obtener_producto(int(producto_id)) is not None:
            conn.execute(
                """
                INSERT INTO "pedido(relacion)" (telefono, idProduc, cantidad)
                VALUES (?, ?, ?)
                """,
                (telefono, int(producto_id), cantidad)
            )

    conn.commit()
    conn.close()

    # Una vez registrado, vaciamos el carrito.
    session["carrito"] = {}
    session.modified = True

    flash("¡Pedido enviado correctamente!", "success")
    return redirect(url_for("carrito"))


# -------------------------------------------------------------------
# INICIO DE LA APLICACIÓN
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Se ejecuta una sola vez al iniciar el servidor.
    init_db()

    # debug=True facilita el desarrollo. Antes de publicar la app,
    # conviene desactivarlo.
    app.run(debug=True)
