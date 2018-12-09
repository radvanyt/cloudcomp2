import re

import psycopg2 as ps
import psycopg2.errorcodes as errorcodes

import exceptions


def add_user(
    cursor:ps.extensions.connection,
    username:str,
    password:str):

    """
    Insert a new username into the database using given information.
    Return the user-id of the just added user.
    """

    # check that the input username is in the correct format i.e. alphanumeric
    username_pattern = r"[a-zA-Z0-9_-]+\Z"
    if not re.match(username_pattern, username):
        raise exceptions.BadRequestException(
            "Invalid username, it must contain only alphanumeric characters or '-' '_'")

    # insert new user into the database
    try:
        with cursor.connection:
            cursor.execute(
                "INSERT INTO Users (username, password) VALUES (%s, %s) RETURNING user_id;", 
                [username, password])
            result = cursor.fetchone()
        return result[0]

    except ps.DataError as e:
        if e.pgcode == errorcodes.STRING_DATA_RIGHT_TRUNCATION:
            raise exceptions.BadRequestException(
                '''Invalid username, it must contain alphanumeric 
                characters or \'-\' or \'_\'''')
        else:
            raise exceptions.BadRequestException(e.pgerror)

    except ps.IntegrityError as e:
        if e.pgcode == errorcodes.UNIQUE_VIOLATION:
            raise exceptions.ConflictException(
                "Username already in use")
        else:
            raise exceptions.ConflictException(e.pgerror)

def update_user(
    cursor:ps.extensions.cursor,
    user_id:int,
    new_username:str,
    new_password:str):

    # check that the input username is in the correct format i.e. alphanumeric
    username_pattern = r"[a-zA-Z0-9_-]+\Z"
    if not re.match(username_pattern, new_username):
        raise exceptions.BadRequestException(
            "Invalid username, it must contain only alphanumeric characters or '-' '_'")

    # insert new user into the database
    try:
        with cursor.connection:
            cursor.execute(
                '''
                UPDATE Users
                SET username=%s, password=%s
                WHERE user_id=%s
                RETURNING user_id;''',
                [new_username, new_password, user_id])
            result = cursor.fetchone()
            if result is None:
                raise exceptions.NotFoundException(
                    "User-id not found")
        return result[0]

    except ps.DataError as e:
        if e.pgcode == errorcodes.STRING_DATA_RIGHT_TRUNCATION:
            raise exceptions.BadRequestException(
                '''Invalid username, it must contain alphanumeric 
                characters or \'-\' or \'_\'''')
        else:
            raise exceptions.BadRequestException(e.pgerror)

    except ps.IntegrityError as e:
        if e.pgcode == errorcodes.UNIQUE_VIOLATION:
            raise exceptions.ConflictException(
                "Username already in use")
        else:
            raise e

#-------------------------------------------------------------------------------
# Work in Progress
def query_users(
    cursor: ps.extensions.cursor,
    where_user_id:int=None,
    where_username:str=None,
    where_password:str=None,
    select_user_id:bool=False,
    select_username:bool=False,
    select_password:bool=False):

    # build select
    attrs=[]
    addall = not (select_user_id or select_username or select_password)
    if select_user_id or addall: attrs.append("user_id")
    if select_username or addall: attrs.append("username")
    if select_password or addall: attrs.append("password")
    select_str = ",".join(attrs)

    # build where
    where_str= "TRUE"
    values = []
    if where_user_id is not None:
        where_str += " AND user_id = %s"
        values.append(where_user_id)

    if where_username is not None:
        where_str += " AND username = %s"
        values.append(where_username)

    if where_password is not None:
        where_str += " AND password = %s"
        values.append(where_password)

    try:
        cursor.execute(
            ("SELECT "+select_str+
            "\nFROM users"+
            "\nWHERE " + where_str + ";"),
            values)
        return _to_dict(cursor.fetchall(), attrs)

    except ps.DataError as e:
        if e.pgcode == errorcodes.STRING_DATA_RIGHT_TRUNCATION:
            raise exceptions.BadRequestException(
                '''Invalid username, it must contain only alphanumeric 
                characters or \'-\' or \'_\'''')
        else:
            raise exceptions.BadRequestException(e.pgerror)

def send_message(cursor, sender_id, receiver_ids, msg_text):
    num_receivers = len(receiver_ids)
    assert num_receivers > 0

    try:
        with cursor.connection:
            cursor.execute(
                '''
                INSERT INTO Messages (sender_id, message_text, timestamp) 
                VALUES (%s, %s, current_timestamp) RETURNING message_id;
                ''', [sender_id, msg_text])
            insert_id = cursor.fetchone()[0]

            values = [None]*num_receivers*2
            for i in range(num_receivers):
                values[2*i] = insert_id
                values[2*i+1] = receiver_ids[i]

            cursor.execute(
                '''
                INSERT INTO receivers (message_id, receiver_id, message_read)
                VALUES'''+" (%s,%s,DEFAULT)"+",(%s,%s,DEFAULT)"*(num_receivers-1)+";",
                values)
        return insert_id

    except ps.DataError as e:
        raise exceptions.BadRequestException(e.pgerror)
    except ps.IntegrityError as e:
        if e.pgcode == errorcodes.FOREIGN_KEY_VIOLATION:
            raise exceptions.NotFoundException("At least one of the receiver-ids is not associated to a valid user!")
        raise e

