from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config

# logging.basicConfig(level=logging.INFO)  # Define nível de log
# logger = logging.getLogger(__name__)  # Cria o logger global


# Configura o pool de conexões
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=280
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SQLAlchemy()


def create_app():
    try:
        app = Flask(__name__)
        app.config.from_object(Config)

        # Inicializações
        db.init_app(app)

        # Registrar blueprint
        from .routes import bp as main_bp
        app.register_blueprint(main_bp)

        return app

    except Exception as e:
        print(f"Erro ao inicializar a aplicação: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
