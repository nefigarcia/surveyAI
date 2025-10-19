import os
import json
import openai
import pymysql

# For local development
if os.getenv("VERCEL") is None:
    from dotenv import load_dotenv
    load_dotenv()

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )

    return json.loads(response.choices[0].message.content.strip())

# ✅ Vercel entry point
def handler(request):
    try:
        if request.method != "POST":
            return {
                "statusCode": 405,
                "body": "Method Not Allowed"
            }

        body = request.get_json()
        message = body.get("message", "").strip()

        if not message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'message' field"})
            }

        analysis = analyze_feedback_message(message)

        doctor_score = analysis.get("doctor", 5)
        nurse_score = analysis.get("nurse", 5)
        hospital_score = analysis.get("hospital", 5)
        notes = analysis.get("notes", "")

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO analyzed_feedback (message, doctor_score, nurse_score, hospital_score, notes_analysis)
                VALUES (%s, %s, %s, %s, %s)
            """, (message, doctor_score, nurse_score, hospital_score, notes))
            conn.commit()
        conn.close()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "success",
                "data": {
                    "doctor": doctor_score,
                    "nurse": nurse_score,
                    "hospital": hospital_score,
                    "notes": notes
                }
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