def get_message(cursor, user_id, message_id):
    try:
        with cursor.connection:
            cursor.execute(
            '''
            SELECT message_text, sender_id, timestamp
            FROM Messages
            WHERE message_id = %s;''', [message_id])
            result = cursor.fetchone()

            if result is None:
                raise exceptions.NotFoundException(
                    "Message-id not found")

            message_text, sender_id, timestamp = result

            cursor.execute(
                '''
                SELECT receiver_id, message_read
                FROM Receivers
                WHERE message_id = %s;''', [message_id])
            results = _to_dict(
                cursor.fetchall(),
                ["receiver_id","message_read"])

            cursor.execute(
                '''
                UPDATE Receivers
                SET message_read = TRUE
                WHERE message_id = %s AND receiver_id = %s
                RETURNING *''',
                [message_id, user_id])

            update_res = cursor.fetchone()
            if update_res is None and user_id != sender_id : #id is not the receiver
                raise exceptions.UnauthorizedException(
                    "You must be either the message receiver or sender in order to retrieve it")
            
            for t in results:
                if t["receiver_id"] == user_id:
                    t["message_read"] = True

        return {"message_id": message_id,
                "message_text":message_text,
                "sender_id":sender_id,
                "timestamp":timestamp,
                "message_read":results}

    except ps.DataError as e:
        raise exceptions.BadRequestException(e.pgerror)
    except ps.IntegrityError as e:
        raise e

def get_received_messages(cursor, user_id):
    try:
        with cursor.connection:
            cursor.execute(
            '''
            SELECT m.message_id, m.sender_id, m.timestamp
            FROM Receivers as r, Messages as m
            WHERE r.receiver_id = %s AND r.message_id = m.message_id;''',
            [user_id])
            results = cursor.fetchall()
        return _to_dict(results, ["message_id", "sender_id", "timestamp"])

    except ps.DataError as e:
        raise exceptions.BadRequestException(e.pgerror)

def get_sent_messages(cursor, user_id):
    try:
        with cursor.connection:
            cursor.execute(
            '''
            SELECT message_id, sender_id, timestamp
            FROM Messages
            WHERE sender_id = %s;''',
            (user_id,))
            results = cursor.fetchall()
        return _to_dict(results, ["message_id", "sender_id", "timestamp"])
    except ps.DataError as e:
        raise exceptions.BadRequestException(e.pgerror)

def delete_message(cursor, user_id, message_id):
    try:
        with cursor.connection:
            # check if the message is indeed in the database
            cursor.execute(
                '''
                SELECT *
                FROM Receivers
                WHERE message_id = %s;''',
                [message_id])
            result = cursor.fetchone()
            if result is None:
                raise exceptions.NotFoundException("Message-id not found")

            # check if any of the receivers has read the message
            cursor.execute(
                '''
                SELECT *
                FROM Receivers
                WHERE message_id = %s AND message_read=TRUE;''',
                [message_id])
            result = cursor.fetchone()

            if result is None: # if not remove the message
                cursor.execute(
                    '''
                    DELETE FROM Messages 
                    WHERE message_id = %s AND sender_id =%s
                    RETURNING message_id;''', [message_id, user_id])
                result = cursor.fetchone()
                if result is None:
                    raise exceptions.UnauthorizedException(
                        "Only the sender user can remove the message")
            else: # somebody has read the message
                raise exceptions.ConflictException(
                     "The message has already been read by at least a receiver, deletion is not possible")
    except ps.DataError as e:
        raise exceptions.BadRequestException(e.pgerror)

def broadcast_message(cursor, sender_id, message_text):
    try:
        with cursor.connection:
            cursor.execute(
            '''
            INSERT INTO Messages (sender_id, message_text, timestamp)
            VALUES (%s, %s, current_timestamp)
            RETURNING message_id;''', [sender_id, message_text])
            message_id = cursor.fetchone()[0]

            cursor.execute(
            '''
            INSERT INTO Receivers(message_id, receiver_id)
                SELECT m.message_id, u.user_id
                FROM Messages as m, Users as u
                WHERE m.message_id = %s AND u.user_id != %s;''',
                [message_id, sender_id])
        return message_id
    except ps.DataError as e:
        raise exceptions.BadRequestException(e.pgerror)

#-------------------------------------------------------------------------------
def _to_dict(results:list, attributes:list):
    _fun = lambda x: dict(zip(attributes, x))
    return [_fun(x) for x in results]