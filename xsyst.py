#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author   Bram van Oploo
# @email    info@sudo-systems.com
# @date     2013-03-30
# @version  1.0.0 alpha 2
#

import json
import types
import urllib.request
import urllib.parse
import urllib.error
import sys
import os
from functools import wraps
from inspect import stack
from os import path
from flask import Flask, render_template, request, Response, redirect, send_file
from werkzeug import secure_filename
from System import *

root_path = os.path.abspath(os.path.dirname(__file__)) + '/'
filesystem.create_directory(root_path + 'logs')
filesystem.create_directory(root_path + 'static/backups')
filesystem.create_directory(root_path + 'database')

app = Flask(__name__)


def check_auth(username, password):
    return username == 'admin' and password == 'xsyst'


def authenticate():
    return Response('Please enter your credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def is_method(method_name):
    try:
        ret = type(eval(method_name))
        return ret in (types.FunctionType, types.BuiltinFunctionType)
    except AttributeError:
        return False


@app.route('/')
@requires_auth
def index():
    return redirect('/system_info', 301)


@app.route('/update')
@requires_auth
def update():
    return 'Updated' if application.update() else 'Error updating'


@app.route('/xbmc_repositories')
@requires_auth
def xbmc_repositories():
    return render_template('xbmc_repositories.html')


@app.route('/xbmc_backups')
@requires_auth
def xbmc_backups():
    return render_template('xbmc_backups.html',
        xbmc_dir_size=helper.get_readable_size(
            filesystem.get_directory_size(config.xbmc_home_dir)),
            backups=xbmc.get_existing_backup_url_paths())


@app.route('/xbmc_backups/download/<path:filename>')
@requires_auth
def download_backup(filename):
    return send_file(config.xbmc_backups_dir + filename, as_attachment=True)


@app.route('/addon_repositories')
@requires_auth
def addon_repositories():
    return render_template('addon_repositories.html',
        repositories=xbmc.get_installable_repositories())


@app.route('/system_info')
@requires_auth
def system():
    return render_template('system_info.html',
        os=ubuntu.get_version(),
        kernel=ubuntu.get_kernel_version(),
        gpu_manufacturer=hardware.get_gpu_manufacturer(),
        gpu_type=hardware.get_gpu_type(),
        resolution=hardware.get_current_resolution(),
        cpu_type=hardware.get_cpu_type(),
        cpu_core_count=hardware.get_cpu_core_count(),
        cpu_load=hardware.get_cpu_load(),
        total_ram=hardware.get_total_ram(),
        ram_in_use=hardware.get_ram_in_use())


@app.route('/prepare_system')
@requires_auth
def prepare_system():
    #db.set('installation_steps', 'prepare_system', 1)
    return render_template('prepare_system.html')


@app.route('/about')
@requires_auth
def about():
    return render_template('about.html',
        application_version=application.get_version())


@app.route('/config')
@requires_auth
def config():
    return render_template('config.html')


@app.route('/system_tools')
@requires_auth
def system_tools():
    return render_template('system_tools.html')


@app.route('/upload_backup', methods=['POST'])
@requires_auth
def upload_backup():
    backup_file = request.files['backup_file']
    backup_file_name = secure_filename(backup_file.filename)
    backup_file.save(path.join(config.xbmc_backups_dir, backup_file_name))
    return redirect('/xbmc_backups', 301)


@app.route('/api')
@requires_auth
def api():
    result = {
        'success': False,
        'message': 'Request not executed (' + urllib.parse.unquote(request.args['method'])
            + '(' + urllib.parse.unquote(request.args['params']) + '))'
    }
    if 'method' in request.args and is_method('' + urllib.parse.unquote(request.args['method'])):
        full_request = None
        if 'params' in request.args and request.args['params'] != '':
            full_request = '' + urllib.parse.unquote(request.args['method'])
            + '(' + urllib.parse.unquote(request.args['params']) + ')'
        else:
            full_request = '' + urllib.parse.unquote(request.args['method']) + '()'

        log.debug('request:' + full_request, stack()[0][3])
        try:
            data = eval(full_request)
            if isinstance(data, bool):
                if not data:
                    result = {
                        'success': False,
                        'message': 'An unknown error occurred'
                    }
                else:
                    result = {
                        'success': True,
                        'result': True
                    }
            else:
                result = {
                    'success': True,
                    'result': data
                }
        except AttributeError as e1:
            log.error(str(e1), stack()[0][3])
            result = {
                'success': False,
                'message': 'Illegal request: Attribute error (' + str(e1) + ')'
            }
        except TypeError as e2:
            log.error(str(e2), stack()[0][3])
            result = {
                'success': False,
                'message': 'Illegal request: Type error (' + str(e2) + ')'
            }
        except NameError as e3:
            log.error(str(e3), stack()[0][3])
            result = {
                'success': False,
                'message': 'Illegal Request: Name error (' + str(e3) + ')'
            }
        except:
            log.error('An unknown error occurred', stack()[0][3])
            result = {
                'success': False,
                'message': 'An unknown error occurred'
            }
    json_result = json.dumps(result)
    log.debug('result:' + json_result, stack()[0][3])
    response = Response(json_result, status=200, mimetype='application/json')
    return response

try:
    server_port = sys.argv[1]
except:
    server_port = "8092"
    pass

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(server_port), debug=True)
