# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, login_user, logout_user

from NoMoreFormsApp.extensions import login_manager
from NoMoreFormsApp.public.forms import LoginForm
from NoMoreFormsApp.user.forms import RegisterForm
from NoMoreFormsApp.user.models import User
from NoMoreFormsApp.utils import flash_errors

import requests
from environs import Env

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.info("Hello from the home page!")
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/home.html", form=form)


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)


@blueprint.route("/sendMsg", methods=['POST'])
def sendMsg():

    # call the rasa rest endpoint (which is localhost)
    current_app.logger.info("message send callback hit")
    current_app.logger.info("message data: " + str(request.json['data']['message']))

    if str(request.json['data']['message']['senderId']) != '123456':
        current_app.logger.info('wrong user, not forwarding to rasa')
        return "no rasa sent"

    payload = {'sender': 'you', 'message': str(request.json['data']['message']['text'])}
    r = requests.post('http://host.docker.internal:5005/webhooks/rest/webhook', json=payload)
    current_app.logger.info("rasa raw response: " + str(r.json()))

    env = Env()
    headers = {'Authorization': 'Bearer ' + env("TALKJS_SECRET")}
    response_payload = [
                         {
                           "text": r.json()[0]['text'],
                           "sender": "654321",
                           "type": "UserMessage"
#                            "referencedMessageId": "msg_6TKoWs0Jm8XrjPOmFdOGiX"
                         }
                       ]
    requests.post('https://api.talkjs.com/v1/tuP7sjEL/conversations/7fcfae37bf41727cd5d6/messages', headers=headers, json=response_payload)
#     print(request)
#     print(request.json)
#     print(request.form)
    # use the response from rasa to call the talk JS rest to add message to conversation
    return "rasa sent"
