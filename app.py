from flask import Flask, request
from dotenv import load_dotenv
import openai
import requests
import os

app = Flask(__name__)
load_dotenv()
# Replace these with your actual tokens
openai.api_key = os.getenv("OPENAI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.route('/')
def home():
    return 'WhatsApp AI Bot is running locally!'

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Unauthorized", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        message = data['entry'][0]['changes'][0]['value']['messages'][0]
        user_message = message['text']['body']
        sender_id = message['from']

        # Get AI response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        ai_reply = response['choices'][0]['message']['content']
        send_whatsapp_reply(sender_id, ai_reply)

    except Exception as e:
        print("Error:", e)
    return "ok", 200

def send_whatsapp_reply(to, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    res = requests.post(url, headers=headers, json=data)
    print("Sent to WhatsApp:", res.text)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render sets this
    app.run(host="0.0.0.0", port=port)

