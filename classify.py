import logging
import os
import google.generativeai as genai
from formatData import format_data

# Configure logger
logger = logging.getLogger(__file__)

def classify(text: str):
    # Configure the generative AI API with the API key
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Specify the model you want to use (ensure the model name is correct)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = """
    請幫我判斷文字，分類是哪一種類型
    總共有三種類型：筆記、待辦事項、活動。
    如果是筆記，請輸出 "note"。
    如果是待辦事項，請輸出 "todo"。
    如果是活動，請輸出 "event"。
    分辨不出來的話，請輸出 "unknown"。
    只能輸出這四種類型，不准有其他的輸出。
    """

    # Generate content using the model
    response = model.generate_content([prompt, text])
    response_type = response.text.strip()  # Clean up any extra whitespace or newlines
    
    # Log the AI response
    logger.info(f"AI response: {response_type}")
    
    # Use the cleaned-up response type to format the data
    formatted_response = format_data(response_type, text)
    
    return response_type, formatted_response

if __name__ == "__main__":
    # Test the function with a sample text
    text = input("Please input the text you want to classify: ")
    response_type, formatted_output = classify(text)
    print(f"Type: {response_type}")
    print(f"Formatted Output: {formatted_output}")
