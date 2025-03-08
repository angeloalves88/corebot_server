from application import create_app, db
from application.models import Machine

app = create_app()

with app.app_context():
    # Verificar se as máquinas já existem
    if not Machine.query.filter_by(queue_name="machine_1_queue").first():
        machine1 = Machine(name="Machine 1", queue_name="machine_1_queue")
        db.session.add(machine1)

    db.session.commit()
    print("Banco de dados populado com sucesso!")
