from pdfminer.high_level    import extract_text
from dotenv                 import load_dotenv
from pathlib                import Path
from itertools              import chain
from io                     import BytesIO
from datetime               import  datetime
from topic_extractor        import * 
import PyPDF2
import re
import json
import requests
import openai
import os

env_path =                  Path('.')/'.env'
load_dotenv(dotenv_path=    env_path)
openai.api_key =            token=os.environ['CHAT_TOKEN']
def print_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
        print(json.dumps(data, indent=4))

def summarize_topic(self, topic, subtopics, chunk):
    system_prompt =         self.identity
    system_prompt += (
        f"You are preparing notes for your own use for an interview discussing the paper \"{self.paper}\", "
        f"The topic that you are preparing about is {topic}, which contains the subtopics: {subtopics}. "
        "Make sure that your notes have all the information that you will need, "
        "and put extreme care into accuracy of the information. "
        f"The section of the paper you're summarizing is attached here:\n{chunk}"
    )
    user_prompt = ""
    response =  openai.ChatCompletion.create(
            model=          self.model,
            messages=[
                    {"role": "system", "content": system_prompt},
            ],
            temperature =   0.8,
            max_tokens =    1000
            )
    self.record.append(response)
    return response['choices'][0]['message']['content']

if __name__ == "__main__":
    extraction_path = input("Path to extracted topics json: ")
    if (extraction_path == ""):
        extraction_path = "./cache/13:52-14-08-2023.json"
    data =                      load_extraction(extraction_path)
    extraction =                data['data']
    print_json_file(extraction_path) 
