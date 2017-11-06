#coding=utf-8
import os
import sqlite3, time
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

#数据库
DATABASE = 'flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'admin'
UPLOADED_PHOTOS_DEST = os.getcwd()

app = Flask(__name__)
app.config.from_object(__name__)

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)

class UploadForm(FlaskForm):
    photo = FileField(validators=[
        FileAllowed(photos, u'只能上传图片！'), 
        FileRequired(u'文件未选择！')])
    submit = SubmitField(u'上传')

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read().decode())
            db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/')
def show_entries():
    cur = g.db.execute('select title, text, time from entries order by id desc')
    num = g.db.execute('update number set num = num +1')
    g.db.commit()
    number = g.db.execute('select num from number')
    show_num = [dict(num=row[0]) for row in number.fetchall()]
    entries = [dict(title=row[0], text=row[1], time=row[2]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries , show_num=show_num)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text, time) values (?, ?, ?)',[request.form['title'], request.form['text'], time.strftime("%a %m-%d %H:%M:%S", time.localtime())])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)
