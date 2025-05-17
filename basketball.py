# app.py
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import os
import logging
from chatbot_logic import BasketballChatbot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize the chatbot
chatbot = BasketballChatbot()

# Set secret key - use environment variable if available, otherwise use a default
secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-please-change-in-production")
app.secret_key = secret_key
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history", methods=["GET"])
def history():
    return jsonify(session.get("chat_history", []))

@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.json.get("message")
    if not user_input:
        logger.warning("Received empty message in request")
        return jsonify({'error': 'No message provided'}), 400
        
    try:
        # First try to get a general bot response (greetings, etc.)
        response = chatbot.get_bot_response(user_input)
        
        # If it's not a greeting response, try player-specific response
        if "Hey there!" not in response and "I'm great" not in response and "Goodbye" not in response:
            player_response = chatbot.answer_player_question(user_input)
            if "I couldn't find" not in player_response and "I couldn't understand" not in player_response:
                response = player_response
                logger.info(f"Found player-specific response for query: {user_input}")
            else:
                logger.info(f"Using general bot response for query: {user_input}")
            
        # Update chat history
        if "chat_history" not in session:
            session["chat_history"] = []
            
        entry = {"user": user_input, "bot": response}
        session["chat_history"].append(entry)
        session.modified = True
        
        # Log chat history
        try:
            with open("chat_history.txt", "a") as f:
                f.write(f"You: {user_input}\nBot: {response}\n\n")
        except IOError as e:
            logger.error(f"Failed to write to chat history file: {e}")
            
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500

if __name__ == "__main__":
    logger.info("Starting Flask application")
    app.run(debug=True)
