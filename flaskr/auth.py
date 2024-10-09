import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        
        db = get_db()
        error = None
        
        if not name:
            error = 'name is required.'
        elif not password:
            error = 'Password is required.'
        
        if error is None:
            try:
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO \"user\" (id, name, password) VALUES (uuid_generate_v1(), %s, %s)",
                    (name, generate_password_hash(password))
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {name} is already registered."
            else:
                return redirect(url_for("auth.login"))
        
        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        db = get_db()
        error = None
        
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM \"user\" WHERE name = %s", (name,)
        )
        user = cursor.fetchone()

        print(user)
        if user is None:
            error = 'Incorrect name.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        
        flash(error)
    
    return render_template('auth/login.html')
        
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    db = get_db()
    
    if user_id is None:
        g.user = None
    else:
        cursor = db.cursor()
        cursor.execute(
            'SELECT * FROM \"user\" WHERE id = %s', (user_id,)
        )
        g.user = cursor.fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    return wrapped_view