README
======
In order to start the web application you need to:

 - have a 3.7.x python interpreter and pip installed
 - install python dependencies: *pip install -r requirements.txt*

If you want to start the application on heroku you will need to initialize the db by executing the one-off dyno *"heroku run redis_init"* (the web application is automatically initialized by heroku).

Otherwise, with a standard server you need to:

 - start the redis-server
 - initialize the db: *python src/db_init.py*
 - start the web application: *python src/main.py*