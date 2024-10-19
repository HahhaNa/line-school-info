import json
import os
import requests
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from PIL import Image
from io import BytesIO
import pytesseract
import uvicorn

app = FastAPI()

def check_img(img_url: str):
    try:
        response = requests.get(img_url)
        response.raise_for_status()  # Raise an error for bad responses
        image_data = response.content
        image = Image.open(BytesIO(image_data))
        return image
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Image URL is not valid: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process the image: {str(e)}")

def extract_text_from_image(image: Image.Image):
    try:
        text = pytesseract.image_to_string(image, lang='eng')
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        return text.replace('\n', ' ').strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text from image: {str(e)}")

@app.get("/")
def find_image_keyword(img_url: str = "https://assets.ltkcontent.com/images/977901/What-Is-an-Article-in-Grammar_27c5571306.jpg"):
    image = check_img(img_url)
    extracted_text = extract_text_from_image(image)
    return {"extracted_text": extracted_text}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
