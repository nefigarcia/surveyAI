import os
import json
import openai
import pymysql
from dotenv import load_dotenv
from flask import Request, Response

# Load .env locally
load_dotenv()

# OpenAI Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# MySQL connection params
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Connect to MySQL
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

# Analyze feedback using OpenAI
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

# Main handler
def handler(request: Request) -> Response:
    try:
        if request.method != 'POST':
            return Response("Method Not Allowed", status=405)

        data = request.get_json()
        message = data.get("message", "").strip()

        if not message:
            return Response(json.dumps({"error": "Missing 'message' field"}), status=400, mimetype='application/json')

        analysis = analyze_feedback_message(message)

        doctor_score = analysis.get("doctor", 5)
        nurse_score = analysis.get("nurse", 5)
        hospital_score = analysis.get("hospital", 5)
        notes = analysis.get("notes", "")

        # Insert into MySQL
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO analyzed_feedback (message, doctor_score, nurse_score, hospital_score, notes_analysis)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (message, doctor_score, nurse_score, hospital_score, notes))
            conn.commit()

        conn.close()

        return Response(json.dumps({
            "status": "success",
            "data": {
                "doctor": doctor_score,
                "nurse": nurse_score,
                "hospital": hospital_score,
                "notes": notes
            }
        }), status=200, mimetype='application/json')

    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
