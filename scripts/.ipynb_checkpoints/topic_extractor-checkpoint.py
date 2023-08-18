from pdfminer.high_level    import extract_text
from dotenv                 import load_dotenv
from pathlib                import Path
from itertools              import chain
from io                     import BytesIO
from datetime               import  datetime
import PyPDF2
import re
import json
import requests
import openai
import os

env_path =                  Path('.')/'.env'
load_dotenv(dotenv_path=    env_path)
openai.api_key =            token=os.environ['CHAT_TOKEN']

def printlist(arr: list):
    for i, element in enumerate(arr):
        print(i)
        print(element) 
        print("--------------------------------\n\n\n\n")

def get_windows(sentences: list[str], max_words:int =4000, overlap:int=200) -> list[str]:
    words =                     list(chain(*[sentence.split() for sentence in sentences]))
    start_idx =                 0
    while   start_idx < len(words):
        end_idx =               start_idx + max_words
        if  end_idx > len(words):
            end_idx =           len(words)
        window_words =          words[start_idx:end_idx]
        window_text =           ' '.join(window_words)
        yield window_text
        start_idx +=            (max_words - overlap)

def get_sentences(file_path: str) -> list[str]:
    text =                      extract_text(file_path)
    sentences =                 re.split(r'[.!?]', text)
    sentences =                 [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences
def get_sentences_from_text(text:str) -> list[str]:
    sentences =                 re.split(r'[.!?]', text)
    sentences =                 [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences

def extract_points(chunk, topics):
    system_prompt = (
        "You are an interviewer trying to extract the main points out from a piece of paper in preperation for an interview. "
        "Use the extract() function to get the chapter names and keypoints out from the paper. The keys for the json are: topics: [topic, subtopics : [subtopic]]"   
    )
    user_prompt =               "Text to extract content from:\n"
    user_prompt +=              chunk
    functions = [
        {
            "name": "extract_topics",
            "description": (
                "Get the section titles, main topics and important points from the paper. " 
                "Focus on new conceptst, novel techniques and discoveries. "
                "Also extract interesting subpoints brought up for every topic."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topics" :{
                        "type": "array",
                        "items": {
                            "topic": {
                                "type": "string",
                                "description": "name of topic or important point from the paper",
                            },
                            "subtopics": {
                                "type": "array",
                                "items": {
                                    "point":{
                                        "type": "string",
                                        "description": "subtopic discussed for every main topic in the paper",
                                    }
                                },
                                "required": ["point"],
                            }
                            
                        },
                        "required": ["topic", "subtopics"],
                    }
                    
                },
                "required": ["topics"],
            },
        },
    ]
    completion = openai.ChatCompletion.create(
        model =             "gpt-3.5-turbo-16k",
        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
        ],
        functions =         functions,
        function_call =     {"name": "extract_topics"},
        max_tokens =        5000
    )
    choice =                completion.choices[0]
    print(choice)
    encoded_data =          choice.message.function_call.arguments
    #print(json.dumps(json.loads(encoded_data), indent=4))
    return encoded_data

def extract_chunk(chunk, extraction_count:int = 5):
    extractions =           []
    for i in range(extraction_count): 
        topics =            []
        #SWAP OUT EXTRACTION FUNCTION HERE
        #---------------------------------
        json_raw =          extract_points(chunk, topics)
        #print(json_raw)
        data =              json.loads(json_raw)
        topics_key =        list(data.keys())
        topics =            data[topics_key[0]]
        topic_count =       len(topics) 
        subtopic_count =    0
        for topic in topics:
            try:
                topic_keys =            list(topic.keys())
                try:
                    subtopic_key =      topic_keys[1]
                    subtopic_count +=   len(topic[subtopic_key])
                except:
                    pass
            except:
                pass
        #print("Topics: " + str(topic_count))
        #print("Subtopics: " + str(subtopic_count))
        extraction_score =              topic_count + subtopic_count*0.5
        extraction =                    [topics, topic_count, subtopic_count, extraction_score]
        extractions.append(extraction)
    sorted_extractions =                sorted(extractions, key=lambda x: x[3], reverse=True)
    best_extraction =                   sorted_extractions[0]
    return best_extraction
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
def extract_from_url(url):
    text =                  get_pdf_text(url)
    sentences =             get_sentences_from_text(text)
    windows =               list(get_windows(sentences))
    print(len(windows))
    extractions =           []
    for i, chunk  in enumerate(windows):
        print(i)
        extraction =        extract_chunk(str(chunk))
        extraction.append(i)
        extractions.append(extraction)
    data =                  {
            "url" : url,
            "data": extractions
            }

    time = formatted_time()
    savepath =              "./cache/" + time+ ".json"
    with open(savepath, "w") as f:
        json.dump(data, f)

def formatted_time() -> str:
    now =                       datetime.now()
    formatted_time =            now.strftime('%H:%M-%d-%m-%Y')
    return formatted_time
def extract_doc(filepath, savepath):
    if os.path.exists(savepath):
        return True
    sentences =             get_sentences(filepath)
    windows =               list(get_windows(sentences))
    print(len(windows))
    extractions =           []
    for i, chunk  in enumerate(windows[:3]):
        print(i)
        extraction =        extract_chunk(str(chunk))
        extraction.append(i)
        extractions.append(extraction)
    data =                  {"data": extractions}
    with open(savepath, "w") as f:
        json.dump(data, f)

def load_extraction(filepath):
    with open(filepath, "r") as f:
        data =              json.load(f)
    return data


if __name__ == "__main__":
    url = input("arXiv abs link: ")
    extract_from_url(url)
