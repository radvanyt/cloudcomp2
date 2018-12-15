import datetime
import re

import redis

import exceptions

#---------------------------
USER_DOMAIN = 'users:'
USER_COUNTER = 'user_counter'
RECEIVED = ':received'
SENT = ':sent'
IDS = 'ids:'

#---------------------------
MESSAGE_DOMAIN = 'messages:'
MESSAGE_COUNTER = 'message_counter'
RECIPIENTS = ':recipients'
READ = ':read'
ALL = ':all'
#---------------------------
MAX_TRANSACTION_ATTEMPS = 10
USR_MAX_LEN = 32

r = None
LOCK = None
def connect(url:str):
    global r, LOCK
    r = redis.from_url(url=url)
    LOCK = r.lock('lock')

def add_user(username:str, password:str):
    # check if username is valid
    if len(username) > USR_MAX_LEN or len(password)> USR_MAX_LEN:
            raise exceptions.BadRequestException(
            "Invalid username or password, the username/password lenght must be less than or equal to "+str(USR_MAX_LEN)+"!")
    username_pattern = r"[a-zA-Z_-][a-zA-Z0-9_-]*\Z"
    if not re.match(username_pattern, username):
        raise exceptions.BadRequestException(
            "Invalid username, it must contain only alphanumeric characters or '-' '_' and not start with a number")

    with LOCK:
        # check if another user with same name exists
        if r.exists(_username_key(username)):
            raise exceptions.ConflictException('Username aready used!')

        # update database state
        user_id = r.incr(USER_COUNTER)
        r.set(_username_key(username), user_id)
        r.hmset(_user_key(user_id), {'username':username, 'password':password})
    return user_id

def update_user(user_id:int, new_username:str, new_password:str):
    # check if username is valid
    if len(new_username)>USR_MAX_LEN or len(new_password)>USR_MAX_LEN:
        raise exceptions.BadRequestException(
            "Invalid username or password, the username/password lenght must be less than or equal to "+str(USR_MAX_LEN)+"!")
    username_pattern = r"[a-zA-Z_-][a-zA-Z0-9_-]*\Z"
    if not re.match(username_pattern, new_username):
        raise exceptions.BadRequestException(
            "Invalid username, it must contain only alphanumeric characters or '-' '_' and not start with a number")

    with LOCK:
        # check if another user with same name exists
        if not r.exists( _user_key(user_id)):
            raise exceptions.BadRequestException('User-id not associated to an existing user!')

        username = _b2s(r.hget(_user_key(user_id), 'username'))
        r.delete(_username_key(username))
        r.hmset(_user_key(user_id), {'username':new_username, 'password':new_password})
        r.set(_username_key(new_username), user_id)
    return user_id

def send_message(
    sender_id:int,
    recipient_ids:int,
    message_text:str):
    with LOCK:
        # check sender_id is valid
        if not r.exists(_user_key(sender_id)):
            raise exceptions.NotFoundException(
                'The sender-id is not associated to an existing user!')

        # check that each recipient is valid
        for recipient_id in recipient_ids:
            if not r.exists(_user_key(recipient_id)):
                raise exceptions.NotFoundException(
                    'The recipient-id '+str(recipient_id)+' is not associated to an existing user!')

        message_id = r.incr(MESSAGE_COUNTER)
        r.hmset(_msg_key(message_id),
                {'sender_id':sender_id,
                 'message_text':message_text,
                 'timestamp':str(datetime.datetime.now())})

        for recipient_id in recipient_ids:
            r.sadd(_user_received_key(recipient_id), message_id)
            r.sadd(_msg_rec_key(message_id), recipient_id)
        r.sadd(_user_sent_key(sender_id), message_id)
    return message_id

def get_message(user_id:int, message_id:int):
    with LOCK:
        # check user is valid
        if not r.exists(_user_key(user_id)):
            raise exceptions.NotFoundException(
                'The user-id is not associated to an existing user!')

        # check message is valid
        if not r.exists(_msg_key(message_id)):
            raise exceptions.NotFoundException(
                'The msg-id is not associated to an existing message!')

        # check if user is receiver 
        recipient_ids = _parse_set(r.smembers(_msg_rec_key(message_id)), _b2i)
        reader_ids = _parse_set(r.smembers(_msg_read_key(message_id)), _b2i)
        message = _parse_dict(r.hgetall(_msg_key(message_id)))

        # get message fields
        sender_id = int(message['sender_id'])
        message_text = message['message_text']
        timestamp = message['timestamp']

        isreceiver = user_id in recipient_ids
        issender = user_id == sender_id
        message_obj = {
            'recipients':recipient_ids,
            'have_read':reader_ids,
            'sender_id':sender_id,
            'message_text':message_text,
            'timestamp':timestamp}

        if isreceiver:
            r.sadd(_msg_read_key(message_id), user_id)
            message_obj['have_read'].append(user_id)
            return message_obj
        elif issender:
            return message_obj
        else:
            raise exceptions.UnauthorizedException(
                'You have to be either a recipient or the sender of the message to retrieve it!')

