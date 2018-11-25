import psycopg2 as ps
import connexion

import controller

def main():
    app = connexion.App(__name__, specification_dir='../', debug=True)
    app.add_api(
        'swagger.yml',
        strict_validation=True,
        #validate_responses=True,
        arguments={'title': 'Cloud Computing Exercise 2'})
    app.run(port=8080)

if __name__ == '__main__':
    main()
    controller.connection.close()
