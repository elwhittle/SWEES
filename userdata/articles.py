"""
This file will manage interactions with our data store.
At first, it will just contain stubs that return fake data.
Gradually, we will fill in actual calls to our datastore.
"""
import requests
from bs4 import BeautifulSoup
import logging
import userdata.db_connect as dbc  # userdata.
from bson.objectid import ObjectId
from bson.errors import InvalidId
import userdata.extras as extras
import userdata.users as users  # articles depends on user, avoid circular import!
import re
import textwrap


# ------ configuration for MongoDB ------ #
USER_COLLECT = 'users'
ARTICLE_COLLECTION = 'articles'
# field name for user ID in the articles collection
ARTICLE_LINK = "article_link"
ARTICLE_TITLE = "article_title"
ARTICLE_BODY = "article_body"
ARTICLE_PREVIEW = "article_preview"
PRIVATE = "private"


# ------ DB fields ------ #
NAME = users.NAME
EMAIL = users.EMAIL
PASSWORD = users.PASSWORD
SUBMITTER_ID_FIELD = users.SUBMITTER_ID_FIELD
OBJECTID = '_id'


def fetch_article_content(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises exception for 4XX or 5XX errors
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    return response.text


def extract_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else "No Title Found"
    article = soup.find('article')
    if not article:
        logging.warning("Article tag not found.")
        return None
    article_text = article.get_text(strip=True)
    wrapped_text = textwrap.fill(article_text, width=85)  # Wrap text to 85 characters per line
    return title, wrapped_text


def store_article_submission(submitter_id: str, article_url: str) -> (bool, str):
    """
    Store the submitted article content fetched from a URL.
    """
    user = users.get_user_by_id(submitter_id)
    if not user:
        return False, f"User with {submitter_id} NOT found"

    html_content = fetch_article_content(article_url)
    if not html_content:
        return False, "Failed to fetch article content"

    article_title, article_text = extract_content(html_content)
    if not article_text:
        return False, "Failed to extract article content"

    submission_record = {
        ARTICLE_LINK: article_url,
        ARTICLE_TITLE: article_title,
        ARTICLE_BODY: article_text,
        SUBMITTER_ID_FIELD: user[OBJECTID],
        PRIVATE: False
    }
    dbc.connect_db()
    submission_id = dbc.insert_one(ARTICLE_COLLECTION, submission_record)
    return True, submission_id


def get_article_by_id(article_id, user_id=None):
    try:
        object_id = ObjectId(article_id)
    except InvalidId:
        return None

    dbc.connect_db()
    article = dbc.fetch_one(ARTICLE_COLLECTION, {OBJECTID: object_id})
    if article and (article[SUBMITTER_ID_FIELD] == user_id or not article[PRIVATE]):
        return article
    else:
        return None


def fetch_all_with_filter(filt={}, projection={}, constrained=False, title_keyword=None, submitter_id=None):
    """
    Find with a filter and return all matching docs.
    If a title_keyword is provided, it filters articles by titles containing that keyword.
    """
    # Connect to the database (if not already connected)
    if title_keyword:
        # Use regular expressions for case-insensitive search
        filt[ARTICLE_TITLE] = {'$regex': re.compile(title_keyword, re.IGNORECASE)}

    if submitter_id:
        filt[SUBMITTER_ID_FIELD] = submitter_id

    if constrained:
        articles = extras.fetch_all_with_constrained_filter(ARTICLE_COLLECTION, filt, projection)
    else:
        articles = extras.fetch_all_with_filter(ARTICLE_COLLECTION, filt, projection)
    return articles


def fetch_all():
    """
    Find all.
    """
    # Connect to the database (if not already connected)
    articles = fetch_all_with_filter()
    return articles


def get_articles_by_username(username):
    """
    Fetch all articles submitted by a specific user identified by username.

    :param username: The username of the user.
    :return: A list of articles submitted by the user.
    """
    user = users.get_user_by_name(username)
    if not user:
        return f"User {username} NOT found"  # User not found

    user_id = user[OBJECTID]

    # Fetch all articles submitted by this user
    articles = fetch_all_with_filter({SUBMITTER_ID_FIELD: user_id})
    return articles


def fetch_with_combined_filter(or_filter, and_filter, remove_filter, title_keyword=None, db=dbc.USER_DB):
    """
    Find with a filter and return all matching docs.
    Combines OR and AND filters, with projection to remove certain fields.
    """
    if title_keyword:
        query_or_filter = {ARTICLE_TITLE: {'$regex': re.compile(title_keyword, re.IGNORECASE)}, **or_filter}
    else:
        query_or_filter = or_filter
    articles = extras.fetch_with_combined_filter(ARTICLE_COLLECTION, query_or_filter, and_filter, remove_filter, db)
    return articles
