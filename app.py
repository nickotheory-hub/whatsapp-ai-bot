from flask import Flask, request
from dotenv import load_dotenv
import openai
import requests
import os
import sys

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
        data = request.get_json(force=True, silent=True)
        print("[WEBHOOK] Received POST request")
        print("[WEBHOOK DATA]", data)
        sys.stdout.flush()

        try:
            entry = data['entry'][0]
            change = entry['changes'][0]
            value = change['value']

            if 'messages' not in value:
                print("[INFO] No 'messages' field found — likely a delivery receipt or status update.")
                return "ok", 200

            message = value['messages'][0]
            user_message = message['text']['body']
            sender_id = message['from']
            print(f"[MESSAGE RECEIVED] From: {sender_id} — Message: {user_message}")

            # OpenAI GPT call
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_message}]
                )
                ai_reply = response['choices'][0]['message']['content']
                print("[GPT REPLY]", ai_reply)

                send_whatsapp_reply(sender_id, ai_reply)

            except openai.error.AuthenticationError as e:
                print("[OPENAI ERROR] Invalid API key or access denied:", e)
                send_whatsapp_reply(sender_id, "⚠️ This bot is currently offline due to OpenAI authentication issues.")
            except openai.error.RateLimitError as e:
                print("[OPENAI ERROR] Rate limit or credit exhausted:", e)
                send_whatsapp_reply(sender_id, "⚠️ Bot temporarily unavailable — rate limit or quota exceeded.")
            except openai.error.OpenAIError as e:
                print("[OPENAI ERROR] General API error:", e)
                send_whatsapp_reply(sender_id, "⚠️ Something went wrong on the AI side. Try again later.")

        except Exception as e:
            print("[ERROR] Exception occurred in webhook processing:")
            print(e)

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
    try:
        res = requests.post(url, headers=headers, json=data)
        print("[SEND] WhatsApp API responded with:", res.status_code)
        print(res.text)
    except Exception as e:
        print("[SEND ERROR] Failed to send WhatsApp reply:", e)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

