# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 09:00:39 2017

@author: rauli
"""

from datetime import datetime
import sqlite3
import json
import hashlib
from flask_httpauth import HTTPBasicAuth
from flask import Flask, request, jsonify, abort, make_response, session, render_template

DBNAME = './quiz.db'

def lambda_handler(event, context):
    """Checks validty of the required challenges and executes it"""
    try:
        import numbers
        def not_equals(first, second):
            if isinstance(first, numbers.Number) and isinstance(second, numbers.Number):
                return abs(first - second) > 1e-3
            return first != second
        
        # TODO implement
        ndes = int(event['ndes'])
        code = event['code']
        args = event['args']
        resp = event['resp']
        diag = event['diag']
        exec(code, locals())
        
        test = []
        for index, arg in enumerate(args):
            if not 'desafio{0}'.format(ndes) in locals():
                return "Nome da função inválido. Usar 'def desafio{0}(...)'".format(ndes)
            
            if not_equals(eval('desafio{0}(*arg)'.format(ndes)), resp[index]):
                test.append(diag[index])

        return " ".join(test)
    except:
        return "Função inválida."

def convert_data(orig):
    """Formats data into a more easily read structure"""
    return orig[8:10]+'/'+orig[5:7]+'/'+orig[0:4]+' '+orig[11:13]+':'+orig[14:16]+':'+orig[17:]

def get_quizes(user):
    """Acesses database and returns id and numb from the quiz table"""
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    if user in ('admin', 'fabioja'):
        cursor.execute("SELECT id, numb from QUIZ".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    else:
        cursor.execute("SELECT id, numb from QUIZ where release < '{0}'".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def get_user_quiz(userid, quizid):
    """Acesses database and returns sent, answer and result from userquiz table for a specific user and quiz"""
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sent,answer,result from USERQUIZ where userid = '{0}' and quizid = {1} order by sent desc".format(userid, quizid))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def set_user_quiz(userid, quizid, sent, answer, result):
    """Alters database by inserting a new quiz from an  user"""
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("insert into USERQUIZ(userid,quizid,sent,answer,result) values (?,?,?,?,?);", (userid, quizid, sent, answer, result))
    conn.commit()
    conn.close()

def getQuiz(id, user):
    """Returns information by quiz id"""
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    if user == 'admin' or user == 'fabioja':
        cursor.execute("SELECT id, release, expire, problem, tests, results, diagnosis, numb from QUIZ where id = {0}".format(id))
    else:
        cursor.execute("SELECT id, release, expire, problem, tests, results, diagnosis, numb from QUIZ where id = {0} and release < '{1}'".format(id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    info = [reg for reg in cursor.fetchall()]
    conn.close()
    return info

def set_info(pwd, user):
    """Updates user password"""
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE USER set pass = ? where user = ?", (pwd, user))
    conn.commit()
    conn.close()

def get_info(user):
    """Retruns password and type from a user"""
    conn = sqlite3.connect(DBNAME)
    cursor = conn.cursor()
    cursor.execute("SELECT pass, type from USER where user = '{0}'".format(user))
    print("SELECT pass, type from USER where user = '{0}'".format(user))
    info = [reg[0] for reg in cursor.fetchall()]
    conn.close()
    if len(info) == 0:
        return None
    else:
        return info[0]

auth = HTTPBasicAuth()

app = Flask(__name__, static_url_path='')
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?TX'

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def main():
    """Main fuction"""
    msg = ''
    var = 1
    challenges = get_quizes(auth.username())
    sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if request.method == 'POST' and 'ID' in request.args:
        id = request.args.get('ID')
        quiz = getQuiz(id, auth.username())
        if len(quiz) == 0:
            msg = "Boa tentativa, mas não vai dar certo!"
            var = 2
            return render_template('index.html', username=auth.username(), challenges=challenges, var=var, msg=msg)

        
        quiz = quiz[0]
        if sent > quiz[2]:
            msg = "Sorry... Prazo expirado!"
        
        f = request.files['code']
        filename = './upload/{0}-{1}.py'.format(auth.username(), sent)
        f.save(filename)
        with open(filename, 'r') as fp:
            answer = fp.read()
        
        #lamb = boto3.client('lambda')
        args = {"ndes": id, "code": answer, "args": eval(quiz[4]), "resp": eval(quiz[5]), "diag": eval(quiz[6])}

        #response = lamb.invoke(FunctionName="Teste", InvocationType='RequestResponse', Payload=json.dumps(args))
        #feedback = response['Payload'].read()
        #feedback = json.loads(feedback).replace('"','')
        feedback = lambda_handler(args, '')


        result = 'Erro'
        if len(feedback) == 0:
            feedback = 'Sem erros.'
            result = 'OK!'

        set_user_quiz(auth.username(), id, sent, feedback, result)


    if request.method == 'GET':
        if 'ID' in request.args:
            id = request.args.get('ID')
        else:
            id = 1

    if len(challenges) == 0:
        msg = "Ainda não há desafios! Volte mais tarde."
        var = 2
        return render_template('index.html', username=auth.username(), challenges=challenges, var=var, msg=msg)
    else:
        quiz = getQuiz(id, auth.username())

        if len(quiz) == 0:
            msg = "Oops... Desafio invalido!"
            var = 2
            return render_template('index.html', username=auth.username(), challenges=challenges, var=var, msg=msg)

        answers = get_user_quiz(auth.username(), id)
    
    return render_template('index.html', username=auth.username(), challenges=challenges, quiz=quiz[0], e=(sent > quiz[0][2]), answers=answers, var=var, msg=msg, expi=convert_data(quiz[0][2]))

@app.route('/pass', methods=['GET', 'POST'])
@auth.login_required
def change():
    """Altering password"""
    if request.method == 'POST':
        velha = request.form['old']
        nova = request.form['new']
        repet = request.form['again']

        var = 1
        msg = ''
        if nova != repet:
            msg = 'As novas senhas nao batem'
            var = 3
        elif get_info(auth.username()) != hashlib.md5(velha.encode()).hexdigest():
            msg = 'A senha antiga nao confere'
            var = 3
        else:
            set_info(hashlib.md5(nova.encode()).hexdigest(), auth.username())
            msg = 'Senha alterada com sucesso'
            var = 3
    else:
        msg = ''
        var = 3

    return render_template('index.html', username=auth.username(), challenges=get_quizes(auth.username()), var=var, msg=msg)


@app.route('/logout')
def logout():
    """Executes the logout"""
    return render_template('index.html', var=2, msg="Logout com sucesso"), 401

@auth.get_password
def get_password(username):
    """Retruns the password by user"""
    return get_info(username)

@auth.hash_password
def hash_pw(password):
    """Encodes password"""
    return hashlib.md5(password.encode()).hexdigest()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)

