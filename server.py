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
import sys
# import logging
import click
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
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'),
# ('ada lovelace');""")


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request (every time you enter an address in
    the web browser).

    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except Exception as err:
        print "uh oh, problem connecting to database:"
        print err
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        print exception
        g.conn.close()
    except Exception as err:
        print err


@app.route('/cpu_index')
def cpu_index():
    """
    get all CPU ids and information from sql table - if socket correct
    """

    all_cpus = []
    all_ids = []
    query = '''SELECT DISTINCT c.cpu_id, c.cpu_name, c.speed, c.cores, c.tdp, c.price FROM cpu c,
 cpu_sockets cs WHERE cs.mobo_id = {} AND c.cpu_id = cs.cpu_id'''.format(
        session['mobo_id']) if session['socket'] else "SELECT * FROM cpu"
    print >> sys.stderr, query

    cursor = g.conn.execute(query)
    for result in cursor:
        all_cpus.append('<td>{}</td><td>{}GHz</td><td>{}</td><td>{}W</td><td>${}</td>'.format(
            result['cpu_name'], result['speed'], result['cores'], result['tdp'], result['price']))
        all_ids.append(result['cpu_id'])

    context = dict(cpus=zip(all_cpus, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("cpu_index.html", **context)


@app.route('/motherboard_index')
def motherboard_index():
    """
    get all mobos ids and information from sql table
    """

    all_mobos = []
    all_ids = []

    form_conditional = ''
    if session['form_factor']:
        if 'case_id' in session:
            form_conditional = ' AND ff.case_id = {}'.format(session['case_id'])
        if 'psu_id' in session:
            form_conditional += ' AND ff.psu_id = {}'.format(session['psu_id'])

    query = '''SELECT DISTINCT m.mobo_id, m.mobo_name, m.ram_slots, m.price FROM motherboard m,
 cpu_sockets cs, form_compatible ff WHERE cs.cpu_id = {} AND m.mobo_id = cs.mobo_id'''.format(
            session['cpu_id']) if session['socket'] else "SELECT * FROM motherboard"

    query = "{} AND ram_slots > {} {}".format(query, session['cur_mem_slots'], form_conditional)
    print >> sys.stderr, query

    cursor = g.conn.execute(query)
    for result in cursor:
        all_mobos.append('<td>{}</td><td>{}</td><td>${}</td>'.format(result['mobo_name'],
                                                                     result['ram_slots'],
                                                                     result['price']))
        all_ids.append(result['mobo_id'])

    context = dict(mobos=zip(all_mobos, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("motherboard_index.html", **context)


@app.route('/psu_index')
def psu_index():
    """
    get all PSU ids and information from sql table
    """

    all_psus = []
    all_ids = []


    form_conditional = ''
    if session['form_factor']:
        form_conditional = 'WHERE '
        if 'case_id' in session:
            form_conditional = 'ff.case_id = {}'.format(session['case_id'])
        if 'gpu_id' in session:
            form_conditional += ' {}} ff.gpu_id = {}'.format('AND' if 'case_id' in session else '',
                session['gpu_id'])

    query = '''SELECT DISTINCT p.psu_id, p.psu_name p.series, p.efficiency, p.watts, p.modular,
 p.price FROM psu p, form_compatible ff {}'''.format(form_conditional)
    print >> sys.stderr, query

    cursor = g.conn.execute(query)
    for result in cursor:
        all_psus.append('<td>{}</td><td>{}</td><td>{}</td><td>{}W</td><td>{}</td><td>${}</td>'.
                        format(result['psu_name'], result['series'], result['efficiency'],
                               result['watts'], result['modular'], result['price']))
        all_ids.append(result['psu_id'])

    context = dict(psus=zip(all_psus, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("psu_index.html", **context)


@app.route('/case_index')
def case_index():
    """
    get all case ids and information from sql table
    """

    all_cases = []
    all_ids = []


    form_conditional = ''
    if session['form_factor']:
        form_conditional = 'WHERE '
        if 'psu_id' in session:
            form_conditional = 'ff.psu_id = {}'.format(session['psu_id'])
        if 'gpu_id' in session:
            form_conditional += ' {}} ff.gpu_id = {}'.format('AND' if 'psu_id' in session else '',
                session['gpu_id'])

    query = '''SELECT DISTINCT c.case_id, c.case_name, c.type, c.ext_bays, c.int_bays, c.price FROM
 cases c, form_compatible ff {}'''.format(form_conditional)
    print >> sys.stderr, query

    cursor = g.conn.execute(query)
    for result in cursor:
        all_cases.append('<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>${}</td>'.
                         format(result['case_name'], result['type'], result['ext_bays'],
                                result['int_bays'], result['price']))
        all_ids.append(result['case_id'])

    context = dict(cases=zip(all_cases, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("case_index.html", **context)


@app.route('/gpu_index')
def gpu_index():
    """
    get all GPU ids and information from sql table
    """

    all_gpus = []
    all_ids = []
    cursor = g.conn.execute("SELECT * FROM gpu")
    for result in cursor:
        all_gpus.append('''<td>{}</td><td>{}</td><td>{}</td><td>{}GHz</td><td>{}W</td><td>{}GB</td>
<td>${}</td>'''.format(result['gpu_name'], result['series'], result['chipset'],
                       result['core_clock'], result['tdp'], result['gpu_mem'], result['price']))
        all_ids.append(result['gpu_id'])

    context = dict(gpus=zip(all_gpus, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("gpu_index.html", **context)


@app.route('/memory_index')
def memory_index():
    """
    get all memory ids and information from sql table
    """

    all_mems = []
    all_ids = []
    cursor = g.conn.execute("SELECT * FROM memory WHERE module_num < {}".format(
                            session['max_mem_slots'] - session['cur_mem_slots']))
    for result in cursor:
        all_mems.append('<td>{}</td><td>{}</td><td>{}</td><td>{}GB</td><td>{}</td><td>${}</td>'.
                        format(result['mem_name'], result['speed'], result['cas'],
                               result['module_size'], result['module_num'], result['price']))
        all_ids.append(result['mem_id'])

    context = dict(mems=zip(all_mems, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("memory_index.html", **context)


@app.route('/storage_index')
def storage_index():
    """
    get all storage ids and information from sql table
    """

    all_stos = []
    all_ids = []
    cursor = g.conn.execute("SELECT * FROM storage")
    for result in cursor:
        all_stos.append('''<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}GB</td><td>{}</td>
<td>${}</td>'''.format(result['sto_name'], result['series'], result['form'], result['type'],
                       result['capacity'], result['cache'] if "{}MB".format(result['cache']) is
                       not None else '', result['price']))
        all_ids.append(result['sto_id'])

    context = dict(stos=zip(all_stos, all_ids))

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("storage_index.html", **context)


@app.route('/current_build')
def current_build():
    """
    show current parts in build
    """
    print >> sys.stderr, 'showing build {}'.format(session['build_name'])

    context = dict(build_name=session['build_name'])
    curr_price = 0

    if 'cpu_id' in session:
        cursor2 = g.conn.execute(
            "SELECT cpu_name, price FROM cpu WHERE cpu_id = {}".format(session['cpu_id']))
        for result2 in cursor2:
            context['cpu_name'] = result2['cpu_name']
            curr_price += result2['price']
        cursor2.close()
    else:
        context['cpu_name'] = "No CPU selected"

    if 'mobo_id' in session:
        cursor2 = g.conn.execute(
            "SELECT mobo_name, price, ram_slots FROM motherboard WHERE mobo_id = {}".
            format(session['mobo_id']))
        for result2 in cursor2:
            context['mobo_name'] = result2['mobo_name']
            session['max_mem_slots'] = result2['ram_slots']
            curr_price += result2['price']
        cursor2.close()
    else:
        context['mobo_name'] = "No motherboard selected"

    if 'psu_id' in session:
        cursor2 = g.conn.execute(
            "SELECT psu_name, price FROM psu WHERE psu_id = {}".format(session['psu_id']))
        for result2 in cursor2:
            context['psu_name'] = result2['psu_name']
            curr_price += result2['price']
        cursor2.close()
    else:
        context['psu_name'] = "No power supply selected"

    if 'case_id' in session:
        cursor2 = g.conn.execute(
            "SELECT case_name, price FROM cases WHERE case_id = {}".format(session['case_id']))
        for result2 in cursor2:
            context['case_name'] = result2['case_name']
            curr_price += result2['price']
        cursor2.close()
    else:
        context['case_name'] = "No case selected"

    # select names of parts using has_gpu, has_memory, and has_storage
    if 'gpu_ids' in session:
        all_gpu_ids = ''
        for gid in session['gpu_ids']:
            all_gpu_ids += ' OR gpu_id = {}'.format(gid)
        all_gpu_ids = all_gpu_ids[4:]
        gpu_names = []
        cursor2 = g.conn.execute(
            'SELECT gpu_name, gpu_id price FROM gpu WHERE {}'.format(all_gpu_ids))
        for result2 in cursor2:
            gpu_names.append((result2['gpu_name'], result2['gpu_id']))
            curr_price += result2['price']
        context['gpu_name'] = gpu_names
        cursor2.close()
    else:
        context['gpu_name'] = [("No graphics card selected", -1)]

    if 'mem_ids' in session:
        all_mem_ids = ''
        for mid in session['mem_ids']:
            all_mem_ids += ' OR mem_id = {}'.format(mid)
        all_mem_ids = all_mem_ids[4:]
        mem_names = []
        cursor2 = g.conn.execute(
            'SELECT mem_name, mem_id, price, module_num FROM memory WHERE {}'.format(all_mem_ids))
        for result2 in cursor2:
            mem_names.append((result2['mem_name'], result2['mem_id']))
            curr_price += result2['price']
            session['cur_mem_slots'] += result2['module_num']
        context['mem_name'] = mem_names
        cursor2.close()
    else:
        context['mem_name'] = [("No memory selected", -1)]

    if 'sto_ids' in session:
        all_sto_ids = ''
        for sid in session['sto_ids']:
            all_sto_ids += ' OR sto_id = {}'.format(sid)
        all_sto_ids = all_sto_ids[4:]
        sto_names = []
        cursor2 = g.conn.execute(
            'SELECT sto_name, sto_id, price FROM storage WHERE {}'.format(all_sto_ids))
        for result2 in cursor2:
            sto_names.append((result2['sto_name'], result2['sto_id']))
            curr_price += result2['price']
        context['sto_name'] = sto_names
        cursor2.close()
    else:
        context['sto_name'] = [("No storage selected", -1)]

    context['total_cost'] = curr_price

    # context = dict(build_name=session['build_name'], cpu_name='cpu name', mobo_name='mobo name',
    #                psu_name='psu name', case_name='case name', gpu_name='gpu name',
    #                mem_name='memory name', sto_name='storage name', total_cost=0)

    return render_template("current_build.html", **context)


# Start adding new build to database - keep in session until submitted, so that requirements can be
# checked.
@app.route('/add_new_build', methods=['POST'])
def add_new_build():
    """
    add a new build to database (only have name of build at this point)
    """
    session['build_name'] = request.form['BuildName']
    # check if this fails if cpu_id is already nonexistent/popped

    print >> sys.stderr, 'trying to build {}'.format(session['build_name'])

    if 'cpu_id' in session:
        session.pop('cpu_id', None)
    if 'mobo_id' in session:
        session.pop('mobo_id', None)
    if 'psu_id' in session:
        session.pop('psu_id', None)
    if 'case_id' in session:
        session.pop('case_id', None)
    if 'gpu_ids' in session:
        session.pop('gpu_ids', None)
    if 'mem_ids' in session:
        session.pop('mem_ids', None)
    if 'sto_ids' in session:
        session.pop('sto_ids', None)
    session['max_mem_slots'] = 8
    session['cur_mem_slots'] = 0
    session['socket'] = False
    session['form_factor'] = False

    return redirect(url_for('current_build'))


@app.route('/add_cpu', methods=['POST'])
def add_cpu():
    """
    add cpu to session, redirect to current_build
    """
    session['cpu_id'] = request.form['cpu_id']
    session['socket'] = True
    return redirect(url_for('current_build'))


@app.route('/add_mobo', methods=['POST'])
def add_mobo():
    """
    add mobo to session, redirect to current_build
    """
    session['mobo_id'] = request.form['mobo_id']
    session['socket'] = True
    session['form_factor'] = True

    return redirect(url_for('current_build'))


@app.route('/add_psu', methods=['POST'])
def add_psu():
    """
    add psu to session, redirect to current_build
    """
    session['psu_id'] = request.form['psu_id']
    session['form_factor'] = True
    return redirect(url_for('current_build'))


@app.route('/add_case', methods=['POST'])
def add_case():
    """
    add case to session, redirect to current_build
    """
    session['case_id'] = request.form['case_id']
    session['form_factor'] = True
    return redirect(url_for('current_build'))


# ************************FOR THESE ADD TO A LIST IF NOT ALREADY INSIDE*****************************
@app.route('/add_gpu', methods=['POST'])
def add_gpu():
    """
    add gpu to session, redirect to current_build
    """
    session['gpu_id'] = request.form['gpu_id']
    return redirect(url_for('current_build'))


# ************************FOR THESE ADD TO A LIST IF NOT ALREADY INSIDE*****************************
@app.route('/add_mem', methods=['POST'])
def add_mem():
    """
    add memory to session, redirect to current_build
    """
    # if not enough ram slots, redirect as error and flash message

    # if enough ram slots, add to build
    session['mem_id'] = request.form['mem_id']
    return redirect(url_for('current_build'))


# ************************FOR THESE ADD TO A LIST IF NOT ALREADY INSIDE*****************************
@app.route('/add_sto', methods=['POST'])
def add_sto():
    """
    add storage to session, redirect to current_build
    """
    session['sto_id'] = request.form['sto_id']
    return redirect(url_for('current_build'))


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
    all_build_ids = []
    cursor = g.conn.execute("SELECT * FROM builds")
    for result in cursor:
        curr_build = ''
        all_build_ids.append(result['build_id'])
        curr_build = '<td>{}</td>'.format(result['build_name'])
        curr_price = 0

        # select names of parts using id in build
        cursor2 = g.conn.execute(
            "SELECT cpu_name, price FROM cpu WHERE cpu_id = {}".format(result['cpu_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result2['cpu_name'])
            curr_price += result2['price']
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT mobo_name, price FROM motherboard WHERE mobo_id = {}".format(result['mobo_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result2['mobo_name'])
            curr_price += result2['price']
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT psu_name, price FROM psu WHERE psu_id = {}".format(result['psu_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result2['psu_name'])
            curr_price += result2['price']
        cursor2.close()

        cursor2 = g.conn.execute(
            "SELECT case_name, price FROM cases WHERE case_id = {}".format(result['case_id']))
        for result2 in cursor2:
            curr_build += " <td>{}</td>".format(result2['case_name'])
            curr_price += result2['price']
        cursor2.close()

        # select names of parts using has_gpu, has_memory, and has_storage
        cursor2 = g.conn.execute(
            '''SELECT g.gpu_name, g.price FROM gpu g, has_gpu hg WHERE g.gpu_id = hg.gpu_id AND
 hg.build_id = {}'''.format(result['build_id']))
        curr_build += "<td>"
        counter = 0
        for result2 in cursor2:
            counter += 1
            curr_build += "{}".format(result2['gpu_name'])
            if counter != 1:
                curr_build += "<br />"  # different gpus lie on same line
            curr_price += result2['price']
        curr_build += "</td>"
        cursor2.close()

        cursor2 = g.conn.execute(
            '''SELECT m.mem_name, m.price FROM memory m, has_memory hm WHERE m.mem_id = hm.mem_id
 AND hm.build_id = {}'''.format(result['build_id']))
        curr_build += "<td>"
        counter = 0
        for result2 in cursor2:
            counter += 1
            curr_build += "{}".format(result2['mem_name'])
            if counter != 1:
                curr_build += "<br />"  # different gpus lie on same line
            curr_price += result2['price']
        curr_build += "</td>"
        cursor2.close()

        cursor2 = g.conn.execute(
            '''SELECT s.sto_name, s.price FROM storage s, has_storage hs WHERE s.sto_id = hs.sto_id
 AND hs.build_id = {}'''.format(result['build_id']))
        curr_build += "<td>"
        counter = 0
        for result2 in cursor2:
            counter += 1
            curr_build += "{}".format(result2['sto_name'])
            if counter != 1:
                curr_build += "<br />"  # different gpus lie on same line
            curr_price += result2['price']
        curr_build += "</td>"
        cursor2.close()

        curr_build += "<td>${}</td>".format(curr_price)

        all_builds.append(curr_build)
    cursor.close()

    context = dict(builds=all_builds, build_ids=all_build_ids)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("build_index.html", **context)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    login POST/GET method for this app
    """
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
    """
    pop user from users logged in
    """
    session.pop('logged_in', None)
    flash('you were logged out')
    return redirect(url_for('index'))


@app.route('/')
def index():
    '''
    default index page - shown only if not logged in
    '''
    # if not logged in show index.html
    # return render_template("index.html")

    # if logged in go to builds
    return redirect(url_for('build_index'))


if __name__ == "__main__":

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
