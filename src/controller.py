import psycopg2 as ps
import connexion
import flask

import db_utils
import exceptions


connection = None
database_url = ""

def connect(db_url):
    global connection
    global database_url
    database_url = db_url
    connection = ps.connect(database_url)

def get_connection():
    global connection
    if connection.closed:
        connect(database_url)
        return connection
    else:
        return connection
 
def close_connection():
    connection.close()

#users/ ------------------------------------------------------------------------
def add_user(user_info):
    try:
        cur = get_connection().cursor()
        _check_credentials(cur)

        new_user_id = db_utils.add_user(
            cursor=cur,
            username=user_info["username"],
            password=user_info["password"])
        return new_user_id, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

def get_all_users():
    try:
        cur = get_connection().cursor()
        _check_credentials(cur)

        users = db_utils.query_users(
            cursor=cur,
            select_username=True,
            select_user_id=True)
        return users, 200


    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

# users/{user_id} --------------------------------------------------------------
def send_message(message):
    try:
        cur = get_connection().cursor()
        sender_id = _check_credentials(cur)

        # TODO throw error if attributes not in dict
        message_text = message["message_text"]
        receiver_ids = message["receiver_ids"]

        msg_id = db_utils.send_message(
            cursor=cur,
            receiver_ids=receiver_ids,
            sender_id=sender_id,
            msg_text= message_text)
        return msg_id, 200


    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

def update_user(user_id, user_info):
    try:
        # TODO raise exception if attributes not in dir
        username = user_info["username"]
        password = user_info["password"]

        cur = get_connection().cursor()
        authorized_user_id = _check_credentials(cur)
        if authorized_user_id != user_id:
            raise exceptions.UnauthorizedException(
                "Not enough rights to change the given user's info")

        result = db_utils.update_user(
            cursor=cur,
            user_id=user_id,
            new_username=username,
            new_password=password)

        if result is None:
            raise exceptions.NotFoundException("Given user-id not found")
        else:
            return result, 200


    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

def get_user(user_id):
    try:
        cur = get_connection().cursor()
        _check_credentials(cur)

        results = db_utils.query_users(
            cursor=cur,
            where_user_id=user_id,
            select_username=True,
            select_user_id=True)
        if len(results) == 0:
            raise exceptions.NotFoundException(
                "Given user-id not found")
        return results[0], 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

def get_user_v2(username):
    try:
        cur = get_connection().cursor()
        _check_credentials(cur)

        results = db_utils.query_users(
            cursor=cur,
            where_username=username,
            select_username=True,
            select_user_id=True)
        if len(results) == 0:
            raise exceptions.NotFoundException(
                "Given username not found")
        return results[0], 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

# users/all --------------------------------------------------------------------
def broadcast_message(message):
    try:
        cur = get_connection().cursor()
        user_id = _check_credentials(cur)
        message_text = message.decode('utf-8')

        message_id = db_utils.broadcast_message(cur, user_id, message_text)
        return  message_id, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

# user/{user_id}/received ------------------------------------------------------
def get_received_messages(user_id):
    try:
        cur = get_connection().cursor()
        authorized_user_id = _check_credentials(cur)
        if authorized_user_id != user_id:
            raise exceptions.UnauthorizedException(
                "Not enough rights to access the user's received messages!")

        messages = db_utils.get_received_messages(cur, user_id)
        return  messages, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

# user/{user_id}/sent ----------------------------------------------------------
def get_sent_messages(user_id):
    try:
        cur = get_connection().cursor()
        authorized_user_id = _check_credentials(cur)
        if authorized_user_id != user_id:
            raise exceptions.UnauthorizedException(
                "Not enough rights to access the user's received messages!")

        messages = db_utils.get_sent_messages(cur, user_id)
        return  messages, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

# message/{msg_id} -------------------------------------------------------------
def get_message(message_id):
    try:
        cur = get_connection().cursor()
        user_id = _check_credentials(cur)
        result = db_utils.get_message(
            cursor=cur,
            user_id=user_id,
            message_id=message_id)
        return result, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

def delete_message(message_id):
    try:
        cur = get_connection().cursor()
        user_id = _check_credentials(cur)
        db_utils.delete_message(
            cursor=cur,
            user_id=user_id,
            message_id=message_id)
        return "Message successfully delated", 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

#-------------------------------------------------------------------------------
################################################################################

def _check_credentials(cursor=None):
    auth = connexion.request.authorization
    headers = connexion.request.headers

    # check that the authorization method is Basic HTTP
    if ('Authorization' not in headers or
        "Basic" != headers['Authorization'].split()[0]):
        raise exceptions.UnauthorizedException(
            "You must use Basic HTTP authentication to access this resource")

    # query the database for user information
    cur = get_connection().cursor() if cursor is None else cursor
    user_ids = db_utils.query_users(
        cursor=cur,
        where_username=auth.username,
        where_password=auth.password,
        select_user_id=True)
    if cursor is None: cur.close()

    # check if the credentials are valid
    if len(user_ids) == 0:
        raise exceptions.UnauthorizedException(
            "Invalid authentication credentials!")
    return user_ids[0]["user_id"]