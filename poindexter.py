import slack
import random
import openai
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask import request
from slackeventsapi import SlackEventAdapter
import time
from wakeUp import wakeUp
from poindexter_function import *
import jsonify
import threading
#/dumbitdown https://arxiv.org/abs/2307.15111
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)
poindexter_id = token=os.environ['POINDEXTER_ID']
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events',app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
blackList=['U05LN4UMP7U']
wakeUp()

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event',{})
    message_ts = event.get('ts')
    message_thread = event.get('thread_ts')
    print("Message ts:" + str(message_ts))
    print("Message thread:" + str(message_thread))
    if message_thread != None:
        message_ts=message_thread
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    print(user_id)
    print(text)
    if contatinsArxivLink(text):
        print('Does Contain')
        if user_id not in blackList:
                link = "<"+ findArxivLink(text) + ">"
                link=link.replace(">","|Link>")
                #summary = dumb_down_abstract(findArxivLink(text))
                thread = threading.Thread(target=messageDumbingItDown, args=(findArxivLink(text),message_ts,channel_id,checkLevel(text)))
                thread.start()
                finalMessage = f"I see you sent an Arxiv {link}, allow me to explain :point_up: :nerd_face: "
                client.chat_postMessage(channel=channel_id, text=finalMessage,thread_ts=message_ts)
def contatinsArxivLink(txt):
    pattern = r'https://arxiv\.org/abs/[\d.]+'
    return bool(re.search(pattern,txt))

def findArxivLink(txt):
    pattern = r'https://arxiv\.org/abs/[\d.]+'
    match = re.search(pattern,txt)
    return match.group(0)


@app.route('/dumbitdown', methods=['GET','POST'])
def returnDumbedDown():
    data = request.form
    text = data.get('text')
    payload = {
        "response_type": "in_channel",
        "text": "Its ackshually quite simple... :point_up: :nerd_face:",
        "delete_original": "true"
    }
    response_url = request.form.get('response_url')
    # Start the background task
    thread = threading.Thread(target=dumbingItDown, args=(response_url,findArxivLink(text),checkLevel(text)))
    thread.start()
    return payload
    #client.chat_postMessage(channel='autofaq-bot', text= dumb_down_abstract(link)+" "+link)

def messageDumbingItDown(link,message_ts,channel_id,level):
    print("Current level submitted is: " + level)
    result = poindexter(link,level)
    client.chat_postMessage(channel=channel_id, text=result,thread_ts=message_ts)
    return None

def checkLevel(text):
    text = text.lower()
    pattern = r'(child|teenager|undergraduate|graduate|phd)'
    match = re.search(pattern,text)
    if match:
        level = match.group(0)
    else:
        level='child'
    return level

def dumbingItDown(response_url,link,level):
    print("Current level submitted is: " + level)
    result = poindexter(link,level)
    requests.post(response_url, json={
        "response_type": "in_channel",
        "text": result,
    })


@app.route('/getAuthor', methods=['GET','POST'])
def returnAuth():
    data = request.form
    link = data.get('text')
    return get_authors(link)

@app.route('/getTitle', methods=['GET','POST'])
def returnTitle():
    data = request.form
    link = data.get('text')
    return get_title(link)
@app.route('/getAbstract', methods=['GET','POST'])
def returnAbs():
    data = request.form
    link = data.get('text')
    return get_abstract(link)

@app.route('/getIntro', methods=['GET','POST'])
def returnIntro():
    data = request.form
    link = data.get('text')
    return get_introduction(link)

@app.route('/getConclusion', methods=['GET','POST'])
def returnConclusion():
    data = request.form
    link = data.get('text')
    return get_conclusion(link)

if __name__ == "__main__":
    app.run(debug=True, port=4999)
if 1==1:
    print("0")