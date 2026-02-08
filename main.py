import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# This covers both common variable names used by different SDK versions
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No API Key found! Check your Koyeb Environment Variables.")

genai.configure(api_key=api_key)
# Stick with 'gemini-2.5-flash' for the best speed/logic balance
model = genai.GenerativeModel('gemini-2.5-flash')

game_state = {
    "player": {"hp": 100, "level": 1},
    "progress": 0,
    "current_enemy": None,
    "log": "A new journey begins in high definition!",
    "bg_image": "vibrant lush pokemon forest battle background"
}

@app.post("/action")
async def take_action(request: Request, action: str = Form(...)):
    global game_state
    
    # Fast Battle Logic
    if action in ["Attack", "Skill"] and game_state["current_enemy"]:
        game_state["current_enemy"]["hp"] -= 40
        if game_state["current_enemy"]["hp"] <= 0:
            game_state["progress"] += 20
            game_state["current_enemy"] = None
            game_state["log"] = "Target defeated! Searching for the next challenge..."
            return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

    # "Director" Prompt for High-End Visuals
    prompt = f"""
    Acting as an HD Pokemon Director. 
    Progress: {game_state['progress']}%
    Action: {action}
    
    Output ONLY JSON:
    {{
        "description": "Dramatic battle text",
        "bg_prompt": "High quality anime style battle background, {action} theme, vibrant colors",
        "enemy": {{
            "name": "Epic Monster Name",
            "hp": 100,
            "sprite_prompt": "Full color high-detail pokemon sprite, {action} element, white background"
        }},
        "options": ["Attack", "Skill"]
    }}
    """
    
    response = await model.generate_content_async(prompt)
    data = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
    
    game_state["current_enemy"] = data["enemy"]
    game_state["log"] = data["description"]
    game_state["bg_image"] = data["bg_prompt"]

    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})
