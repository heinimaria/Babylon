import secrets
import os
from PIL import Image, ExifTags
from Babylon import app, db, bcrypt
from flask import Flask, render_template, redirect, flash, url_for, request, abort, session
from flask_login import login_user, current_user, logout_user, login_required
from Babylon.forms import RegistrationForm, LoginForm, PlantForm, HouseForm, DateWateredForm, UpdateAccountForm
from Babylon.models import User, Plant, House
from datetime import timedelta, datetime


@app.route('/', methods=['POST', 'GET'])
def login():
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
        flash('Your account has been created. You are now able to log in!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    houses = current_user.houses
    form = HouseForm()
    list1 = []
    for house in houses:
        for plant in house.plants:
            plant_list = []
            if days_until_watering(plant.id) <= 0:
                plant_list.append(house.id)
                plant_list.append(plant.name)
                plant_list.append(plant.location)
            list1.append(plant_list)
    return render_template('dashboard.html', title='My Dashboard', houses=houses, list1=list1, form=form)


@app.route('/dashboard#second', methods=['POST', 'GET'])
@login_required
def add_house():
    form = HouseForm()
    if form.validate_on_submit():
        house = House(name=form.name.data, address_first_line=form.address_first_line.data,
                      address_second_line=form.address_second_line.data, postcode=form.postcode.data,
                      town=form.town.data, user=current_user)
        db.session.add(house)
        db.session.commit()
        flash('You have successfully created a new house!', 'success')
        return redirect(url_for('house_view', house_id=house.id))
    houses = House.query.all()
    return render_template('dashboard.html', title='Add House', form=form, houses=houses)


def get_address(house_id):
    house = House.query.filter_by(id=house_id).one()
    if house.address_first_line is not None or house.address_second_line is not None or house.postcode is not None or house.town is not None:
        address = house.address_first_line + '\n' + house.address_second_line + '\n' + house.postcode + " " + house.town
        address1 = [house.address_first_line, house.address_second_line, house.postcode, house.town]
    else:
        address1 = ''
    return address1


def days_until_watering(plant_id):
    plant = Plant.query.filter_by(id=plant_id).one()
    if plant.date_watered is not None:
        days_until_watering = plant.next_watering - datetime.now()
        days = days_until_watering.days
    else:
        days = 0
    return days


def progress(plant_id):
    plant = Plant.query.filter_by(id=plant_id).one()
    if plant.date_watered is not None:
        days_until_watering = plant.next_watering - datetime.now()
        water_progress = 100 - days_until_watering.days / plant.watering_frequency * 100
    else:
        water_progress = ""
    return water_progress


@app.route('/houseview/<house_id>', methods=['POST', 'GET'])
@login_required
def house_view(house_id):
    house = House.query.get_or_404(house_id)
    if house.user != current_user:
        abort(403)
    progress_ids = []
    unknown_plants = []
    watering_needed = []
    ok_plants = []
    for plant in house.plants:
        prog = [plant.id, progress(plant.id)]
        progress_ids.append(prog)
        if plant.date_watered is None:
            unknown_plants.append(plant)
        elif plant.next_watering <= datetime.now():
            watering_needed.append(plant)
        elif plant.next_watering > datetime.now():
            ok_plants.append(plant)
    house_form = HouseForm()
    form = PlantForm()
    date_now = datetime.now()
    address = get_address(house_id)
    return render_template('house.html', title=house.name, house=house, house_form=house_form,
                           form=form, address=address, progress_ids=progress_ids, date_now=date_now, unknown_plants=unknown_plants, watering_needed=watering_needed, ok_plants=ok_plants)


@app.route('/edithouse/<house_id>', methods=['POST', 'GET'])
@login_required
def edit_house(house_id):
    house = House.query.get_or_404(house_id)
    if house.user != current_user:
        abort(403)
    form = HouseForm()
    if form.validate_on_submit():
        house.name = form.name.data
        house.address_first_line = form.address_first_line.data
        house.address_second_line = form.address_second_line.data
        house.town = form.town.data
        house.postcode = form.postcode.data
        db.session.commit()
        flash(f'{house.name} was updated successfully!', 'success')
        return redirect(url_for('house_view', house_id=house.id))
    elif request.method == 'GET':
        form.name.data = house.name
        form.address_first_line.data = house.address_first_line
        form.address_second_line.data = house.address_second_line
        form.town.data = house.town
        form.postcode.data = house.postcode
    return render_template('edit_house.html', form=form, house=house, title='Edit')


@app.route('/deletehouse/<house_id>', methods=['POST', 'GET'])
@login_required
def delete_house(house_id):
    house = House.query.get_or_404(house_id)
    if house.user != current_user:
        abort(403)
    if request.method == 'POST':
        db.session.delete(house)
        db.session.commit()
        flash(house.name + ' was deleted successfully!', 'success')
        return redirect(url_for('dashboard', house_id=house.id))
    else:
        return render_template('dashboard.html')


@app.route('/plantview/<plant_id>', methods=['POST', 'GET'])
@login_required
def plant_view(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if plant.house.user != current_user:
        abort(403)
    water_form = DateWateredForm()
    form = PlantForm()
    image_file = url_for('static', filename='plant_pics/' + plant.image_file)
    watering_progress = progress(plant_id)
    days_til_watering = days_until_watering(plant_id)
    return render_template('plant.html', title=plant.name + ' | ' + plant.house.name, plant=plant,
                           water_form=water_form, form=form, image_file=image_file,
                           watering_progress=watering_progress, days_til_watering=days_til_watering)


def save_plant_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/plant_pics', picture_fn)

    output_size = (400, 400)
    i = Image.open(form_picture)
    i.thumbnail(output_size, Image.ANTIALIAS)
    i.save(picture_path)

    return picture_fn


@app.route('/addplant/<house_id>', methods=['POST', 'GET'])
@login_required
def add_plant(house_id):
    house = House.query.get_or_404(house_id)
    if house.user != current_user:
        abort(403)
    form = PlantForm()
    if form.validate_on_submit():
        plant = Plant(name=form.name.data, location=form.location.data, image_file=form.image.data,
                      watering_frequency=form.watering_frequency.data, house=house)
        if form.image.data:
            picture_file = save_plant_picture(form.image.data)
            plant.image_file = picture_file
        db.session.add(plant)
        db.session.commit()
        flash('New plant has been added!', 'success')
        return redirect(url_for('house_view', house_id=house.id))
    return render_template('addPlant.html', title='Add Plant', form=form)


@app.route('/deleteplant/<plant_id>', methods=['POST', 'GET'])
@login_required
def delete_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if plant.house.user != current_user:
        abort(403)
    if request.method == 'POST':
        house_ref = plant.house.id
        db.session.delete(plant)
        db.session.commit()
        flash(plant.name + ' was deleted successfully!', 'success')
        return redirect(url_for('house_view', house_id=house_ref))
    else:
        return render_template('plant.html')


@app.route('/wateringdate/<plant_id>', methods=['POST', 'GET'])
@login_required
def date_watered(plant_id):
    water_form = DateWateredForm()
    plant = Plant.query.get_or_404(plant_id)
    if plant.house.user != current_user:
        abort(403)
    if water_form.validate_on_submit():
        plant.date_watered = water_form.date_watered.data
        plant.next_watering = water_form.date_watered.data + timedelta(days=plant.watering_frequency)
        db.session.commit()
        return redirect(url_for('plant_view', plant_id=plant.id))
    return render_template('plant.html', water_form=water_form, plant=plant)



def save_profile_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size, Image.ANTIALIAS)
    i.save(picture_path)

    return picture_fn


@app.route('/account', methods=['POST', 'GET'])
@login_required
def user_account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", 'success')
        return redirect(url_for('user_account'))
    # populates the form fields with current name and email
    elif request.method == "GET":
        form.name.data = current_user.name
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', form=form, image_file=image_file)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/editplant/<plant_id>', methods=['POST', 'GET'])
@login_required
def edit_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if plant.house.user != current_user:
        abort(403)
    form = PlantForm()
    if form.validate_on_submit():
        plant.name = form.name.data
        plant.location = form.location.data
        plant.watering_frequency = form.watering_frequency.data
        if form.image.data:
            picture_file = save_plant_picture(form.image.data)
            plant.image_file = picture_file
        db.session.commit()
        flash(f'{plant.name} was updated successfully!', 'success')
        return redirect(url_for('plant_view', plant_id=plant.id))
    elif request.method == 'GET':
        form.name.data = plant.name
        form.location.data = plant.location
        form.watering_frequency.data = plant.watering_frequency
    image_file = url_for('static', filename='plant_pics/' + plant.image_file)
    return render_template('edit_plant.html', image_file=image_file, form=form, plant=plant, title='Edit')


# organise plants by watering
# watering history
# edit function for house
# delete function for user
# search function for plants
# fix account edit/add plant forms
