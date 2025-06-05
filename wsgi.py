import sys
import os

# Ajouter le dossier contenant app.py au chemin
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
