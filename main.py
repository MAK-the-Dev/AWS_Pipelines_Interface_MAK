from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import boto3
import time
from time import sleep
from threading import Thread, Event
from datetime import datetime

################ Configurations Starts #################

# Intialize Flask
app = Flask(__name__)
'''
# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'
'''
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mak123'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

# Intialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
################ Configurations Ends #################

# Intialize boto3 client
client = boto3.client('codepipeline')
info = client.list_pipelines()
aws_pipeline_names = []

# Intialize Thread
thread = Thread()
thread_stop_event = Event()

for element in info['pipelines']:
    aws_pipeline_names.append(element['name'])
    print(aws_pipeline_names)
    # str = str + element['name'] + " , "

#Thread Class For Continuous Status Fetch
class RandomThread(Thread):
    def __init__(self,name,response):
        Thread.__init__(self)
        self.name=name
        self.response=response
        self.delay = 1
        # super(RandomThread, self).__init__()

    def randomStatusRequestor(self):

        while not thread_stop_event.isSet():
            info = client.get_pipeline_execution(pipelineName=self.name, pipelineExecutionId=self.response)
            status = str(info['pipelineExecution']['status'])
            socketio.emit('newStatus', {'status': status, 'name': self.name}, namespace='/test')
            sleep(self.delay)
            print(status)
            if status != "InProgress":
                thread_stop_event.set()
                print("Final State:" + "  " + info['pipelineExecution']['status'])
    def run(self):
        self.randomStatusRequestor()

#SocketIO Event Starts
@socketio.on('my-event', namespace='/test')
def test_connect(name,response):
    i=0
    threadCount= "thread " + str(i)
    print("Starting ",threadCount)
    thread = RandomThread(name, response)
    thread.start()
    i= i+1

#SocketIO Event Ends
@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

#Utility function for history summary of last 10 executions
def get_pipeline_last_execution_count(name):

    response = client.list_pipeline_executions(
        pipelineName=name,
        maxResults=10,
        # nextToken='string'
    )
    pName=name
    print(response)
    pToken = response['nextToken']
    print(pToken)
    newReturnList = []

    for key, values in response.items():
        # print(key, values)
        if key=='pipelineExecutionSummaries':
            for value in values:
                # print(value)
                for key_value, values_value in value.items():
                    if key_value=='status':
                        pStatus = values_value
                        # print(pStatus)
                        newReturnList.append((pStatus))
    # print(newReturnList)
    fCount=newReturnList.count("Failed")
    # print(fCount)
    sCount=newReturnList.count("Succeeded")
    # print(sCount)
    supCount = newReturnList.count("Superseded")
    # print(supCount)
    emptyString="&nbsp;"

    return emptyString, fCount, sCount, supCount, emptyString

#Utility function for history of last 10 executions
def get_pipeline_all_run_history(name):

    response = client.list_pipeline_executions(
        pipelineName=name,
        maxResults=10,
        #nextToken='string'
    )
    pName=name
    print(response)
    pToken = response['nextToken']
    print(pToken)
    returnList = []

    for key, values in response.items():
        # print(key, values)
        if key=='pipelineExecutionSummaries':
            for value in values:
                # print(value)
                for key_value, values_value in value.items():
                    if key_value=='pipelineExecutionId':
                        pPipelineExecutionId = values_value
                        # print(pPipelineExecutionId)
                    elif key_value=='status':
                        pStatus = values_value
                        # print(pStatus)
                    elif key_value == 'startTime':
                        pStartTime = values_value
                        # print(pStartTime)
                    elif key_value == 'lastUpdateTime':
                        pLastUpdateTime = values_value
                        # print(pLastUpdateTime)
                        returnList.append(("&nbsp;", pName, pPipelineExecutionId, pStatus, pStartTime, pLastUpdateTime, "&nbsp;"))
    # print(returnList)
    return returnList

#UnUsed Utility Function for detailed history of pipeline last execution
def get_pipeline_history(name):
    response = client.get_pipeline_state(
        name=name
    )
    print(response)
    pName = response['pipelineName']
    print(pName)
    pVersion = response['pipelineVersion']
    print(pVersion)

    for key, values in response.items():
        # print(key, values)
        if key=='stageStates':
            for value in values:
                # print(value)
                for key_value, values_value in value.items():
                    if key_value=='actionStates':
                        # print(values_value)
                        for val in values_value:
                            # print(val)
                            for key_val, values_val in val.items():
                                if key_val=='latestExecution':
                                    # print(values_val)
                                    for key_in_val, val_in_val in values_val.items():
                                       # print(key_in_val, val_in_val)
                                        if key_in_val=='status':
                                            pStatus = val_in_val
                                        elif key_in_val=='summary':
                                            pSummary = val_in_val
                                        elif key_in_val=='lastStatusChange':
                                            pLastStatusChange= val_in_val

    pCreated = response['created']
    pUpdated = response['updated']

    # msg = 'This is just a msg!'
    # Show message (if any)
    # return msg
    return pName, pVersion, pStatus, pSummary, pLastStatusChange, pCreated, pUpdated

#Utility function for Time
@app.route("/getTime", methods=['GET'])
def getTime():
    print("browser time: ", request.args.get("time"))
    print("server time : ", time.strftime('%A %B, %d %Y %H:%M:%S'));
    return "Done"

