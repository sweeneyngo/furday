import os
import time
import json
import discord
import traceback
import timeago as timesince
import tweepy
import psycopg2

from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv

from io import BytesIO

load_dotenv(find_dotenv())
ACCESS_SECRET = os.environ.get("ACCESS_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
DATABASE_USER = os.environ.get("DATABASE_USER")
DATABASE_PASS = os.environ.get("DATABASE_PASS")
DATABASE_HOST = os.environ.get("DATABASE_HOST")
DATABASE_PORT = os.environ.get("DATABASE_PORT")
DATABASE_DATABASE = os.environ.get("DATABASE_DATABASE")

def config(filename: str = "config"):
    """ Fetch default config file """
    try:
        with open(f"{filename}.json", encoding='utf8') as data:
            return json.load(data)
    except FileNotFoundError:
        raise FileNotFoundError("JSON file wasn't found")


def traceback_maker(err, advance: bool = True):
    """ A way to debug your code anywhere """
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = ('```py\n{1}{0}: {2}\n```').format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"

def api():

    key = config()
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
    return api

def search():
    _api = api()
    key = config()

    conn = psycopg2.connect(user = DATABASE_USER, 
                        password = DATABASE_PASS,
                        host = DATABASE_HOST,
                        port = DATABASE_PORT,
                        database = DATABASE_DATABASE)
                     
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS store (id SERIAL PRIMARY KEY,
    tweet BIGINT NOT NULL UNIQUE)''')

    tweets = _api.user_timeline(key['twitter_id'], count=5)
    
    for tweet in tweets:

        text = ''
        status = to_json(tweet)

        # check DB if tweet already sent by bot
        res = query(cur, '''
        SELECT * FROM store
        WHERE EXISTS
        (SELECT 1 FROM store WHERE tweet=%s)''', (status['id'],))
        
        print(f"Does it exist in DB? {res}")
        
        # don't sift through older tweets
        if res != None:
            break

        if 'text' in status:
            text = status['text']

        # Response to tweet
        if 'Suggested by' in text and 'in_reply_to_status_id' in status:
            continue

        # Original tweet
        elif "Today's furry character" in text:
            
            # store id in DB
            cur = conn.cursor()
            
            res = cur.execute('''
            INSERT INTO store (tweet)
            VALUES (%s)''', (status['id'],))

            conn.commit()
            # print current table
            print(query(cur, '''
            SELECT * FROM store'''))

            cur.connection.close()

            return image(tweet)

def image(src):

    source = to_json(src)
    key = config()
    
    img = key['err_image']
    profile = key['err_image']
    text = source['text'] or 'Nothing found.'
    time = datetime.now()

    if 'media' in source['entities']:
        for image in source['entities']['media']:

            if 'media_url_https' in image:
                img = image['media_url_https']
            break

    if 'profile_image_url' in source['user']:
        profile = source['user']['profile_image_url']

    if 'created_at' in source:
        created = datetime.strptime(source['created_at'], "%a %b %d %H:%M:%S %z %Y")
        time = timesince.format(datetime.now(timezone.utc) - created)

    return text, img, profile, time

def send_embed(color, user, res, img, profile, time):
    key = config()
    embed = discord.Embed(colour=color, timestamp=datetime.utcnow())
    embed.set_author(name=f"{user} | {key['version']}", icon_url=user.avatar_url)
    embed.set_thumbnail(url=img)
    embed.add_field(name="Today's furry:", value=res)
    embed.add_field(name="Requested:", value=time)
    embed.set_image(url=img)
    embed.set_footer(text='@daily_furry', icon_url=profile)
    return embed

def to_json(obj):
    return json.loads(json.dumps(obj))

def query(cur, query, args=()):

    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()]
    return (r[0] if r else None)