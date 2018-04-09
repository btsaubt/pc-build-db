#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash


tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
# set a secret key
app.secret_key = 'l\xbd!\xeaN\xc8\x16r\xa3:\xa4\xc9\x15\xea\xc9)\xcd\xd3\xd0\x1a\xab6\xe3\x89'
DATABASEURI = "postgresql://kf2448:2558@35.227.79.146/proj1part2"
engine = create_engine(DATABASEURI)


# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request 
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print "uh oh, problem connecting to database"
        import traceback
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


@app.route('/cpu_index')
def cpu_index():
    '''
    get all CPU ids and information from sql table
    '''

    all_cpus = []
    all_ids = []
    cursor = g.conn.execute("SELECT * FROM cpu")
    for result in cursor:
        all_cpus.append('<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>'.
                        format(result['cpu_name'], result['speed'], result['cores'],
                               result['tdp'], result['price']))
        all_ids.append(result['cpu_id'])

    context = dict(cpus=all_cpus, cpu_ids=all_ids)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("cpu_index.html", **context)


@app.route('/build_index')
def build_index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print request.args

    # let us grab all builds from database and build a table row:
    all_builds = []
    cursor = g.conn.execute("SELECT * FROM builds")
    for result in cursor:
        curr_build = ''
        build_id = result['build_id']
        curr_build = '<td>{}</td>'.format(result['build_name'])
        curr_price = 0

        # select names of parts using id in build
        cursor2 = g.conn.execute(
            "SELECT cpu_name, price FROM cpu WHERE cpu_id = {}".format(result['cpu_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result['cpu_name'])
            curr_price += result['price']
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT mobo_name, price FROM motherboard WHERE mobo_id = {}".format(result['mobo_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result['mobo_name'])
            curr_price += result['price']
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT psu_name, price FROM psu WHERE psu_id = {}".format(result['psu_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result['psu_name'])
            curr_price += result['price']
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT case_name, price FROM case WHERE case_id = {}".format(result['case_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result['case_name'])
            curr_price += result['price']
        cursor2.close()

        # select names of parts using has_gpu, has_memory, and has_storage
        cursor2 = g.conn.execute(
            "SELECT g.gpu_name, g.price FROM gpu g, has_gpu hg WHERE g.gpu_id = hg.gpu_id AND hg.build_id = {}".format(result['build_id']))
        curr_build += "<td>"
        counter = 0
        for result2 in cursor2:
            counter += 1
            curr_build['gpu_name'].append(result['gpu_name'])
            curr_build += "{}".format(result['gpu_name'])
            if counter != 1:
                curr_build += "<br />"  # different gpus lie on same line
            curr_price += result['price']
        curr_build += "</td>"
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT m.mem_name, m.price FROM memory m, has_memory hm WHERE m.mem_id = hm.mem_id AND hm.build_id = {}".format(result['build_id']))
        curr_build += "<td>"
        counter = 0
        for result2 in cursor2:
            counter += 1
            curr_build['mem_name'].append(result['mem_name'])
            curr_build += "{}".format(result['mem_name'])
            if counter != 1:
                curr_build += "<br />"  # different gpus lie on same line
            curr_price += result['price']
        curr_build += "</td>"
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT s.sto_name, s.price FROM storage s, has_storage hs WHERE s.sto_id = hs.sto_id AND hs.build_id = {}".format(result['build_id']))
        curr_build += "<td>"
        counter = 0
        for result2 in cursor2:
            counter += 1
            curr_build['sto_name'].append(result['sto_name'])
            curr_build += "{}".format(result['sto_name'])
            if counter != 1:
                curr_build += "<br />"  # different gpus lie on same line
            curr_price += result['price']
        curr_build += "</td>"
        cursor2.close()

        curr_build += "<td>{}</td>".format(curr_price)

        all_builds.append(curr_build)
    cursor.close

    context = dict(builds=all_builds)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


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
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    '''
    pop user from users logged in
    '''
    session.pop('logged in', None)
    flash('you were logged in')
    return redirect(url_for('index'))


# Start adding new build to database - keep in session until submitted, so that requirements can be checked.
@app.route('/add_new_build', methods=['POST'])
def add():
    name = request.form['name']
    g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
    return redirect('/')


@app.route('/')
def index():
    return redirect(url_for('build_index'))
    # return render_template("index.html")


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help

        """

        HOST, PORT = host, port
        print "running on %s:%d" % (HOST, PORT)
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()