#Start pipeline Function Used in button url
@app.route('/start_pipeline/<string:name>', methods=['GET', 'POST'])
@app.route('/start_pipeline/<string:name>/<string:environmentName>', methods=['GET', 'POST'])
def start_pipeline(name,environmentName='Anonymous'):
    response = client.start_pipeline_execution(
        name=name
    )
    print(response)
    print(response['pipelineExecutionId'])
    time.sleep(20)
    print("sleep over")
    info = client.get_pipeline_execution(
        pipelineName=name,
        pipelineExecutionId=response['pipelineExecutionId']
    )
    now = datetime.now()
    #SocketIO Connection Call
    test_connect(name,  response['pipelineExecutionId'])
    if(environmentName=='Anonymous'):
        return redirect(url_for('home', nowTime=now,nowPipeline=name))
    elif(environmentName=='T'):
        return redirect(url_for('show_pipeline', environmentName=environmentName, nowTime=now,nowPipeline=name))
    elif(environmentName=='P'):
        return redirect(url_for('show_pipeline', environmentName=environmentName, nowTime=now, nowPipeline=name))
    # return "Final State:" + "               " + info['pipelineExecution']['status']
    # return Response(stream_with_context(start_pipeline(name)))

'''
#Old Start Pipeline Function
@app.route('/start_pipeline/<string:name>', methods=['GET', 'POST'])
def start_pipeline(name):
    response = client.start_pipeline_execution(
        name=name
    )
    print(response)
    print(response['pipelineExecutionId'])
    time.sleep(150)
    print("sleep over")
    info = client.get_pipeline_execution(
        pipelineName=name,
        pipelineExecutionId=response['pipelineExecutionId']
    )
    mystring = str(info['pipelineExecution']['status'])
    while mystring == "InProgress":
        info = client.get_pipeline_execution(
            pipelineName=name,
            pipelineExecutionId=response['pipelineExecutionId']
        )
        mystring = str(info['pipelineExecution']['status'])
        # print(type(info['pipelineExecution']['status']))
        # print(type(mystring))
        # print(mystring)
    print("Final State:" + "               " + info['pipelineExecution']['status'])
    return "Final State:" + "               " + info['pipelineExecution']['status']
    # return response
'''

#Utility function to show pipelines with respect to different environment names
#It is used in button url
@app.route('/aws-interface/show_pipeline/<string:environmentName>', methods=['GET', 'POST'])
def show_pipeline(environmentName):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM pipelines WHERE client_id = %s AND pipeline_status= %s', ([session['id']], environmentName))
    client_pipelines = cursor.fetchall()
    client_aws_pipeline_names = []
    countMsgs = []
    msgs = []
    for element in client_pipelines:
        client_aws_pipeline_names.append(element['pipeline_name'])
        msgs.append(get_pipeline_all_run_history(element['pipeline_name']))
        countMsgs.append(get_pipeline_last_execution_count(element['pipeline_name']))
    return render_template('home.html', username=session['username'], pipeline_names=client_aws_pipeline_names, titles=[],msgs=msgs,countMsgs=countMsgs,now_time=request.args.get('nowTime'),now_pipeline=request.args.get('nowPipeline'),environment_name=environmentName)

# http://localhost:5000/
# http://localhost:5000/aws-interface/ - this will be the login page, we need to use both GET and POST requests
@app.route('/')
@app.route('/aws-interface/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            #return 'Logged in successfully!'
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

# http://localhost:5000/aws-interface/logout - this will be the logout page
@app.route('/aws-interface/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/aws-interface/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/aws-interface/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', [username])
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/aws-interface/home - this will be the home page, only accessible for loggedin users
@app.route('/aws-interface/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM pipelines WHERE client_id = %s', [session['id']])
        client_pipelines = cursor.fetchall()
        client_aws_pipeline_names = []
        countMsgs = []
        msgs = []
        for element in client_pipelines:
            client_aws_pipeline_names.append(element['pipeline_name'])
            # msgs.append(get_pipeline_history(element['pipeline_name']))
            msgs.append(get_pipeline_all_run_history(element['pipeline_name']))
            countMsgs.append(get_pipeline_last_execution_count(element['pipeline_name']))
        # for x in msgs:
        #     for y in x:
        #         print(y, end=' ')
        #     print()
        # msgs_headings = ['Pipeline Name','Pipeline Version','Pipeline Status','Pipeline Summary','Pipeline LastStatusChange','Pipeline Created','Pipeline Updated']
        # return render_template('home.html', username=session['username'], pipeline_names=client_aws_pipeline_names, titles=[], msgs=msgs, msgs_headings=msgs_headings)
        print(msgs)
        print(countMsgs)
        return render_template('home.html', username=session['username'], pipeline_names=client_aws_pipeline_names,
                               titles=[], msgs=msgs,countMsgs=countMsgs,now_time=request.args.get('nowTime'),now_pipeline=request.args.get('nowPipeline'))
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/aws-interface/profile - this will be the profile page, only accessible for loggedin users
@app.route('/aws-interface/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/aws-interface/dashboard - this will be the dashboard page, only accessible for loggedin users
@app.route('/aws-interface/dashboard')
def dashboard():
    # Check if user is loggedin
    if 'loggedin' in session:
        return render_template('dashboard.html')
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

'''
if __name__ == '__main__':
    #app.debug = True
    #app.run()
    app.run(debug=True, port=5000)
'''

if __name__ == '__main__':
    socketio.run(app)