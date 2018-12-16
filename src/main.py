# standard modules
import sys
import os

# third party modules
import psycopg2 as ps
import connexion

# custom modules
import controller
import db_utils



def main(debug, port_number):
    app = connexion.App(__name__, specification_dir='../', debug=debug)
    app.add_api(
        'swagger.yml',
        strict_validation=True,
        #validate_responses=True,
        arguments={'title': 'Cloud Computing Exercise 2'})
    app.run(port=port_number)


if __name__ == '__main__':
    # check if server is running on heroku (parameter --heroku)
    arg_set = set(sys.argv[1:])
    if "--heroku" in arg_set:
        arg_set.remove("--heroku")
        database_url = os.environ['DATABASE_URL']
        port_number = int(os.environ['PORT'])
    else:
        database_url = db_utils.DEFAULT_DB
        port_number=8080

    # check if server is in debug mode
    if "--debug" in arg_set:
        arg_set.remove("--debug")
        debug=True
    else:
        debug=False

    # check if other falgs are passed to the script, if so return usage
    if len(arg_set) != 0:
        print("Wrong synthax, usage: main.py [--debug][--heroku]")
    else: # otherwise run the application
        try:
            controller.connect(db_url=database_url)
            main(debug=debug,
                 port_number=port_number)
        finally:
            print('REST API server closed successfully!')
            controller.close_connection()
