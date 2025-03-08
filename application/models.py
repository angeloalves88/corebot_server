from datetime import datetime

from . import db


class Tenant(db.Model):
    __tablename__ = "tenant"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    users = db.relationship("User", secondary="user_tenant", back_populates="tenants")


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)  # Armazena o hash da senha
    email = db.Column(db.String(255), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenants = db.relationship("Tenant", secondary="user_tenant", back_populates="users")


class UserTenant(db.Model):
    __tablename__ = "user_tenant"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), primary_key=True)
    is_active = db.Column(db.Boolean, default=True)


class Machine(db.Model):
    __tablename__ = "machine"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    queue_name = db.Column(db.String(100), nullable=False)


class Schedule(db.Model):
    __tablename__ = "schedule"
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(255), nullable=False)
    type_execution = db.Column(db.String(50), nullable=True)
    execution_time = db.Column(db.DateTime, nullable=False)
    recurrence_type = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    interval_minutes = db.Column(db.Integer, nullable=True)
    days_of_week = db.Column(db.String(50), nullable=True)
    cron_expression = db.Column(db.String(100), nullable=True)
    last_execution = db.Column(db.DateTime, nullable=True)  # Essa linha precisa estar presente
    end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Indica se o agendamento está ativo

    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=True)
    bot_id = db.Column(db.Integer, db.ForeignKey("bot.id"), nullable=False)

    machine = db.relationship("Machine")
    bot = db.relationship("Bot", backref="schedules")


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=False)
    execution_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default="pending", nullable=False)  # pending, running, completed, failed
    logs = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    script_name = db.Column(db.String(255), nullable=False)
    script_directory = db.Column(db.String(255), nullable=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=False)

    machine = db.relationship("Machine")
    schedule = db.relationship("Schedule", backref="tasks")


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenant.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bots = db.relationship("Bot", back_populates="project", lazy="dynamic", cascade="all, delete-orphan")
    tenant = db.relationship("Tenant", backref="projects")


class Bot(db.Model):
    __tablename__ = "bot"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    script_name = db.Column(db.String(255), nullable=False)
    script_directory = db.Column(db.String(255), nullable=True)
    git_url = db.Column(db.String(255), nullable=True)  # Novo campo para armazenar o link do Git

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = db.relationship("Project", back_populates="bots")


class ProjectParameter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Text, nullable=True)
