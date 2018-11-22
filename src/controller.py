import psycopg2 as ps
import connexion
import flask

#users/ ------------------------------------------------------------------------
def add_user(username):
    isauthorized, user_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    # TODO insert new user
    ############################
    user_id = 0
    ############################

    return user_id, 200

def get_all_users():
    isauthorized, user_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    # TODO query for all users
    ############################
    all_users = []
    ############################

    return all_users, 200

# users/{user_id} --------------------------------------------------------------
def send_message(user_id, message):
    isauthorized, sender_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    message = str(message)

    # TODO send message to user_id #
    ############################
    msg_id = 0
    ############################

    return msg_id, 0

def update_user(user_id):
    isauthorized, caller_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    user_info = connexion.request.json

    # TODO update user info
    ################
    updated_user_id=0
    ################

    return updated_user_id, 200

def get_user(user_id):
    isauthorized, caller_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    # TODO get user info ######################
    user_info = "{'id':0, 'username':'usrnm'}"#
    ###########################################

    if user_info is None:
        _invalid_user_id_response()
    return user_info, 200

def get_user_v2(username):
    return "not yet implemented", 500


# users/all --------------------------------------------------------------------
def broadcast_message(message):
    isauthorized = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    message = str(message)

    #TODO broadcaste message 
    ##########################
    message_id=0
    ##########################

    return message_id, 200

# user/{user_id}/received ------------------------------------------------------
def get_received_messages(user_ids):
    isauthorized, _ = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    #TODO retreieve messages from db
    #################################
    messages = "[{'text':'testo'}]"
    #################################

    if messages is None:
        if not _user_exists():
            return _invalid_user_id_response()
    return messages, 200

# user/{user_id}/sent ----------------------------------------------------------
def get_sent_messages(user_id):
    isauthorized, _ = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    print(user_id)

    #TODO retreieve messages from db #
    messages = "[{'text':'testo'}]"  #
    ##################################

    if messages is None:
        if not _user_exists():
            return _invalid_user_id_response()

    return messages, 200

# message/{msg_id} -------------------------------------------------------------
def get_message(msg_id):
    isauthorized, user_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    #TODO retreieve message info from db----#
    message = "{'text':'testo'}"            #
    #---------------------------------------#

    if message is None: # <-- no entry in the db associated to msg_id
        return "Invalid message_id", 400
    else:
        return message, 200

def delete_message(msg_id):
    isauthorized, user_id = _check_credentials()
    if not isauthorized:
        return _invalid_credentials_response()

    # TODO try to delete message

    wasremoved = True # <--- substitute
    if wasremoved:
        return "Successful deletion of message", 200
    else:
        # TODO check if the message id is correct
        return "At least a user has read the message, deletion not possible", 403

#-------------------------------------------------------------------------------
################################################################################

# TODO implement
def _user_exists():
    return True

def _check_credentials():
    auth = connexion.request.authorization
    if auth is None:
        return False, -1

    # TODO check that the authorization method is Basic HTTP
    username = auth.username
    password = auth.password
    # TODO check the pair (username, password) is a valid credential
    return True, 0

def _invalid_credentials_response():
    return "Invalid Credentials", 401

def _invalid_user_id_response():
    return "Invalid user-id", 404