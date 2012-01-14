from flask import Flask, request, render_template, url_for, redirect, Response
from vfs import Table, Block, StreamBlock
import os
from uuid import uuid4
app = Flask(__name__)

@app.route("/d/<path:name>")
def get(name):
    t = Table('user.db')
    filename = '/%s' % name.encode('utf-8')
    b = t.find(filename)
    if b:
        x = t.read(b)
    else:
        x = '', 404
    del t
    return x

@app.route('/upload/', methods=['GET', 'POST'], defaults={'folder':''})
@app.route('/upload/<path:folder>', methods=['GET', 'POST'])
def upload_file(folder):
    #print 'upload_file:', folder
    if request.method == 'POST':
        f = request.files['f']

        t = Table('user.db')
        folder = request.form['target'].encode('utf-8')
        filename = os.path.join(folder, str(uuid4()))
        #print type(filename), filename
        b = t.create(filename, f.stream.read())
        t.write(b)
        del t
    else:
        filename = ''
        folder = '/%s' % folder.encode('utf-8')

    return render_template('upload.html', name=filename, folder=folder)

@app.route("/folder/<path:name>")
@app.route("/folder/", defaults={'name':''})
def folder(name):
    #print 'map:', app.url_map
    t = Table('user.db')
    filename = '/%s' % name.encode('utf-8')
    if not filename.endswith('/'):
        filename += '/'
    folders = t.readdir(filename)
    files = t.readfile(filename)

    return render_template('index.html', folders=folders, 
                           files=files, current=filename)


@app.route('/')
def index():
    return redirect(url_for('folder'))

class Foo():
    def __init__(self):
        self.count = 1000
    def __iter__(self):
        return self
    def next(self):
        if self.count == 0:
            raise StopIteration()
        self.count -= 1
        return str(uuid4())
    def __len__(self):
        return 1000 * len(str(uuid4()))

@app.route("/q/<path:name>")
def test(name):
    t = Table('user.db')
    filename = '/%s' % name.encode('utf-8')
    b = t.find(filename)

    f = Response(StreamBlock(b,t), mimetype='application/octet-stream')
    f.content_language = str(b.length)
    return f
    
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',threaded=True)
