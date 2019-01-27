import os
import yaml
import json
import flask
import connexion

import nandy.data

def app():

    app = connexion.App("service", specification_dir='/opt/pi-k8s/openapi')
    app.add_api('service.yaml')

    app.app.data = nandy.data.NandyData()

    return app

# These are for sending and recieving model data as dicts

def model_in(converted):

    fields = {}

    for field in converted.keys():

        if field == "yaml":
            fields["data"] = yaml.load(converted[field])
        else:
            fields[field] = converted[field]

    return fields

def model_out(model):

    converted = {}

    for field in model.__table__.columns._data.keys():

        converted[field] = getattr(model, field)

        if field == "data":
            converted["yaml"] = yaml.dump(dict(converted[field]), default_flow_style=False)

    return converted

def models_out(models):

    return [model_out(model) for model in models]

def setting_load():

    with open("/opt/pi-k8s/config/settings.yaml", "r") as settings_file:
        return yaml.load(settings_file)

def health():

    return {"message": "OK"}

def setting_list():

    return {"settings": setting_load()}

def person_create():

    return {
        "person": model_out(
            flask.current_app.data.person_create(
                model_in(flask.request.json["person"])
            )
        )
    }, 201

def person_list():

    return {"persons": models_out(flask.current_app.data.person_list())}

def person_retrieve(person_id):

    return {"person": model_out(flask.current_app.data.person_retrieve(person_id))}

def person_update(person_id):

    return {
        "updated": flask.current_app.data.person_update(
            person_id,
            model_in(flask.request.json["person"])
        )
    }, 202

def person_delete(person_id):

    return {
        "deleted": flask.current_app.data.person_delete(person_id)
    }, 202

def area_create():

    return {
        "area": model_out(
            flask.current_app.data.area_create(
                model_in(flask.request.json["area"])
            )
        )
    }, 201

def area_list():

    return {"areas": models_out(flask.current_app.data.area_list())}

def area_retrieve(area_id):

    return {"area": model_out(flask.current_app.data.area_retrieve(area_id))}

def area_update(area_id):

    return {
        "updated": flask.current_app.data.area_update(
            area_id,
            model_in(flask.request.json["area"])
        )
    }, 202

def area_status(area_id, status):

    area = flask.current_app.data.area_retrieve(area_id)

    return {
        "updated": flask.current_app.data.area_status(
            area,
            status
        )
    }, 202

def area_delete(area_id):

    return {
        "deleted": flask.current_app.data.area_delete(area_id)
    }, 202

def template_create():

    return {
        "template": model_out(
            flask.current_app.data.template_create(
                model_in(flask.request.json["template"])
            )
        )
    }, 201

def template_list():

    return {"templates": models_out(flask.current_app.data.template_list())}

def template_retrieve(template_id):

    return {"template": model_out(flask.current_app.data.template_retrieve(template_id))}

def template_update(template_id):

    return {
        "updated": flask.current_app.data.template_update(
            template_id,
            model_in(flask.request.json["template"])
        )
    }, 202

def template_delete(template_id):

    return {
        "deleted": flask.current_app.data.template_delete(template_id)
    }, 202

def chore_create():

    return {
        "chore": model_out(
            flask.current_app.data.chore_create(
                fields=(model_in(flask.request.json["chore"]) if "chore" in flask.request.json else None),
                template=(model_in(flask.request.json["template"]) if "template" in flask.request.json else None)
            )
        )
    }, 201

def chore_list():

    return {"chores": models_out(flask.current_app.data.chore_list())}

def chore_retrieve(chore_id):

    return {"chore": model_out(flask.current_app.data.chore_retrieve(chore_id))}

def chore_update(chore_id):

    return {
        "updated": flask.current_app.data.chore_update(
            chore_id,
            model_in(flask.request.json["chore"])
        )
    }, 202

def chore_action(chore_id, action):

    chore = flask.current_app.data.chore_retrieve(chore_id)

    if action in ["next", "pause", "unpause", "skip", "unskip", "complete", "incomplete"]:
        return {
            "updated": getattr(flask.current_app.data, f"chore_{action}")(chore)
        }, 202

def chore_delete(chore_id):

    return {
        "deleted": flask.current_app.data.chore_delete(chore_id)
    }, 202

def task_action(chore_id, task_id, action):

    chore = flask.current_app.data.chore_retrieve(chore_id)

    if action in ["pause", "unpause", "skip", "unskip", "complete", "incomplete"]:
        return {
            "updated": getattr(flask.current_app.data, f"task_{action}")(chore.data["tasks"][task_id], chore)
        }, 202

def act_create():

    return {
        "act": model_out(
            flask.current_app.data.act_create(
                fields=(model_in(flask.request.json["act"]) if "act" in flask.request.json else None),
                template=(model_in(flask.request.json["template"]) if "template" in flask.request.json else None)
            )
        )
    }, 201

def act_list():

    return {"acts": models_out(flask.current_app.data.act_list())}

def act_retrieve(act_id):

    return {"act": model_out(flask.current_app.data.act_retrieve(act_id))}

def act_update(act_id):

    return {
        "updated": flask.current_app.data.act_update(
            act_id,
            model_in(flask.request.json["act"])
        )
    }, 202

def act_delete(act_id):

    return {
        "deleted": flask.current_app.data.act_delete(act_id)
    }, 202
