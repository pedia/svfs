import os
import logging
import httplib2
from uuid import uuid4

from flask import Flask, request, render_template, url_for, redirect, Response, session
from vfs import Table, Block, StreamBlock

app = Flask(__name__)

"""
renren = oauth.remote_app('renren',
    base_url='http://graph.renren.com/1/',
    request_token_url='https://graph.renren.com/oauth/token',
    access_token_url='https://graph.renren.com/oauth/authorize',
    authorize_url='https://graph.renren.com/oauth/authorize', # yes
    consumer_key='f3ef44ed9a76490a89d137dbf749af55',
    consumer_secret='be16f097be0d4b42bead5726604853f7'
)
"""

"""
#1
https://graph.renren.com/oauth/authorize?client_id=f3ef44ed9a76490a89d137dbf749af55&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2F&response_type=code
TODO: scope=[ http://wiki.dev.renren.com/wiki/%E6%9D%83%E9%99%90%E5%88%97%E8%A1%A8 ]

agree got:
?code=B39qhZXDu8EXSKTL8mAhUTbyKXS5tSTn
not agree, got:
?error=nvalid_request&
&error_description=The+request+is+missing+a+required+parameter:+client_id.

#2
https://graph.renren.com/oauth/token?grant_type=authorization_code
&client_id=f3ef44ed9a76490a89d137dbf749af55&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2F
&client_secret=be16f097be0d4b42bead5726604853f7
&code=LABMvxcZy7ZTGu1tOCPJRGaVikgpV8oy

https://graph.renren.com/oauth/token?grant_type=authorization_code&client_id=f3ef44ed9a76490a89d137dbf749af55&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2F&client_secret=be16f097be0d4b42bead5726604853f7&code=LABMvxcZy7ZTGu1tOCPJRGaVikgpV8oy

got:
{"expires_in":2592325,
"refresh_token":"176681|0.a2QqomnEAufn45F0j50J6srV4kWGjNqa.227366242",
"user":{
	"id":227366242,
	"name":"xxx Ken",
	"avatar":[
		{"type":"avatar","url":"http:\/\/hdn.xnimg.cn\/photos\/hdn521\/20110614\/2225\/h_head_3g4R_5f890000d98a2f75.jpg"},
		{"type":"tiny","url":"http:\/\/hdn.xnimg.cn\/photos\/hdn221\/20110614\/2225\/tiny_W9ER_219838k019118.jpg"},
		{"type":"main","url":"http:\/\/hdn.xnimg.cn\/photos\/hdn521\/20110614\/2225\/h_main_O0oa_5f890000d98a2f75.jpg"},
		{"type":"large","url":"http:\/\/hdn.xnimg.cn\/photos\/hdn521\/20110614\/2225\/h_large_0tS6_5f890000d98a2f75.jpg"}
		]
},
"access_token":"176681|6.3dfba441cd6a3f01ed389aa0dff05361.2592000.1329195600-227366242"
}

or:
{"error": "invalid_request", 
"error_description": "The request is missing a required parameter: client_id"}
"""
	
from oauth2client.client import OAuth2WebServerFlow



def rr_flow():    
    return OAuth2WebServerFlow(
        # Visit https://code.google.com/apis/console to
        # generate your client_id, client_secret and to
        # register your redirect_uri.
        auth_uri='https://graph.renren.com/oauth/authorize',
        token_uri='https://graph.renren.com/oauth/token',
        client_id='f3ef44ed9a76490a89d137dbf749af55',
        client_secret='be16f097be0d4b42bead5726604853f7',
        scope='read_user_status',
        user_agent='buzz-cmdline-sample/1.0')

def goog_flow():        
    return OAuth2WebServerFlow(
        # Visit https://code.google.com/apis/console to
        # generate your client_id, client_secret and to
        # register your redirect_uri.
        client_id='',
        client_secret='',
        scope='read_user_status',
        user_agent='buzz-cmdline-sample/1.0')
        
@app.route('/login')
def login():
    callback = 'http://127.0.0.1:5000/auth_return'
    authorize_url = rr_flow().step1_get_authorize_url(callback)
    #memcache.set(user.user_id(), pickle.dumps(flow))
    # print 'callback', callback
    print 'step1', authorize_url
    return redirect(authorize_url)

@app.route('/auth_return')
def auth_return():
    http=httplib2.Http(disable_ssl_certificate_validation=True)
    try:
        credentials,d = rr_flow().step2_exchange(request.args['code'], http)
        return repr(d) #credentials.to_json()
    except:
        return ''

@app.route('/dump')
def dump():
	return "dump: %r" % request.args
	
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
    logging.basicConfig(level=logging.DEBUG)
    
    app.debug = True    
    app.run(host='0.0.0.0',threaded=True)
