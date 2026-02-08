import os, json, urllib.parse, google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

game_state = {"mode": "EXPLORE", "log": "Walk to find a monster!", "player_hp": 100, "enemy": None}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": game_state})

@app.post("/action")
async def take_action(request: Request, action: str = Form(...)):
    global game_state
    if game_state["mode"] == "BATTLE" and action != "Explore":
        prompt = f"Outcome of {action} vs {game_state['enemy']['name']}. Enemy HP: {game_state['enemy']['hp']}. JSON: {{'dmg': int, 'p_dmg': int, 'text': 'str'}}"
        try:
            res = await model.generate_content_async(prompt)
            data = json.loads(res.text.replace('```json', '').replace('```', '').strip())
            game_state["enemy"]["hp"] -= data['dmg']
            game_state["player_hp"] -= data['p_dmg']
            game_state["log"] = data['text']
            if game_state["enemy"]["hp"] <= 0:
                game_state["mode"], game_state["enemy"] = "EXPLORE", None
                game_state["log"] = "Victory!"
        except: game_state["log"] = "The battle rages!"
        return game_state

    prompt = "New Pokemon. JSON: {'name': 'str', 'hp': 100, 'moves': ['m1', 'm2'], 'sprite': '3-word description'}"
    try:
        res = await model.generate_content_async(prompt)
        data = json.loads(res.text.replace('```json', '').replace('```', '').strip())
        game_state.update({"mode": "BATTLE", "enemy": data, "log": f"A wild {data['name']} appeared!"})
    except: game_state["log"] = "Something is hiding..."
    return game_state
