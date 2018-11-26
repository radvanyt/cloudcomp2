import sys
import os

import psycopg2 as ps
import connexion

import controller

def main(debug, port_number):
    app = connexion.App(__name__, specification_dir='../', debug=debug)
    app.add_api(
        'swagger.yml',
        strict_validation=True,
        #validate_responses=True,
        arguments={'title': 'Cloud Computing Exercise 2'})
    app.run(port=port_number)

if __name__ == '__main__':
    
    arg_set = set(sys.argv[1:])
    if "--heroku" in arg_set:
        arg_set.remove("--heroku")
        database_url = os.environ['DATABASE_URL']
        port_number = int(os.environ['PORT'])
    else:
        database_url = "postgres://postgres:postgres@localhost/test_db"
        port_number=8080

    if "--debug" in arg_set:
        arg_set.remove("--debug")
        debug=True
    else:
        debug=False

    if len(arg_set) != 0:
        print("Wrong synthax, usage: main.py [--debug][--heroku]")
    else:
        controller.connect(db_url=database_url)

        main(
            debug=True,#debug,
            port_number=port_number)

        controller.close_connection()
