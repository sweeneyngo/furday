import os
import time
import json
import discord
import traceback
import timeago as timesince
import tweepy
import psycopg2

from datetime import datetime, timezone, timedelta
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

def search(guild, channel):
    _api = api()
    key = config()

    conn = psycopg2.connect(user = DATABASE_USER, 
                        password = DATABASE_PASS,
                        host = DATABASE_HOST,
                        port = DATABASE_PORT,
                        database = DATABASE_DATABASE)
                     
    cur = conn.cursor()

    initdb(cur)
    setchannel(cur, guild, channel)

    tweets = _api.user_timeline(key['twitter_id'], count=5)
    
    for tweet in tweets:

        text = ''
        status = to_json(tweet)

        print(f"Tweet: {status['id']}")

        # check DB if tweet already sent by bot
        res = query(cur, '''
        SELECT * FROM store
        WHERE EXISTS
        (SELECT 1 FROM store WHERE tweet_id=%s)''', (status['id'],))
        
        if res:
           doesExist = 'Yes.' 
        else:
            doesExist = 'No.'

        print(f"Does this tweet exist in store? {doesExist}")

        # if it exists, don't sift through older tweets
        if res != None:
            
            # Task: Check channel DB if current ID is earlier than tweet ID
            
            # Get the tweet from the tweet_id of channel.
            channel_q = query(cur, '''
            SELECT created_date, created_at FROM store
            WHERE tweet_id=
            (SELECT tweet_id FROM channel WHERE channel_id=%s)''', (channel.id,))
            # print("Channel:")
            # print(channel_q, end='\n')

            # Get the tweet from the tweet_id.
            tweet_q = query(cur, '''
            SELECT created_date, created_at FROM store WHERE tweet_id=%s
            ''', (status['id'],))
            
            # print("Tweet:")
            # print(tweet_q, end='\n')

            #Subtract tweet_q[created_at] - channel_q[created_at]
            diff = datetime.combine(tweet_q['created_date'], tweet_q['created_at']) - datetime.combine(channel_q['created_date'], channel_q['created_at'])
            # print(f'Diff: {diff}')

            # Tweet is new for channel, so add!
            if diff > timedelta(hours=0, minutes=0, seconds=0):
                match = checkDaily(cur, status, channel, True)

                if not match:
                    continue
                else:
                    return match

            # If time is equal, or earlier than channel's current tweet, don't send anything.
            print('Tweet already sent to channel! Cancelling. . .')
            break
        
        # If it doesn't exist, update and check
        else:
            match = checkDaily(cur, conn, status, channel)
            if not match:
                continue
            else:
                return match


def updateTweet(cur, conn, status, channel, isMismatch):

    # if new tweet
    if not isMismatch:
        print('Dispersing tweet to channel to match the tweet stack. . .')
        cur.execute('''
        UPDATE channel SET tweet_id=%s
        WHERE channel_id=%s''', (status['id'], channel.id))

    # if update tweet
    else:
        print('Updating channel to match the tweet stack. . .')
        cur.execute('''
        UPDATE channel SET tweet_id=
        (SELECT tweet_id FROM store WHERE tweet_id=%s)
        WHERE channel_id=%s''', (status['id'], channel.id))

    conn.commit()

# check if the tweet is a "Daily" tweet.
def checkDaily(cur, conn, status, channel, isMismatch=False):

    if 'text' in status:
        text = status['text']

    # Response to tweet
    if 'Suggested by' in text and 'in_reply_to_status_id' in status:
        print('Unrelated tweet.', end='\n')
        return None

    # Original tweet
    elif "Today's furry character" in text:
        
        print('Found tweet!', end='\n')
        # store id in DB
        cur = conn.cursor()
        
        created = datetime.strptime(status['created_at'], "%a %b %d %H:%M:%S %z %Y")
        created_date = created.strftime('%Y-%m-%d')
        created_at = created.strftime('%H:%M:%S')

        res = cur.execute('''
        INSERT INTO store (tweet_id, created_date, created_at)
        VALUES (%s, %s, %s)''', (status['id'], created_date, created_at))

        conn.commit()
        

        print('Current Store: ')
        print(query(cur, '''
        SELECT * FROM store'''))

        # update channel->tweet_id
        updateTweet(cur, conn, status, channel, isMismatch)


        cur.connection.close()

        return image(status)

    print('Unrelated tweet.', end='\n')

def image(src):

    source = src
    # source = to_json(src)
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

def initdb(cur):

    cur.execute('''
    CREATE TABLE IF NOT EXISTS server 
    (id SERIAL PRIMARY KEY,
    server_id BIGINT UNIQUE NOT NULL,
    name VARCHAR ( 50 ) NOT NULL)''')
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS channel 
    (id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE NOT NULL,
    server_id BIGINT UNIQUE NOT NULL,
    name VARCHAR ( 50 ) NOT NULL,
    tweet_id BIGINT UNIQUE NOT NULL)''')
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS store 
    (id SERIAL PRIMARY KEY,
    tweet_id BIGINT UNIQUE NOT NULL,
    created_date DATE NOT NULL,
    created_at TIME NOT NULL)''')

def setchannel(cur, guild, channel):

    dead = -1 # snt

    # Add new server if not already there
    cur.execute('''
    INSERT INTO server (server_id, name)
    VALUES (%s, %s)
    ON CONFLICT (server_id)
    DO NOTHING''', (guild.id, guild.name))

    # Add new channel if not already there
    cur.execute('''
    INSERT INTO channel (channel_id, server_id, name, tweet_id)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (server_id)
    DO NOTHING''', (channel.id, guild.id, channel.name, dead))
