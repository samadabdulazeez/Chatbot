# chatbot_logic.py
def get_bot_response(user_input):
    responses = {
        "hi": "Hello!",
        "how are you": "I'm a bot, but I'm doing great!",
        "bye": "Goodbye!",
    }
    return responses.get(user_input.lower(), "Sorry, I didn't understand that.")
