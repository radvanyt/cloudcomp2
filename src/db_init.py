import psycopg2 as ps

import db_utils

def db_init(database_url):
    conn = ps.connect(database_url)
    cur = conn.cursor()

    #---------------------------------------------------------------------------
    # Create necessary tables

    cur.execute(
        '''CREATE TABLE Users (
            user_id serial PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL);''')

    cur.execute(
        '''CREATE TABLE Messages (
            message_id serial PRIMARY KEY,
            sender_id int NOT NULL REFERENCES Users,
            message_text text NOT NULL,
            timestamp timestamp with time zone NOT NULL);''')

    cur.execute(
        '''CREATE TABLE Receivers (
            message_id int NOT NULL REFERENCES Messages ON DELETE CASCADE,
            receiver_id int NOT NULL REFERENCES Users,
            message_read bool NOT NULL DEFAULT FALSE);''')
    conn.commit()

    #---------------------------------------------------------------------------
    # Populate user table

    users = [("TamasRadvany", 'password'),
            ("GiorgioMariani", 'password'),
            ("DonaldKnuth","1 2 3 4 5 7"),
            ("xX_Memelord99_Xx","PaSsWOrD"),
            ("bob", "bob")]
    for u,p in users: db_utils.add_user(cur,u,p)
    conn.commit()

    #---------------------------------------------------------------------------

    cur.close()
    conn.close()

    print("Database initialized!")


#===============================================================================
if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print("usage: python db_init.py <database_url>")
    else:
        database_url = sys.argv[1]
        db_init(database_url)