import slack
import openai
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import pandas as pd
import urllib.request
import requests
import PyPDF2
from io import BytesIO
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)
openai.api_key = token=os.environ['CHAT_TOKEN']

def get_html(url):
    response = urllib.request.urlopen(url)
    html_content = response.read().decode("utf-8")
    return html_content
def get_pdf_text(url):
    arxiv_id = url[22:]
    url = "https://arxiv.org/pdf/" + arxiv_id + ".pdf"
    response = requests.get(url)
    # Ensure the request was successful
    if response.status_code == 200:
        # Step 2: Converting the PDF to a more readable format
        with BytesIO(response.content) as open_pdf_file:
            read_pdf = PyPDF2.PdfReader(open_pdf_file)
            num_pages = len(read_pdf.pages)
            # Step 3: Extracting the text
            text_content = ""
            for i in range(num_pages):
                page = read_pdf.pages[i]
                text_content += page.extract_text()
        return(text_content)
    else:
        return("Pattern not found [Failed match flag]")
def fetch_abstract_from_html(url):
    pattern = r'<meta property="og:description" content="(.*?)"/>'
    html_content = str(get_html(url))
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        extracted_content = match.group(1)
        return(extracted_content)
    else:
        return("Pdf not found [Failed match flag]")
def fetch_abstract(text):
    #print(text)
    pattern = r'Abstract(.*?).\n1'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        extracted_content = match.group(1)
        return(extracted_content)
    else:
        return("Conclusion not found [Failed match flag]")
def fetch_conclusion(text):
    #print(text)
    pattern = r'Conclusion(.*?)Acknowledgments'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        extracted_content = match.group(1)
        return(extracted_content)
    else:
        return("Conclusion not found [Failed match flag]")
def fetch_introduction(text):
    #eturn(text)
    pattern = r'Introduction(.*?).\n2'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        extracted_content = match.group(1)
        return(extracted_content)
    else:
        return("Introduction not found [Failed match flag]")
def remove_newlinechar(user_message):
    pattern = r'\n'
    match = re.search(pattern, user_message, re.DOTALL)
    if match:
        pings = match.group(0)
        user_message = user_message.replace(str(pings), " ")
    return(user_message)
def fetch_authors_from_html(url):
    pattern = r'<meta name="citation_author" content="(.*?)" />'
    html_content = str(get_html(url))
    match = re.findall(pattern, html_content, re.DOTALL)
    if match:
        return(match)
    else:
        return("Authors not found [Failed match flag]")
def fetch_title_from_html(url):
    pattern = r'<meta name="twitter:title" content="(.*?)"/>'
    html_content = str(get_html(url))
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        extracted_content = match.group(1)
        return(extracted_content)
    else:
        return("Title not found [Failed match flag]")
    
def dumb_this_down(text, age):
    system_prompt = "Given the following text from a paper, summarize it so that a " + str(age) + " year old could read it"
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-16k",
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ],
    max_tokens = 100,
    temperature = 0.8,
    )
    return response["choices"][0]["message"]["content"]


################################################
###########  FUNCTIONS FOR MATEO  ##############
################################################
def get_title(url):
    return fetch_title_from_html(url)
def get_authors(url):
    return fetch_authors_from_html(url)
def get_abstract(url):
    return fetch_abstract_from_html(url)
def get_introduction(url):
    return remove_newlinechar(fetch_introduction(get_pdf_text(url)))
def get_conclusion(url):
    return fetch_conclusion(remove_newlinechar(get_pdf_text(url)))
def fetch_everything(url):
    pdf = get_pdf_text(url)
    content = {}
    content["title"] = get_title(url)
    content["authors"] = get_authors(url)
    content["abstract"] =  get_abstract(url)
    content["introduction"] = fetch_introduction(pdf)
    content["conclusion"] =  fetch_conclusion(pdf)
    return content
test_url = "https://arxiv.org/abs/2205.03451"

def append_title(meta_prompt, title):
    if ("[Failed match flag]" not in title):
        meta_prompt += "Summarize the following paper titled \"" + title + "\" "
    else:
        meta_prompt += "Summarize the following paper "
    return meta_prompt
def append_authors(meta_prompt, authors):
    if ("[Failed match flag]" in authors):
        return meta_prompt
    if (len(authors) == 1):
        return meta_prompt + "writen by " + author + " "
    meta_prompt += "written by "
    for i in range(len(authors)-1):
        meta_prompt += authors[i] + ", "
    meta_prompt += authors[-1] + " "
    return meta_prompt
# Levels = ["child", "teenager", "undergraduate", "graduate", "phd"]
def append_level(meta_prompt, level):
    if level == "child":
        return meta_prompt + "such that a child could understand it:\n"
    if level == "teenager":
        return meta_prompt + "such that a teenager could understand it:\n"
    if level == "undergraduate":
        return meta_prompt + "at the level of an undergraduate:\n"
    if level == "graduate":
        return meta_prompt + "to a graduate or masters program audience:\n"
    if level == "phd":
        return meta_prompt + "to a phd, do not leave out technicalities:\n"
def append_abstract(meta_prompt, abstract):
    if ("[Failed match flag]" in abstract):
        return meta_prompt
    abstract = remove_newlinechar(abstract)
    meta_prompt += "Abstract: " + abstract + "\n"
    return meta_prompt
def append_introduction(meta_prompt, introduction):
    if ("[Failed match flag]" in introduction):
        return meta_prompt
    introduction = remove_newlinechar(introduction)
    meta_prompt += "Introduction: " + introduction + "\n"
    return meta_prompt
def append_conclusion(meta_prompt, conclusion):
    if ("[Failed match flag]" in conclusion):
        return meta_prompt
    conclusion = remove_newlinechar(conclusion)
    meta_prompt += "Conclusion: " + conclusion + "\n"
    return meta_prompt
def format_meta_prompt(content, level):
    meta_prompt = ""
    meta_prompt = append_title(meta_prompt, content["title"])
    meta_prompt = append_authors(meta_prompt, content["authors"])
    meta_prompt = append_level(meta_prompt, level)
    meta_prompt += "\n"
    meta_prompt = append_abstract(meta_prompt, content["abstract"])
    meta_prompt += "\n"
    meta_prompt = append_introduction(meta_prompt, content["introduction"])
    meta_prompt += "\n"
    meta_prompt = append_conclusion(meta_prompt, content["conclusion"])
    return meta_prompt



##### Function for Mateoooooo #################
# for level, select from "child", "teenager", "undegraduate", "graduate", "phd" 
def poindexter(url, level = "child"):
    content = fetch_everything(url)
    meta_prompt = format_meta_prompt(content, level)
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-16k",
    messages = [
        {"role": "system", "content": meta_prompt},
    ],
    max_tokens = 500,
    temperature = 0.8,
    )
    return response["choices"][0]["message"]["content"]
print(poindexter(test_url, "child"))
