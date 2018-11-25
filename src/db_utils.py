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
            raise exceptions.ConflictException(e.pgerror)

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

    cursor.execute(
        ("SELECT "+select_str+
         "\nFROM users"+
         "\nWHERE " + where_str + ";"),
        values)
    return _to_dict(cursor.fetchall(), attrs)

def send_message(cursor, sender_id, receiver_ids, msg_text):
    cursor.execute(
        '''
        INSERT INTO Messages (sender_id, message_text, timestamp) 
        VALUES (%s, %s, current_timestamp) RETURNING message_id;
        ''', [sender_id, msg_text])
    insert_id = cursor.fetchone()[0]

    num_receivers = len(receiver_ids)
    assert num_receivers > 0

    values = [None]*num_receivers*2
    for i in range(num_receivers):
        values[2*i] = insert_id
        values[2*i+1] = receiver_ids[i]

    cmd_p1 = "INSERT INTO receivers (message_id, receiver_id, message_read) VALUES"
    cmd_p2 = " (%s, %s, DEFAULT)"+",(%s, %s, DEFAULT)"*(num_receivers-1)
    cmd = cmd_p1+cmd_p2+";"
    cursor.execute(cmd, values)

    # TODO check errors

    return insert_id

def get_message(cursor, user_id, message_id):
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
    results = _to_dict(cursor.fetchall(), ["receiver_id","message_read"])

    cursor.execute(
        '''
        UPDATE Receivers
        SET message_read = TRUE
        WHERE message_id = %s AND receiver_id = %s
        RETURNING *''', [message_id, user_id])
    
    update_res = cursor.fetchone()
    if update_res is None and user_id != sender_id : #id is not the receiver
        raise exceptions.UnauthorizedException(
            "You must be either the message receiver or sender in order to retrieve it")

    return {"message_text":message_text,
            "sender_id":sender_id,
            "timestamp":timestamp,
            "message_read":results}

def get_received_messages(cursor, user_id):
    cursor.execute(
    '''
    SELECT m.message_id, m.sender_id, m.timestamp
    FROM Receivers as r, Messages as m
    WHERE r.receiver_id = %s AND r.message_id = m.message_id;''',
    (user_id,))

    results = cursor.fetchall()
    return _to_dict(results, ["message_id", "sender_id", "timestamp"])

def get_sent_messages(cursor, user_id):
    cursor.execute(
    '''
    SELECT message_id, sender_id, timestamp
    FROM Messages
    WHERE sender_id = %s;''',
    (user_id,))

    results = cursor.fetchall()
    return _to_dict(results, ["message_id", "sender_id", "timestamp"])

def delete_message(cursor, user_id, message_id):
    precondition_cmd = '''
    SELECT *
    FROM Receivers
    WHERE message_id = %s AND message_read=TRUE;'''
    cursor.execute(precondition_cmd, (message_id,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute(
            '''
            DELETE FROM Messages 
            WHERE message_id = %s 
            RETURNING message_id;''',
            (message_id,))

        result = cursor.fetchone()
        if result is None:
            raise exceptions.NotFoundException(
                "Message-id not found")

    else: # somebody has read the message
        raise exceptions.ConflictException(
            "Somebody has already read the message, deletion not possible")


def broadcast_message(cursor, sender_id, message_text):
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
        WHERE m.message_id = %s;''', [message_id])
    return message_id

#-------------------------------------------------------------------------------
# TO WORK ON

#-------------------------------------------------------------------------------
def _to_dict(results:list, attributes:list):
    _fun = lambda x: dict(zip(attributes, x))
    return [_fun(x) for x in results]