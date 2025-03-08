import bcrypt
from sqlalchemy import text

from application import create_app
from application import db
from application.models import Tenant, User


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Crie o contexto da aplicação
app = create_app()
with app.app_context():
    try:
        db.create_all()
        # Teste a conexão ao banco de dados com o SQL Server
        db.session.execute(text("SELECT 1"))

        # Crie o tenant padrão se ele não existir
        development_tenant = Tenant.query.filter_by(name='Development').first()
        if not development_tenant:
            development_tenant = Tenant(name='Development')
            db.session.add(development_tenant)
            db.session.commit()

        # Crie o usuário administrador se ele não existir
        admin_user = User.query.filter_by(username='admin@corebotpy.com').first()
        if not admin_user:
            admin_user = User(username='admin@corebotpy.com',
                              password_hash=hash_password('@corebot$2025', email='admin@corebotpy.com'))
            admin_user.tenants.append(development_tenant)
            db.session.add(admin_user)
            db.session.commit()

        print("Conexão com o banco de dados funcionando corretamente.")
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
