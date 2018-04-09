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
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# set a secret key
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@35.227.79.146/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@35.227.79.146/proj1part2"
#
DATABASEURI = "postgresql://user:password@35.227.79.146/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


def format_sql_request(tablename, attributes="*", condition="*"):
  '''
  format a select query given table name, attributes to select, and condition
  '''
  return "SELECT {} FROM {} WHERE {}".format(tablename, tuples, attributes)


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
    import traceback; traceback.print_exc()
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


@app.route('/build_index')
def build_index():
  '''
  wrapper for build index page
  '''


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args

  # log in information
  if 'username' in session:
    print 'Logged in as {}'.format(escape(session['username'])) #may need to remove escape function
  else:
    print 'Not logged in'

  #
  # example of a database query
  #
  # cursor = g.conn.execute("SELECT name FROM test")
  # names = []
  # for result in cursor:
  #   names.append(result['name'])  # can also be accessed using result[0]
  # cursor.close()

  # let us grab all builds from database:
  all_builds = []
  cursor = g.conn.execute("SELECT * FROM builds")
  for result in cursor:
    curr_build = {}
    build_id = result['build_id']
    curr_build['build_name'] = result['build_name']

    # select names of parts using id in build
    cursor2 = g.conn.execute("SELECT cpu_name FROM cpu WHERE cpu_id == {}".format(result['cpu_id']))
    for result2 in cursor2:
      curr_build['cpu_name'] = result['cpu_name']

    cursor2 = g.conn.execute("SELECT mobo_name FROM motherboard WHERE mobo_id == {}".format(result['mobo_id']))
    for result2 in cursor2:
      curr_build['mobo_name'] = result['mobo_name']

    cursor2 = g.conn.execute("SELECT psu_name FROM psu WHERE psu_id == {}".format(result['psu_id']))
    for result2 in cursor2:
      curr_build['psu_name'] = result['psu_name']

    cursor2 = g.conn.execute("SELECT case_name FROM case WHERE case_id == {}".format(result['case_id']))
    for result2 in cursor2:
      curr_build['case_name'] = result['case_name']

    # select names of parts using has_gpu, has_memory, and has_storage
    curr_build['gpu_name'] = []
    cursor2 = g.conn.execute("SELECT g.gpu_name FROM gpu g, has_gpu hg WHERE g.gpu_id == hg.gpu_id AND hg.build_id == {}".format(result['build_id']))
    for result2 in cursor2:
      curr_build['gpu_name'].append(result['gpu_name'])

    curr_build['mem_name'] = []
    cursor2 = g.conn.execute("SELECT m.mem_name FROM memory m, has_memory hm WHERE m.mem_id == hm.mem_id AND hm.build_id == {}".format(result['build_id']))
    for result2 in cursor2:
      curr_build['mem_name'].append(result['mem_name'])

    cursor2 = g.conn.execute("SELECT s.sto_name FROM storage s, has_storage hs WHERE s.sto_id == hs.sto_id AND hs.build_id == {}".format(result['build_id']))
    for result2 in cursor2:
      curr_build['sto_name'] = result['sto_name']

    all_builds.append(curr_build)
  cursor.close

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(builds = all_builds)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)


@app.route('/login', methods = ['GET', 'POST'])
def login():
  '''
  '''
  # if submitting form for login
  if request.method == 'POST':
    session['username'] = request.form['username']
    return redirect(url_for('index'))
  # if trying to get login page
  else:
    return '''
        <form method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''

@app.route('/logout')
def logout():
  '''
  '''
  session.pop('username', None)
  return redirect(url_for('index'))


# Start adding new build to database - keep in session until submitted, so that requirements can be checked.
@app.route('/add_new_build', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


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
