from Babylon import app, db, bcrypt
from flask import Flask, render_template, redirect, flash, url_for, request
from flask_login import login_user, current_user, logout_user, login_required
from Babylon.forms import RegistrationForm, LoginForm
from Babylon.models import User, Plant, House


@app.route('/', methods=['POST', 'GET'])
def login():
    # need to create dashboard route
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check your email and password.', 'dark')
    return render_template('login.html', title='Login', form=form)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created. You are now able to log in!', 'light')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


#create a route for dashboard and design the layout