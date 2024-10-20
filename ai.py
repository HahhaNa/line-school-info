import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()  # 加載 .env 文件中的變量
def ai_reply(messages):
    gemini_key = os.getenv("GEMINI_API_KEY")
    # Initialize the Gemini Pro API
    genai.configure(api_key=gemini_key)

    model = genai.GenerativeModel("gemini-1.5-pro")
    # messages = "課程名稱: 電路與電子學一Circuits and Electronics (I) 作業名稱: HW9 最後期限: 2024-06-14 23:59 請把握時間完成。 這是系統自動發出的通知信，請勿直接回覆，此信箱可能無人收信提醒您，請於 2024-06-14 (23:59) 前完成作業繳交"
    response = model.generate_content(
        f"now is 2024, and find event name, place, and the deadline in the following message, and return in the format:event_name, place, yyyy/mm/dd hh:mm:ss \n{messages}"
    )
    print(response.text)
    return response.text