import sys
import os
import logging
from dotenv import load_dotenv

# Ruta base del proyecto
project_home = '/var/www/html/SGDWEB'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Cargar variables de entorno desde .env
load_dotenv('/var/www/html/SGDWEB/app/.env')

# Importar la aplicación Flask
from app import app as application

# Configurar logging
application.logger.addHandler(logging.StreamHandler())
application.logger.setLevel(logging.INFO)
