from todo_web import app, mail
from flask import render_template, redirect, url_for, flash, request
from todo_web.models import ToDo, User
from todo_web.forms import RegisterForm, LoginForm
from todo_web import db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from flask_mail import Message

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('todo'))
    if form.errors != {}: #If there are not errors from the validations
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('todo'))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('login.html', form=form)

@app.route('/todo')
@login_required
def todo():
    owner_id = current_user.id
    current_datetime = datetime.now()
    owner_id = current_user.id
    todo_list = ToDo.query.filter_by(owner=owner_id).all()
    for todo in todo_list:
            if todo.deadline:
                if todo.deadline < current_datetime:
                    send_email_notification(current_user.email_address, f'Deadline Passed for Task: {todo.name}')
                elif todo.deadline < current_datetime + timedelta(hours=1):
                    send_email_notification(current_user.email_address, f'Deadline Approaching for Task: {todo.name}')    
    return render_template('main.html', todo_list=todo_list, current_datetime=current_datetime, timedelta=timedelta)

def send_email_notification(to_email, message):
    msg = Message('Task Notification', recipients=[to_email])
    msg.html = render_template('email_notification.html', message=message)
    mail.send(msg)

@app.route('/add',methods=['POST'])
def add():
    name = request.form.get("name")
    description = request.form.get("description")
    deadline_str = request.form.get('deadline')
    if deadline_str:
        deadline = datetime.fromisoformat(deadline_str)
    else:
        deadline = None
    new_task=ToDo(name=name,done=False, description=description, deadline=deadline)
    new_task.owner = current_user.id
    db.session.add(new_task)
    db.session.commit()
    tasks = ToDo.query.order_by(ToDo.id).all()
    for index, task in enumerate(tasks, start=1):
        task.id = index
    db.session.commit()
    return redirect(url_for("todo"))

@app.route('/update/<int:todo_id>')
def update(todo_id):
    todo= ToDo.query.get(todo_id)
    todo.done=not todo.done
    db.session.commit()
    return redirect(url_for("todo"))


@app.route('/delete/<int:todo_id>')
def delete(todo_id):
    todo= ToDo.query.get(todo_id)
    db.session.delete(todo)
    db.session.commit()
    tasks = ToDo.query.order_by(ToDo.id).all()
    for index, task in enumerate(tasks, start=1):
        task.id = index
    db.session.commit()
    return redirect(url_for("todo"))

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))










