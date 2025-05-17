from dotenv import load_dotenv
load_dotenv()

import csv
import json
from typing import Dict, List, Optional
import os
import openai
from openai import OpenAI
from datetime import datetime
import httpx

class BasketballChatbot:
    def __init__(self, csv_path: str = 'NBA-playerlist.csv'):
        self.players_data = self._load_players_csv(csv_path)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Hardcoded NBA champions from 2022-2024
        self.nba_champions = {
            2022: "Golden State Warriors",
            2023: "Denver Nuggets",
            2024: "Boston Celtics"
        }
        
    def _get_openai_response(self, prompt: str) -> str:
        try:
            system_message = "You are a knowledgeable basketball assistant. "
            if "use csv" in prompt.lower():
                # Include CSV data in the prompt
                csv_data = "\n".join([f"{player['DISPLAY_FIRST_LAST']}: {player['TEAM_NAME']}" for player in self.players_data])
                system_message += f"Use the following player data from the CSV file to answer questions accurately:\n{csv_data}\n"
            else:
                system_message += "Use your own intelligence and knowledge of basketball trends and statistics. "
            
            # Include hardcoded NBA champions if the question is about champions
            if "nba champion" in prompt.lower() or "who won" in prompt.lower():
                champions_info = "\n".join([f"{year}: {team}" for year, team in self.nba_champions.items()])
                system_message += f"Here are the NBA champions from 2022-2024:\n{champions_info}\n"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting OpenAI response: {str(e)}")
            return "I'm having trouble accessing my advanced features right now."

    def _load_players_csv(self, filename: str) -> List[Dict]:
        try:
            players = []
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Player data file not found at {filename}")
            
            with open(filename, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                                 for k, v in row.items()}
                    players.append(cleaned_row)
            return players
        except Exception as e:
            print(f"Error loading player data: {str(e)}")
            return []

    def find_player_by_name(self, name: str) -> Optional[Dict]:
        try:
            name = name.lower().strip()
            # First try exact match
            for player in self.players_data:
                if name == player['DISPLAY_FIRST_LAST'].lower():
                    return player
            
            # Then try partial match
            for player in self.players_data:
                if name in player['DISPLAY_FIRST_LAST'].lower():
                    return player
            return None
        except Exception as e:
            print(f"Error searching for player: {str(e)}")
            return None

    def get_player_team(self, player: Dict) -> str:
        try:
            if player['TEAM_NAME']:
                if player['TEAM_CITY']:
                    return f"{player['TEAM_CITY']} {player['TEAM_NAME']}"
                return player['TEAM_NAME']
            return "an unknown team"
        except Exception as e:
            print(f"Error getting team info: {str(e)}")
            return "an unknown team"

    def get_player_career(self, player: Dict) -> str:
        try:
            if player['FROM_YEAR'] and player['TO_YEAR']:
                return f"{player['FROM_YEAR']} to {player['TO_YEAR']}"
            return "unknown years"
        except Exception as e:
            print(f"Error getting career info: {str(e)}")
            return "unknown years"

    def get_player_status(self, player: Dict) -> str:
        try:
            if player['ROSTERSTATUS'] == '1':
                return "Active"
            return "Inactive"
        except Exception as e:
            print(f"Error getting status: {str(e)}")
            return "Unknown"

    def get_player_other_leagues(self, player: Dict) -> str:
        try:
            if player['OTHERLEAGUE_EXPERIENCE_CH'] and player['OTHERLEAGUE_EXPERIENCE_CH'] != '00':
                return "Has experience in other leagues"
            return "No experience in other leagues"
        except Exception as e:
            print(f"Error getting other leagues info: {str(e)}")
            return "Unknown"

    def get_all_player_info(self, player: Dict) -> str:
        try:
            info = [
                f"Name: {player['DISPLAY_FIRST_LAST']}",
                f"Career: {self.get_player_career(player)}",
                f"Team: {self.get_player_team(player)}",
                f"Current Status: {self.get_player_status(player)}",
                f"{self.get_player_other_leagues(player)}"
            ]
            return " | ".join(info)
        except Exception as e:
            print(f"Error getting all player info: {str(e)}")
            return "Unable to retrieve complete player information"

    def answer_player_question(self, user_input: str) -> str:
        try:
            user_input_lower = user_input.lower()
            player_name = None
            
            # Check if the input starts with 'ai:' to route to OpenAI
            if user_input_lower.startswith('ai:'):
                return self._get_openai_response(user_input[3:].strip())
            
            # Check for prediction-related questions
            if any(word in user_input_lower for word in ["predict", "prediction", "future", "next season", "upcoming"]):
                return self._get_openai_response(f"Based on basketball knowledge and current trends, {user_input}")
            
            # Extract player name from various question formats
            if "what team did" in user_input_lower and "play for" in user_input_lower:
                name_start = user_input_lower.find("what team did") + len("what team did")
                name_end = user_input_lower.find("play for")
                player_name = user_input_lower[name_start:name_end].strip()
            elif "which team did" in user_input_lower and "play for" in user_input_lower:
                name_start = user_input_lower.find("which team did") + len("which team did")
                name_end = user_input_lower.find("play for")
                player_name = user_input_lower[name_start:name_end].strip()
            elif "when did" in user_input_lower and "play" in user_input_lower:
                player_name = user_input_lower.replace("when did", "").replace("play", "").strip()
            elif "is" in user_input_lower and "active" in user_input_lower:
                player_name = user_input_lower.replace("is", "").replace("active", "").strip()
            elif "did" in user_input_lower and "play in other leagues" in user_input_lower:
                player_name = user_input_lower.replace("did", "").replace("play in other leagues", "").strip()
            elif "tell me everything about" in user_input_lower:
                player_name = user_input_lower.replace("tell me everything about", "").strip()
            else:
                # Try direct player name search if it's at least two words
                words = user_input_lower.split()
                if len(words) >= 2:
                    player_name = user_input_lower.strip()

            if not player_name:
                return "I couldn't understand which player you're asking about. Please include a player's name in your question."

            player = self.find_player_by_name(player_name)
            if not player:
                return f"I couldn't find any information about {player_name}. Please check the spelling or try a different player name."

            # Handle different types of questions
            if "what team did" in user_input_lower or "which team did" in user_input_lower:
                team = self.get_player_team(player)
                return f"{player['DISPLAY_FIRST_LAST']} played for the {team}."
            
            elif "when did" in user_input_lower:
                career = self.get_player_career(player)
                return f"{player['DISPLAY_FIRST_LAST']} played from {career}."
            
            elif "is" in user_input_lower and "active" in user_input_lower:
                status = self.get_player_status(player)
                return f"{player['DISPLAY_FIRST_LAST']} is {status}."
            
            elif "did" in user_input_lower and "play in other leagues" in user_input_lower:
                other_leagues = self.get_player_other_leagues(player)
                return f"{player['DISPLAY_FIRST_LAST']} {other_leagues.lower()}."
            
            elif "tell me everything about" in user_input_lower:
                return self.get_all_player_info(player)
            
            # If just the player name is provided, return comprehensive info
            return self.get_all_player_info(player)

        except Exception as e:
            print(f"Error processing player question: {str(e)}")
            return "I encountered an error while processing your question. Please try again with a different format."

    def get_bot_response(self, user_input: str) -> str:
        try:
            user_input = user_input.lower().strip()

            # Check for NBA champion questions
            if "nba champion" in user_input or "who won" in user_input:
                # Check if a specific year is mentioned
                for year in self.nba_champions.keys():
                    if str(year) in user_input:
                        return f"The NBA champion in {year} was the {self.nba_champions[year]}."
                # If no specific year is mentioned, return all champions
                champions_info = "\n".join([f"{year}: {team}" for year, team in self.nba_champions.items()])
                return f"Here are the NBA champions from 2022-2024:\n{champions_info}"

            # Greetings
            if any(greeting in user_input for greeting in ["hello", "hi", "hey"]):
                return "Hey there! I'm your basketball knowledge assistant. Ask me about players, their teams, or get predictions about upcoming games and seasons!"

            # How are you variations
            if any(phrase in user_input for phrase in ["how are you", "how's it going", "how you doing"]):
                return "I'm great, thanks for asking! Ready to talk basketball!"

            # Goodbye
            if "bye" in user_input or "goodbye" in user_input:
                return "Goodbye! Come back anytime to talk basketball!"

            # Try to answer player questions
            response = self.answer_player_question(user_input)
            if "I couldn't find" not in response and "I couldn't understand" not in response:
                return response

            # Default response for unrecognized questions
            return "I'm not sure how to answer that. Try asking about a specific player's team, career years, active status, or get predictions about upcoming games!"

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error while processing your question. Please try again with a different format."

# Create an instance of the chatbot
chatbot = BasketballChatbot()

# Example usage
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        response = chatbot.get_bot_response(user_input)
        print(f"Bot: {response}")
