import datetime
import logging
import os
import time
from logging.handlers import RotatingFileHandler

import pika
import pytz

from application import db, create_app
from application.models import Schedule, Machine, Bot, Task
from config import Config

# Obtém o diretório do LocalAppData
local_appdata = os.getenv('LOCALAPPDATA')
log_dir = os.path.join(local_appdata, 'COREBOT-PY')

# Cria o diretório se não existir
os.makedirs(log_dir, exist_ok=True)

# Define o caminho completo para o arquivo de log
log_file = os.path.join(log_dir, f'dafe_scheduler_T{Config.TENANT_ID}.txt')

# Configura o logger com RotatingFileHandler
handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log(log_type, message):
    print(f'[{log_type}] - [{message}]')
    if log_type == 'DEBUG':
        logger.debug(message)
    elif log_type == 'ERROR':
        logger.error(message)
    elif log_type == 'WARN':
        logger.warning(message)
    else:
        logger.info(message)


RABBITMQ_HOST = "localhost"
tz = pytz.timezone("America/Sao_Paulo")


def publish_message(queue_name, message):
    """
    Publica uma mensagem na fila do RabbitMQ.
    """
    # Conectar ao servidor RabbitMQ
    url = os.environ.get(Config.QUEUE_PROVIDER, Config.QUEUE_CONNECT)
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Persiste a mensagem na fila
        ),
    )
    connection.close()
    log('INFO', f"Mensagem publicada na fila '{queue_name}': {message}")


def check_and_schedule_tasks():
    """
    Verifica os agendamentos no horário atual e publica mensagens na fila.
    """
    app = create_app()
    with app.app_context():
        current_time = datetime.datetime.now()

        log('INFO', f"Verificando agendamentos para {current_time}...")

        # Busca agendamentos pendentes para o horário atual
        schedules = (
            Schedule.query.filter(Schedule.execution_time <= current_time,
                                  Schedule.status == "pending")
            .join(Machine, Machine.id == Schedule.machine_id)
            .all()
        )

        def enqueue_task(_schedule):
            """
            Insere um registro na tabela task_execution e publica uma mensagem na fila RabbitMQ.
            """

            # Criar um registro na tabela task_execution
            new_task = Task(
                schedule_id=_schedule.id,
                execution_time=datetime.datetime.now(),  # Hora atual da execução
                created_at=datetime.datetime.now(),  # Hora atual da execução
                status="in_queue",  # Inicialmente, o status será "in_queue"
                script_name=_schedule.bot.script_name,
                script_directory=_schedule.bot.script_directory,
                machine=_schedule.machine
            )

            db.session.add(new_task)

            # Atualizar a coluna last_execution no Schedule
            _schedule.last_execution = datetime.datetime.now()
            _schedule.status = "in_queue"  # Atualizar status do agendamento

            # Commit para salvar no banco de dados
            db.session.commit()

            task_id = new_task.id

            # Montar a mensagem para a fila
            message = {
                "task_id": task_id,
                "schedule_id": _schedule.id,
                "script_name": _schedule.bot.script_name,
                "script_directory": _schedule.bot.script_directory,
                "git_url": _schedule.bot.git_url,
                "bot_id": _schedule.bot_id,
            }

            # Publicar a mensagem na fila associada à máquina
            publish_message(_schedule.machine.queue_name, str(message))

            log('INFO', f"Executando bot {_schedule.bot_id} agendado para {_schedule.execution_time}")

        for schedule in schedules:

            execution_time = schedule.execution_time.replace(second=0, microsecond=0)

            # Buscando o bot associado ao agendamento
            bot = db.session.get(Bot, schedule.bot_id)

            if not bot:
                log('WARN', f"Bot com ID {schedule.bot_id} não encontrado! Pulando...")
                continue  # Pula para o próximo agendamento

            if not bot.is_active:
                log('INFO', f"Bot com ID {bot} é desativado.")
                schedule.status = "Canceled"
                schedule.end_date = datetime.datetime.now()
                schedule.updated_at = datetime.datetime.now()
                db.session.commit()
                schedule.is_active = False
                db.session.commit()
                return

            log('INFO', f"Agendamento encontrado: {schedule.id} - {bot.script_name}")

            # Lógica para cada tipo de recorrência - disparo manual
            if schedule.recurrence_type == "on-demand":
                if execution_time <= current_time:
                    enqueue_task(schedule)
                    schedule.status = 'completed'

            # Lógica para cada tipo de recorrência
            if schedule.recurrence_type == "once":
                if execution_time <= current_time:
                    enqueue_task(schedule)
                    schedule.status = 'completed'

            elif schedule.recurrence_type == "daily":
                if execution_time.time() == current_time.time():
                    enqueue_task(schedule)
                    schedule.status = 'pending'

            elif schedule.recurrence_type == "weekly":
                today = current_time.strftime("%A").lower()  # Obtém o dia da semana (monday, tuesday, etc.)
                scheduled_days = schedule.days_of_week.split(",") if schedule.days_of_week else []
                if today in scheduled_days and execution_time.time() == current_time.time():
                    enqueue_task(schedule)
                    schedule.status = 'pending'

            elif schedule.recurrence_type == "interval":
                last_execution = schedule.last_execution or schedule.execution_time
                interval_minutes = schedule.interval_minutes or 0

                if (current_time - last_execution).total_seconds() >= interval_minutes * 60:
                    enqueue_task(schedule)
                    schedule.last_execution = current_time
                    schedule.status = 'pending'

            db.session.commit()
    # Aguardar antes de verificar novamente
    time.sleep(5)


def check_and_schedule_tasks_bkp():
    """
    Verifica os agendamentos no horário atual e publica mensagens na fila.
    """
    app = create_app()
    with app.app_context():
        current_time = datetime.datetime.now()

        log('INFO', f"Verificando agendamentos para {current_time}...")

        # Busca agendamentos pendentes para o horário atual
        schedules = (
            Schedule.query.filter(Schedule.execution_time <= current_time, Schedule.status == "pending")
            .join(Machine, Machine.id == Schedule.machine_id)
            .all()
        )

        for schedule in schedules:
            log('INFO', f"Agendamento encontrado: {schedule.id} - {schedule.script_name}")

            # Monta a mensagem para a fila
            message = {
                "schedule_id": schedule.id,
                "script_name": schedule.script_name,
                "script_directory": schedule.script_directory,
            }

            # Publica a mensagem na fila associada à máquina
            publish_message(schedule.machine.queue_name, str(message))

            # Atualiza o status do agendamento para "in_queue"
            schedule.status = "in_queue"
            db.session.commit()
    # Aguardar antes de verificar novamente
    time.sleep(5)


if __name__ == "__main__":
    log('INFO', f"Iniciando o servidor de agendamentos...")
    while True:
        try:
            check_and_schedule_tasks()
            time.sleep(10)  # Aguarda 10 segundos antes de verificar novamente
        except KeyboardInterrupt:
            log('WARN', f"Servidor de agendamentos interrompido pelo usuário.")
            break
        except Exception as e:
            log('ERROR', f"Erro no servidor de agendamentos: {str(e)}")
