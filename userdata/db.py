"""
This file will manage interactions with our data store.
At first, it will just contain stubs that return fake data.
Gradually, we will fill in actual calls to our datastore.
"""
import random
import userdata.db_connect as dbc  # userdata.

# ------ configuration for MongoDB ------ #
USER_COLLECT = 'users'


# ------ DB fields ------ #
NAME = 'Username'
EMAIL = 'Email'
PASSWORD = 'Password'


# ------ DB rules ------ #
ID_LEN = 24
BIG_NUM = 100000000000000000000
MAX_EMAIL_LEN = 320
EMAIL_TAIL = '@gmail.com'
EMAIL_TAIL_LEN = 10


# ------ mock values ------ #
MOCK_ID = '0' * ID_LEN
MOCK_NAME = 'test'
MOCK_EMAIL = '1@gmail.com'
MOCK_PASSWORD = 2
MOCK_NAME_2 = 'updated'
MOCK_EMAIL_2 = 'example@gmail.com'
MOCK_PASSWORD_2 = 1
MAX_MOCK_LEN = MAX_EMAIL_LEN - EMAIL_TAIL_LEN


# returns json of mock user
def get_test_user():
    return {NAME: MOCK_NAME, EMAIL: MOCK_EMAIL, PASSWORD: MOCK_PASSWORD}


# returns a randomly generated mock email
def _get_random_name():
    return str(random.randint(0, BIG_NUM))


# gets a user with a random gmail address
def get_rand_test_user():
    rand_part = _get_random_name()
    return {NAME: rand_part, EMAIL: MOCK_EMAIL, PASSWORD: MOCK_PASSWORD}


def update_test_user():
    return {NAME: MOCK_NAME_2, EMAIL: MOCK_EMAIL_2, PASSWORD: MOCK_PASSWORD_2}


def _gen_id() -> str:
    _id = random.randint(0, BIG_NUM)
    _id = str(_id)
    _id = _id.rjust(ID_LEN, '0')
    return _id


def get_users() -> dict:
    dbc.connect_db()
    return dbc.fetch_all_as_dict(NAME, USER_COLLECT)


def add_user(username: str, email: str, password: str) -> str:
    if exists(username):
        raise ValueError(f'Duplicate Username: {username=}')
    if not username:
        raise ValueError('username may not be blank')
    user = {}
    user[NAME] = username
    user[EMAIL] = email
    user[PASSWORD] = password
    dbc.connect_db()
    _id = dbc.insert_one(USER_COLLECT, user)
    return str(_id) if _id else "False"


def verify_user(username: str, password: str) -> bool:
    dbc.connect_db()
    # Retrieve user from database using the fetch_one function
    user = dbc.fetch_one(USER_COLLECT, {NAME: username})
    if user and password == user[PASSWORD]:
        return True
    return False


def update_user(username: str, update_dict: dict):
    if exists(username):
        return dbc.update_doc(USER_COLLECT, {NAME: username}, update_dict)
    else:
        raise ValueError(f'Update failure: {username} not in database.')


def del_user(username: str):
    if exists(username):
        return dbc.del_one(USER_COLLECT, {NAME: username})
    else:
        raise ValueError(f'Delete failure: {username} not in database.')


def exists(name: str) -> bool:
    dbc.connect_db()
    return dbc.fetch_one(USER_COLLECT, {NAME: name})


def get_user_by_email(email: str):
    """
    Fetches a user from the database by their name.
    """
    dbc.connect_db()
    return dbc.fetch_one(USER_COLLECT, {EMAIL: email})


def get_user_by_name(name: str):
    """
    Fetches a user from the database by their name.
    """
    dbc.connect_db()
    return dbc.fetch_one(USER_COLLECT, {NAME: name})


def store_article_submission(article_link: str, submitter_id: str) -> str:
    """
    Store the submitted article for review.
    """
    # Connect to the database
    dbc.connect_db()

    # Create a new article submission record
    submission_record = {
        "article_link": article_link,
        "submitter_id": submitter_id,
        # Add any other relevant fields, such as submission timestamp
    }

    # Insert the record into the database and retrieve the submission ID
    submission_id = dbc.insert_one('articles', submission_record)

    return submission_id
