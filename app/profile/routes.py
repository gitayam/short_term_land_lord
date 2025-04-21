from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.profile import bp
from app.profile.forms import EditProfileForm, ChangePasswordForm

@bp.route('/')
@login_required
def view_profile():
    return render_template('profile/view_profile.html', title='My Profile')

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.email)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile.view_profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email

    return render_template('profile/edit_profile.html', title='Edit Profile', form=form)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been changed.', 'success')
        return redirect(url_for('profile.view_profile'))

    return render_template('profile/change_password.html', title='Change Password', form=form)