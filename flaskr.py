#coding=utf-8
import sqlite3, time ,os 
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, send_from_directory
from contextlib import closing
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from PIL import Image

#数据库
DATABASE = 'flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'admin'
UPLOADED_PHOTOS_DEST = './photo/static/photo'
app = Flask(__name__)
app.config.from_object(__name__)

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB

class UploadForm(FlaskForm):
    photo = FileField(validators=[
        FileAllowed(photos, u'只能上传图片！'), 
        FileRequired(u'文件未选择！')])
    submit = SubmitField(u'上传')

'''@app.route('/addpic', methods=['GET', 'POST'])
def upload_file():
    global file_url
    form = UploadForm()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
    else:
        file_url = None
    return render_template('addpic.html', form=form, file_url=file_url)'''

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/pictures', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    #picture = g.db.execute('select file_url,id from pictures')
    #show_pic = [dict(pic=row[0],id=row[1]) for row in picture.fetchall()]
    or_path = 'photo/static/photo/'
    sl_path = 'photo/static/slphoto/'
    or_list = os.listdir(or_path)
    sl_list = os.listdir(sl_path)

    or_result = [(or_list, os.stat(or_path + or_list).st_ctime) for or_list in os.listdir(or_path)]
    sl_result = [(sl_list, os.stat(sl_path + sl_list).st_ctime) for sl_list in os.listdir(sl_path)]
    or_list = sorted(or_result, key=lambda x: x[1],reverse=True)
    sl_list = sorted(sl_result, key=lambda x: x[1],reverse=True)
    or_photo = [dict(or_pic = row[0]) for row in or_list]
    sl_photo = [dict(sl_pic = row[0],sl_time = time.strftime("%Y-%m-%d %H:%M:%S" , time.localtime(row[1]))) for row in sl_list]
    photo = []
    for i in range(len(or_photo)):
        photo.append(dict(or_photo[i],**sl_photo[i]))
    print(photo)
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        #file_url = photos.url(filename)
        #g.db.execute('insert into pictures (file_url,time) values (?,?)',[file_url,time.strftime("%a %m-%d %H:%M:%S", time.localtime())])
        #g.db.commit()
        filename1 = filename.rstrip('.bmp.jpg.png.tiff.gif.pcx.tga.exif.fpx.svg.psd.cdr.pcd.dxf.ufo.eps.ai.raw.WMF')
        img = Image.open(or_path + filename)
        img = img.resize((250, 250), Image.ANTIALIAS)
        img.save(sl_path + filename1 + '.png','png')
        flash('Upload completed')
    else:
        filename = None
    return render_template('pictures.html',form=form,photo=photo)
    '''show_pic=show_pic,'''

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
    number = g.db.execute('select num from number')
    #picture = g.db.execute('select file_url,id from pictures')
    #show_pic = [dict(pic=row[0],id=row[1]) for row in picture.fetchall()]
    show_num = [dict(num=row[0]) for row in number.fetchall()]
    entries = [dict(title=row[0], text=row[1], time=row[2]) for row in cur.fetchall()]
    g.db.commit()
    return render_template('show_entries.html', entries=entries , show_num=show_num )

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
