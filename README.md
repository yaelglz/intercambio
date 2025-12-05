# Append runtime deps
cat >> `requirements.txt` <<'EOF'
gunicorn==20.1.0
psycopg2-binary==2.9.7
EOF

# Example snippet to add/merge into your `app.py` so it uses env vars (keeps SQLite as fallback)
cat > `app_env_snippet.py` <<'PY'
import os
from flask import Flask

app = Flask(__name__)

# Secret key from env (set in Render environment)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

# Prefer Postgres via DATABASE_URL, fallback to local sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///intercambio.db'
)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_flag = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug_flag)
PY

# Render start command to use in the dashboard:
# gunicorn app:app --bind 0.0.0.0:$PORT# 🎄 Intercambio Navideño 2025 🎄

Aplicación web para gestionar el intercambio navideño (Secret Santa) con restricciones familiares y anonimato condicional.

## Características

- ✅ Registro de participantes con información personal
- ✅ Sorteo automático con restricción: no se puede asignar a alguien del mismo jefe de familia
- ✅ Anonimato condicional basado en si pasarán Navidad en Tepoztlán
- ✅ Propuesta de 3 opciones de regalo por participante
- ✅ Vista para Santa Claus con opciones de regalo de sus usuarios asignados

## Requisitos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Inicia la aplicación:
```bash
python app.py
```

2. Abre tu navegador en: `http://localhost:5000`

3. Flujo de uso:
   - **Registro**: Los participantes se registran en la página principal
   - **Sorteo**: Un administrador realiza el sorteo desde la página "Sorteo"
   - **Ver Santa Claus**: Cada participante puede ver su Santa Claus (anónimo) y proponer 3 opciones de regalo
   - **Ver Regalos**: Cada Santa Claus puede ver las opciones de regalo de sus usuarios asignados

## Estructura del Proyecto

```
intercambio2025/
├── app.py              # Aplicación Flask principal
├── models.py           # Modelos de base de datos
├── requirements.txt    # Dependencias
├── intercambio.db      # Base de datos SQLite (se crea automáticamente)
├── templates/          # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── sorteo.html
│   ├── ver_santa.html
│   ├── ver_regalos.html
│   ├── buscar_usuario.html
│   └── buscar_santa.html
└── static/
    └── style.css       # Estilos CSS
```

## Reglas del Sorteo

1. **Restricción familiar**: Un usuario no puede ser Santa Claus de otro usuario con el mismo jefe de familia
2. **Anonimato condicional**:
   - Si el usuario **SÍ** pasará Navidad en Tepoztlán: se muestra un número como identificador
   - Si el usuario **NO** pasará Navidad en Tepoztlán: se muestra el nombre completo

## Jefes de Familia Permitidos

- Fátima
- Conka
- María
- Guadalupe
- Lourdes
- Mónica
- Beatriz
- Martín
- Pablo

## Notas

- La base de datos se crea automáticamente al ejecutar la aplicación por primera vez
- Los datos se almacenan en SQLite (`intercambio.db`)
- Para producción, cambia la `SECRET_KEY` en `app.py`

## Desarrollo

Para ejecutar en modo desarrollo:
```bash
python app.py
```

La aplicación se ejecutará en `http://0.0.0.0:5000` con modo debug activado.

¡Feliz Navidad! 🎅🎄

