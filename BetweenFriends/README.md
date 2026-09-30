# Between Friends - versión Flask corregida

## Estructura

```text
BetweenFriends_corregido/
├── app.py
├── BaseDatosMateo (copia).db
├── requirements.txt
├── templates/
│   ├── inicio.html
│   ├── promos.html
│   ├── comidas.html
│   ├── postres.html
│   ├── bebidas.html
│   ├── info.html
│   └── carrito.html
└── static/
    ├── stylesinicio.css
    ├── stylespromo.css
    ├── stylescomidas.css
    ├── stylespostres.css
    ├── stylesbebidas.css
    ├── stylesinfo.css
    ├── stylescarrito.css
    └── imagenes/
```

## Ejecutar

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python3 app.py
```

Luego abrir `http://127.0.0.1:5000/`.

## Base de datos

La aplicación usa SQLite y el archivo `BaseDatosMateo (copia).db`.

La tabla `productos` necesita las categorías:

- `promos`
- `comidas`
- `postres`
- `bebidas`

Al iniciar, `app.py` agrega automáticamente las columnas `categoria` y `descripcion` si la base antigua no las tiene.

La base entregada no contiene productos cargados, por eso las páginas de menú muestran un aviso hasta que se inserten productos.
