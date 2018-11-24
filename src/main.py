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

    connection = ps.connect(
        dbname="test_db",
        user="postgres",
        password="postgres")

    '''
    import db_utils
    cursor = connection.cursor()
    users = [
         ("TamàsRadvàny", 'password'),
         ("GiorgioMariani", 'password'),
         ("DonaldKnuth","1 2 3 4 5 7"),
         ("xX_pussyDestroyer99_Xx","PaSsWOrD"),
         ("bob", "bob")]

    u0,p0 = users[0]
    db_utils.add_user(cursor, u0, p0)
    cursor.close()'''

    main()

    connection.close()