def get_received_messages(user_id:int):
    with LOCK:
        if not r.exists(_user_key(user_id)):
            raise exceptions.NotFoundException(
                'The user-id is not associated to an existing user!')
        return _parse_set(r.smembers(_user_received_key(user_id)),_b2i)

def get_sent_messages(user_id:int):
    with LOCK:
        if not r.exists(_user_key(user_id)):
            raise exceptions.NotFoundException(
                'The user-id is not associated to an existing user!')
        return _parse_set(r.smembers(_user_sent_key(user_id)),_b2i)

def delete_message(user_id:int, message_id:int):
    with LOCK:
        if not r.exists(_user_key(user_id)):
            raise exceptions.NotFoundException(
                'The user-id is not associated to an existing user!')

        # check message is valid
        if not r.exists(_msg_key(message_id)):
            raise exceptions.NotFoundException(
                'The msg-id is not associated to an existing message!')

        # check if user is sender
        sender_id = _b2i(r.hget(_msg_key(message_id), 'sender_id'))
        issender = user_id == sender_id

        if issender:
            # check if someone has read the message
            if r.exists(_msg_read_key(message_id)):
                raise exceptions.ConflictException(
                     "The message has already been read by at least a receiver, deletion is not possible")
            else:
                # delete message
                # delete from user:{user_id}:received for each recipient
                for recipient_id in _parse_set(r.smembers(_msg_rec_key(message_id)), _b2i):
                    r.srem(_user_received_key(recipient_id), message_id)

                # delete from user:{user_id}:sent
                r.srem(_user_received_key(sender_id), message_id)

                # delete messages:{message_id}
                r.delete(_msg_key(message_id))
                # delete messages:{message_id}:recipients
                r.delete(_msg_rec_key(message_id))
                # delete messages:{message_id}:read
                r.delete(_msg_read_key(message_id))
                return message_id
        else:
            raise exceptions.UnauthorizedException(
                'You have to be either a recipient or the sender of the message to retrieve it!') 

def get_all_users():
    users = []
    for user_key in r.scan_iter(match=USER_DOMAIN+IDS+'*'):
        user_id = int(_b2s(user_key).split(':')[-1])
        result = _parse_dict(r.hgetall(user_key))
        user = {'user_id':user_id, 'username':result['username']}
        users.append(user)
    return users

def get_user_info(user_id:int):
    #check user exists
    if not r.exists(_user_key(user_id)):
        raise exceptions.NotFoundException(
                'The user-id is not associated to an existing user!')
    result = _parse_dict(r.hgetall(_user_key(user_id)))
    return {'user_id':user_id, 'username':result['username']}

def get_user_info_v2(username:str):
    #check user exists
    if not r.exists(_username_key(username)):
        raise exceptions.NotFoundException(
                'The user-id is not associated to an existing user!')
    user_id = _b2i(r.get(_username_key(username)))
    return {'user_id':user_id, 'username':username}

def check_credentials(username:str, password:str):
    user_id_raw = r.get(_username_key(username))
    if user_id_raw is None:
        raise exceptions.UnauthorizedException('Authentication username not found in database!')

    user_id = _b2i(user_id_raw)
    password_target = _b2s(r.hget(_user_key(user_id), 'password'))
    if password != password_target:
        raise exceptions.UnauthorizedException('Invalid password for username!')
    return user_id


#----------------------------------------------------------
def _b2s(byte_array:bytes):
    return byte_array.decode('utf-8')

def _b2i(byte_array:bytes):
    return int(_b2s(byte_array))

def _parse_dict(d:dict):
    return {_b2s(k):_b2s(v) for k,v in d.items()}

def _parse_set(s:set, fun=_b2s):
    return [fun(e) for e in s]

#----------------------------
def _user_key(user_id:int):
    return USER_DOMAIN+IDS+str(user_id)

def _username_key(username:str):
    return USER_DOMAIN+'username:'+str(username)

def _user_received_key(user_id:int):
    return USER_DOMAIN+str(user_id)+RECEIVED

def _user_sent_key(user_id:int):
    return USER_DOMAIN+str(user_id)+SENT

def _msg_key(msg_id:int):
    return MESSAGE_DOMAIN+str(msg_id)

def _msg_rec_key(msg_id:int):
    return MESSAGE_DOMAIN+str(msg_id)+RECIPIENTS

def _msg_read_key(msg_id:int):
    return MESSAGE_DOMAIN+str(msg_id)+READ
#----------------------------------
#----------------------------------

def init():
    r.flushall(True)
    add_user('root','root')
    add_user('user1','pass')
    add_user('user2','pass')
    add_user('user3','pass')
    add_user('user4','pass')