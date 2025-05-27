from flask import Flask, request, render_template
import os
import sqlite3
import datetime
import requests

import google.generativeai as genai
from dotenv import load_dotenv

#load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file.")

telegram_key = os.getenv("TELEGRAM_TOKEN")
if not api_key:
    raise EnvironmentError("TELEGRAM_TOKEN not found in .env file.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def main():
    return (render_template("main.html"))

@app.route("/index", methods=["GET", "POST"])
def index():
    return (render_template("index.html"))

@app.route("/paynow", methods=["GET", "POST"])
def paynow():
    return (render_template("paynow.html"))

@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    return (render_template("prediction.html"))

@app.route("/prediction_reply", methods=["GET", "POST"])
def prediction_reply():
    q = float(request.form.get("q"))
    print(q)
    return (render_template("prediction_reply.html",r=90.2 + (-50.6*q)))

@app.route("/gemini", methods=["GET", "POST"])
def gemini():
    return (render_template("gemini.html"))

@app.route("/gemini_reply", methods=["GET", "POST"])
def gemini_reply():
    q = request.form.get("q")
    print(q)
    r = model.generate_content(q)
    return (render_template("gemini_reply.html",r=r.text))

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    q = request.form.get("q")
    if not q:
      return render_template("add_user.html", error="Name cannot be empty.")

    t = datetime.datetime.now()
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("insert into users(name,timestamp) values(?,?)",(q,t))
    conn.commit()
    c.close()
    conn.close()
    return render_template("add_user.html", error=None)

@app.route("/user_log", methods=["GET", "POST"])
def user_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("select * from users")
    rows = c.fetchall()
    c.close()
    conn.close()
    return (render_template("user_log.html",rows=rows))

@app.route("/delete_log", methods=["GET", "POST"])
def delete_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    return (render_template("delete_log.html"))

@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():

    domain_url = os.getenv('WEBHOOK_URL')

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{telegram_key}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    
    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{telegram_key}/setWebhook?url={domain_url}/telegram"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot t.me/dsai_ttt_gemini_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    
    return(render_template("telegram.html", status=status))

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            r_text = "Welcome to the Gemini Telegram Bot! You can ask me any finance-related questions."
        else:
            # Process the message and generate a response
            system_prompt = "You are a financial expert. Answer ONLY questions related to finance, economics, investing, and financial markets. If the question is not related to finance, state that you cannot answer it."
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = model.generate_content(prompt)
            r_text = r.text
        
        # Send the response back to the user
        send_message_url = f"https://api.telegram.org/bot{telegram_key}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text})
    # Return a 200 OK response to Telegram
    # This is important to acknowledge the receipt of the message
    # and prevent Telegram from resending the message
    # if the server doesn't respond in time
    return('ok', 200)

if __name__ == '__main__':
    app.run()