import pytz
from flask import Blueprint, render_template, request, redirect, url_for, flash

from . import db
from .models import Project, ProjectParameter

bp = Blueprint('main', __name__)

# Defina o fuso horário de Brasília
brasil = pytz.timezone('America/Sao_Paulo')


#############################################
# Parameters
#############################################

@bp.route("/projects/<int:project_id>/parameters")
def list_parameters(project_id):
    project = Project.query.get_or_404(project_id)
    parameters = ProjectParameter.query.filter_by(project_id=project_id).all()
    return render_template("parameters.html", project=project, parameters=parameters)


@bp.route("/projects/<int:project_id>/parameters/new", methods=["POST"])
def add_parameter(project_id):
    project = Project.query.get_or_404(project_id)
    key = request.form.get("key")
    value = request.form.get("value")

    if not key or not value:
        flash("Chave e valor são obrigatórios.", "danger")
        return redirect(url_for("main.list_parameters", project_id=project_id))

    parameter = ProjectParameter(project_id=project_id, key=key, value=value)
    db.session.add(parameter)
    db.session.commit()
    flash("Parâmetro adicionado com sucesso!", "success")
    return redirect(url_for("main.list_parameters", project_id=project_id))


@bp.route("/projects/<int:project_id>/parameters/edit/<int:parameter_id>", methods=["POST"])
def edit_parameter(project_id, parameter_id):
    parameter = ProjectParameter.query.get_or_404(parameter_id)
    parameter.key = request.form.get("key")
    parameter.value = request.form.get("value")
    db.session.commit()
    flash("Parâmetro atualizado com sucesso!", "success")
    return redirect(url_for("main.list_parameters", project_id=project_id))


@bp.route("/projects/<int:project_id>/parameters/delete/<int:parameter_id>", methods=["POST"])
def delete_parameter(project_id, parameter_id):
    parameter = ProjectParameter.query.get_or_404(parameter_id)
    db.session.delete(parameter)
    db.session.commit()
    flash("Parâmetro removido com sucesso!", "success")
    return redirect(url_for("main.list_parameters", project_id=project_id))
