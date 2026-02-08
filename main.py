import os
import json
import urllib.parse
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# State now includes actual battle mechanics
game_state = {
    "mode": "EXPLORE",
    "log": "Use Arrow Keys to find a challenge!",
    "player_hp": 100,
    "enemy": None,
    "map_seed": 1
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.post("/action")
async def take_action(request: Request, action: str = Form(...)):
    global game_state
    
    # 1. Handle Battle Logic
    if game_state["mode"] == "BATTLE" and action not in ["Explore"]:
        # AI decides the outcome of the specific move
        prompt = f"Battle! Player uses {action} against {game_state['enemy']['name']}. " \
                 f"Enemy HP: {game_state['enemy']['hp']}. Player HP: {game_state['player_hp']}. " \
                 "Output ONLY JSON: {'damage': int, 'enemy_move': 'string', 'player_dmg': int, 'text': 'string'}"
        
        try:
            res = await model.generate_content_async(prompt)
            data = json.loads(res.text.replace('```json', '').replace('```', '').strip())
            
            game_state["enemy"]["hp"] -= data['damage']
            game_state["player_hp"] -= data['player_dmg']
            game_state["log"] = f"{data['text']} {game_state['enemy']['name']} used {data['enemy_move']}!"
            
            if game_state["enemy"]["hp"] <= 0:
                game_state["mode"] = "EXPLORE"
                game_state["log"] = f"Victory! You defeated {game_state['enemy']['name']}!"
                game_state["enemy"] = None
        except:
            game_state["log"] = "The clash was intense! Try again."
        
        return game_state

    # 2. Trigger New Encounter
    prompt = "Create a unique Pokemon-style encounter. Output ONLY JSON: " \
             "{'name': 'Creature', 'hp': 100, 'moves': ['Move1', 'Move2'], 'sprite': 'short visual description', 'story': 'string'}"
    
    try:
        response = await model.generate_content_async(prompt)
        data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
        
        game_state["mode"] = "BATTLE"
        game_state["enemy"] = data
        game_state["log"] = data["story"]
    except:
        game_state["log"] = "Something stirs in the shadows..."

    return game_state
