import os
import json
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Use your universal key from Koyeb
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
# Using 2.5-flash as requested for maximum speed
model = genai.GenerativeModel('gemini-2.5-flash')

# Global state to keep track of the adventure
game_state = {
    "hp": 100,
    "progress": 0,
    "log": "Use the arrow keys to explore the forest!",
    "current_enemy": None
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.post("/action")
async def take_action(request: Request, action: str = Form(...)):
    global game_state
    
    # Quick math for battles so the UI feels responsive
    if action in ["Attack", "Skill"]:
        game_state["progress"] += 20
        game_state["current_enemy"] = None
        game_state["log"] = "Victory! The enemy vanished. Keep exploring!"
        return game_state

    # AI narrative generation for new encounters
    prompt = f"""
    Acting as a Pokemon Game Master. Thomas Jr. is exploring. 
    Mission Progress: {game_state['progress']}%
    Action: {action}
    
    Output ONLY valid JSON:
    {{
        "text": "A short, exciting story beat!",
        "enemy_name": "Monster Name",
        "sprite_prompt": "pixel art monster, colorful, white background"
    }}
    """
    
    try:
        response = await model.generate_content_async(prompt)
        # Cleaning the AI response to prevent JSON errors
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
        
        game_state["log"] = data["text"]
        game_state["current_enemy"] = {
            "name": data["enemy_name"],
            "sprite": data["sprite_prompt"],
            "hp": 100
        }
    except Exception as e:
        print(f"AI Error: {e}")
        game_state["log"] = "You hear a rustle in the tall grass..."
        
    return game_state
