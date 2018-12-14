import psycopg2 as ps
import connexion
import flask

import redis_utils
import exceptions


#users/ ------------------------------------------------------------------------
def add_user(user_info):
    try:
        _check_credentials()
        new_user_id = redis_utils.add_user(
            username=user_info["username"],
            password=user_info["password"])
        return new_user_id, 201

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

def get_all_users():
    try:
        _check_credentials()
        users = redis_utils.get_all_users()
        return users, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

# users/{user_id} --------------------------------------------------------------
def send_message(message):
    try:
        sender_id = _check_credentials()
        message_text = message["message_text"]
        receiver_ids = message["receiver_ids"]

        # TODO encrypt message_text 
        message_text_encrypted = client.encrypt(message_text)
        msg_id = redis_utils.send_message(
            recipient_ids=receiver_ids,
            sender_id=sender_id,
            message_text=message_text_encrypted)
        return msg_id, 201


    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code


def update_user(user_id, user_info):
    try:
        username = user_info["username"]
        password = user_info["password"]

        authorized_user_id = _check_credentials()
        if authorized_user_id != user_id:
            raise exceptions.UnauthorizedException(
                "Not enough rights to change the user's info")

        result = redis_utils.update_user(
            user_id=user_id,
            new_username=username,
            new_password=password)
        return result, 200
    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

def get_user(user_id):
    try:
        _check_credentials()
        user_info = redis_utils.get_user_info(user_id=user_id)
        return user_info, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

def get_user_v2(username):
    try:
        _check_credentials()
        user_info = redis_utils.get_user_info_v2(username=username)
        return user_info, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

# user/{user_id}/received ------------------------------------------------------
def get_received_messages(user_id):
    try:
        authorized_user_id = _check_credentials()
        if authorized_user_id != user_id:
            raise exceptions.UnauthorizedException(
                "Not enough rights to access the user's received messages!")

        messages = redis_utils.get_received_messages(user_id)
        return  messages, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

# user/{user_id}/sent ----------------------------------------------------------
def get_sent_messages(user_id):
    try:
        authorized_user_id = _check_credentials()
        if authorized_user_id != user_id:
            raise exceptions.UnauthorizedException(
                "Not enough rights to access the user's received messages!")

        messages = redis_utils.get_sent_messages(user_id)
        return  messages, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code


# message/{msg_id} -------------------------------------------------------------
def get_message(message_id):
    try:
        user_id = _check_credentials()
        result = redis_utils.get_message(
            user_id=user_id,
            message_id=message_id)
        return result, 200

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code


def delete_message(message_id):
    try:
        user_id = _check_credentials()
        redis_utils.delete_message(
            user_id=user_id,
            message_id=message_id)
        return "Message successfully delated", 204

    except exceptions.UnauthorizedException as e:
        return e.description, e.code, e.authentication_header
    except exceptions.ResponseException as e:
        return e.description, e.code

#-------------------------------------------------------------------------------
################################################################################



def _check_credentials():
    auth = connexion.request.authorization
    headers = connexion.request.headers

    # check that the authorization method is Basic HTTP
    if ('Authorization' not in headers or
        "Basic" != headers['Authorization'].split()[0]):
        raise exceptions.UnauthorizedException(
            "You must use Basic HTTP authentication to access this resource")
    return redis_utils.check_credentials(auth.username, auth.password)