import logging
import os
import re
import requests
import json
import google.generativeai as genai

# Configure logger
logger = logging.getLogger(__file__)

def format_todo(text: str):
    # Configure the generative AI API with the API key
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Specify the model you want to use (ensure the model name is correct)
    model = genai.GenerativeModel(name="gemini-1.5-flash")
    
    # Define the prompt for generating the content
    prompt = f"""
    請幫我把文字中的代辦事項期限提取出來，並決定一個標題。
    其中時間區間的格式必須符合 Google Calendar 的格式，像是 "20240409T070000Z"。
    由於時區為 GMT+8，所以請記得將時間換算成 GMT+0 的時間。
    如果是中華民國年，請轉換成西元年，例如 110 年要轉換成 2021 年。
    content 請只保留純文字，不要有任何 HTML 標籤。
    不准有 markdown 的格式。
    輸出成 JSON 格式，絕對不能有其他多餘的格式，例如：
    {{
        "deadline": "20240409T070000Z",
        "description": "這是描述"
    }}
    """

    # Generate content using the model
    response = model.generate_content([prompt, text])
    
    # Log the AI response
    logger.info(response.text)
    
    # Return the text as it should already be in JSON format
    return response.text

def format_event(text: str):
    # Configure the generative AI API with the API key
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Specify the model you want to use (ensure the model name is correct)
    model = genai.GenerativeModel(name="gemini-1.5-flash")
    
    # Define the prompt for generating the content
    prompt = f"""
    請幫我把文字中的時間、地點、活動標題 以及活動內容提取出來。
    如果有沒提到的資訊，就留空白。
    其中時間區間的格式必須符合 Google Calendar 的格式，像是 "20240409T070000Z/20240409T080000Z"。
    由於時區為 GMT+8，所以請記得將時間換算成 GMT+0 的時間。
    如果是中華民國年，請轉換成西元年，例如 110 年要轉換成 2021 年。
    content 請只保留純文字，不要有任何 HTML 標籤，並且幫忙列點一些活動的注意事項。
    不准有 markdown 的格式。
    輸出成 JSON 格式，絕對不能有其他多餘的格式，例如：
    {{
        "title": "活動標題",
        "description": "這是描述",
        "location": "地點",
        "startTime": "20240409T070000Z",
        "endTime": "20240409T080000Z",
    }}
    """

    # Generate content using the model
    response = model.generate_content([prompt, text])
    
    # Log the AI response
    logger.info(response.text)
    
    # Return the text as it should already be in JSON format
    return response.text