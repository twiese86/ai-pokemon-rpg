import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# INITIAL STATE
game_state = {
    "player": {"name": "Thomas Jr.", "hp": 100},
    "collection": [],
    "progress": 0,
    "mission": "Defeat the Void Monarch and restore the Prism Core.",
    "current_enemy": None,
    "log": "The world is fading. You are the last hope.",
    "is_victory": False
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.post("/action")
async def take_action(request: Request, action: str = Form(...)):
    global game_state
    
    # 1. Reset Game if finished
    if action == "Restart":
        game_state["progress"] = 0
        game_state["collection"] = []
        game_state["is_victory"] = False
        game_state["current_enemy"] = None
        return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

    # 2. Hard-Coded Battle Logic
    if action in ["Attack", "Skill"] and game_state["current_enemy"]:
        damage = 35 if action == "Attack" else 55
        game_state["current_enemy"]["hp"] -= damage
        
        if game_state["current_enemy"]["hp"] <= 0:
            name = game_state["current_enemy"]["name"]
            game_state["collection"].append(name)
            game_state["progress"] += 20
            game_state["current_enemy"] = None
            game_state["log"] = f"Victory! {name} was captured. Move forward!"
            
            if game_state["progress"] >= 100 and name == "VOID MONARCH":
                game_state["is_victory"] = True
            
            return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

    # 3. AI Narrative Generation
    is_boss = game_state["progress"] >= 100
    prompt = f"""
    Acting as a Pokemon Game Master.
    Mission: {game_state['mission']}
    Current Progress: {game_state['progress']}%
    Action: {action}
    
    If Progress is 100, generate the FINAL BOSS 'VOID MONARCH'.
    Otherwise, generate a wild encounter consistent with the mission story.
    
    Output ONLY JSON:
    {{
        "description": "Narrative flavor text",
        "enemy": {{
            "name": "Creature Name",
            "hp": {500 if is_boss else 100},
            "sprite_prompt": "Pokemon pixel art style, {'ultimate cosmic boss' if is_boss else 'wild creature'}, white background"
        }},
        "options": ["Attack", "Skill"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        game_state["current_enemy"] = data["enemy"]
        game_state["log"] = data["description"]
    except:
        game_state["log"] = "Searching the tall grass..."

    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})
