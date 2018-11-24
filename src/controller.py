import psycopg2 as ps
import connexion
import flask

import db_utils
import exceptions


connection = ps.connect(
    dbname="test_db",
    user="postgres",
    password="postgres")


#users/ ------------------------------------------------------------------------
def add_user(user_info):
    try:
        cur = connection.cursor()
        _check_credentials(cur)
        new_user_id = db_utils.add_user(cur, user_info["username"], user_info["password"])
        connection.commit()

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

    return new_user_id, 200

def get_all_users():
    try:
        cur = connection.cursor()
        _check_credentials(cur)
        results = db_utils.query_users(
            cursor=cur,
            select_username=True,
            select_user_id=True)

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

    return results, 200

# users/{user_id} --------------------------------------------------------------
def send_message(user_id, message):
    try:
        cur = connection.cursor()
        receiver_id = user_id
        sender_id = _check_credentials(cur)
        message_text = str(message)

        msg_id = db_utils.send_message(
            cursor=cur,
            receiver_ids=[receiver_id],
            sender_id=sender_id,
            msg_text=message_text)
        connection.commit()

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()
    return msg_id, 200

def update_user(user_id, user_info):
    try:
        username = user_info["username"]
        password = user_info["password"]

        cur = connection.cursor()
        _check_credentials(cur)
        result = db_utils.update_user(
            cursor=cur,
            user_id=user_id,
            new_username=username,
            new_password=password)
        if result is None:
            raise exceptions.NotFoundException(
                "Given user-id not found")
        connection.commit()


    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()
    return result, 200

def get_user(user_id):
    try:
        cur = connection.cursor()
        _check_credentials(cur)
        results = db_utils.query_users(
            cursor=cur,
            where_user_id=user_id,
            select_username=True,
            select_user_id=True)
        if len(results) == 0:
            raise exceptions.NotFoundException(
                "Given user-id not found")

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()
    return results[0], 200

# users/all --------------------------------------------------------------------
def broadcast_message(message):
    try:
        cur = connection.cursor()
        user_id = _check_credentials(cur)
        message_text = str(message)
        message_id = db_utils.broadcast_msg(cur, user_id, message_text)
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
        cur = connection.cursor()
        _check_credentials(cur)
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
        cur = connection.cursor()
        _check_credentials(cur)
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
        cur = connection.cursor()
        user_id = _check_credentials(cur)
        result = db_utils.get_message(
            cursor=cur,
            user_id=user_id,
            message_id=message_id)
        connection.commit()
        return result, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code
    finally:
        cur.close()

def delete_message(message_id):
    try:
        cur = connection.cursor()
        user_id = _check_credentials(cur)
        db_utils.delete_msg(
            cursor=cur,
            user_id=user_id,
            message_id=message_id)
        connection.commit()
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
    cur = connection.cursor() if cursor is None else cursor
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