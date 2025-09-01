import os
from src.main import app, db

with app.app_context():
    db.create_all()
    print("Banco de dados inicializado com sucesso!")

