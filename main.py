import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Universal Key Support
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

game_state = {
    "mode": "MAP", # MAP or BATTLE
    "player_pos": {"x": 200, "y": 200},
    "map_theme": "vibrant lush pixel art pokemon world map top down",
    "current_enemy": None,
    "collection": []
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.post("/encounter")
async def trigger_encounter(request: Request):
    global game_state
    prompt = f"RPG Mode. Create a wild encounter for a {game_state['map_theme']}. Return ONLY JSON: {{'story': '...', 'enemy': {{'name': '...', 'hp': 100, 'sprite': 'pixel art monster'}}}}"
    
    try:
        response = await model.generate_content_async(prompt)
        data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
        game_state["mode"] = "BATTLE"
        game_state["current_enemy"] = data["enemy"]
        game_state["log"] = data["story"]
    except:
        game_state["mode"] = "MAP" # Fallback if AI fails
        
    return game_state

@app.post("/reset")
async def reset_to_map():
    game_state["mode"] = "MAP"
    game_state["current_enemy"] = None
    return {"status": "ok"}
