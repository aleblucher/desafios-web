Guia de Instalação
=========================================================

pip3 install flask
pip3 install flask httpauth

(conecta com o banco de dados)
sqlite3 quiz.db

(dot comman! Importante colocar ponto antes dos comandos)	
(read executa o sql para a criacao das tabelas necessárias)
sqlite> .read quiz.sql
sqlite> .quit

criar um arquivo users.csv
dentro deste arquivo adicionar usuario e senha no seguinte formato:
usuario,tipo
(!!! a senha padrão é o próprio usuario – o tipo é a permissão o usuario, exe admin. Para criar um usuario que não seja admin só insira qualquer caracteres que não a string ‘admin’ . Deixar o campo vazio causará um erro)


rodar na linha de comando:
python3 adduser.py

Export FLASK APP=softdes
flask run

acessar o localhost fornecido
fazer login com o usuario adicionado 