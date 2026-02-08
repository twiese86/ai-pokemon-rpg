import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Use your universal key
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

game_state = {
    "player": {"name": "Thomas Jr.", "hp": 100},
    "progress": 0,
    "current_enemy": None,
    "bg_style": "vibrant lush pokemon forest",
    "log": "The world map is generating... welcome!"
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.post("/action")
async def take_action(request: Request, action: str = Form(...)):
    global game_state
    
    # Fast-path for battle math
    if action in ["Attack", "Skill"] and game_state["current_enemy"]:
        game_state["current_enemy"]["hp"] -= 40
        if game_state["current_enemy"]["hp"] <= 0:
            game_state["progress"] += 20
            game_state["current_enemy"] = None
            game_state["log"] = "Target defeated! Moving to the next sector."
            return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

    # AI Narrative and Sprite Generation
    prompt = f"RPG Mode. Action: {action}. Progress: {game_state['progress']}%. Output ONLY JSON: {{'story': '...', 'bg': 'env description', 'enemy': {{'name': '...', 'hp': 100, 'sprite': 'pixel art [type] monster'}}}}"
    
    try:
        response = await model.generate_content_async(prompt)
        # Robust parsing to avoid 500 errors
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        game_state["log"] = data["story"]
        game_state["bg_style"] = data["bg"]
        game_state["current_enemy"] = data["enemy"]
    except Exception as e:
        game_state["log"] = "The tall grass rustles..."

    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})
