from flask import Flask, request
from dotenv import load_dotenv
import openai
import requests
import os

app = Flask(__name__)
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.route('/')
def home():
    return 'WhatsApp AI Bot is running!'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("[VERIFY] Webhook verified.")
            return challenge, 200
        print("[VERIFY] Failed verification.")
        return "Unauthorized", 403

    if request.method == 'POST':
        data = request.get_json()
        print("[WEBHOOK] Received POST request")
        print("[WEBHOOK DATA]", data)

        try:
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            user_message = message['text']['body']
            sender_id = message['from']
            print(f"[MESSAGE] From: {sender_id} - Text: {user_message}")

            # GPT response
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": user_message}]
            )
            ai_reply = response['choices'][0]['message']['content']
            print("[GPT REPLY]", ai_reply)

            send_whatsapp_reply(sender_id, ai_reply)

        except Exception as e:
            print("[ERROR]", e)

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
    print("[SEND] Response from WhatsApp:", res.status_code, res.text)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
