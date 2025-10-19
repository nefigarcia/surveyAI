import os
import json
import pymysql
from openai import OpenAI

# Load .env locally
if os.getenv("VERCEL") is None:
    from dotenv import load_dotenv
    load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# DB credentials
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )


def analyze_feedback_message(message):
    prompt = (
        "You are a helpful assistant analyzing patient feedback. "
        "Give each of the following a score from 1 (very bad) to 10 (excellent): doctor, nurse, hospital. "
        "If not mentioned, give a score of 5. Explain why you gave those scores in a 'Notes Analysis'. "
        "Respond ONLY in JSON format like this:\n"
        "{ \"doctor\": 8, \"nurse\": 5, \"hospital\": 9, \"notes\": \"...\" }"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )

    return json.loads(completion.choices[0].message.content.strip())


# ✅ Correct Vercel entry point
   print("Function loaded!")  # This will show in build logs

def handler(request):
    print("Handler triggered")  # This will show in runtime logs
    return {
        "statusCode": 200,
        "body": "Hello"
    }


