import time
import slack
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

#Currently hard coded to this private channel
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

def wakeUp():
    named_tuple = time.localtime() # get struct_time
    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    client.chat_postMessage(channel='#apptesting', text='Hello LLMYST I woke up at: '+time_string)
