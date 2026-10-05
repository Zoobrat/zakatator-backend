from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from services.sheets_service import get_wishlist, spin_gift, reserve_gifts, get_goals, contribute_to_goal
import os
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику (фронтенд)
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
def read_root():
    return FileResponse("../frontend/index.html")

@app.post("/api/spin")
def spin(budget: int, category: str = None, limit: int = 5, previous_ids: str = None):
    if budget <= 0:
        raise HTTPException(status_code=400, detail="Бюджет должен быть больше 0")
    
    previous_ids_list = previous_ids.split(',') if previous_ids else None
    
    gifts = spin_gift(budget=budget, category=category, limit=limit, previous_ids=previous_ids_list)
    
    if not gifts:
        raise HTTPException(status_code=404, detail="Подарки не найдены")
    
    return {"gifts": gifts}

@app.get("/api/wishlist")
def wishlist():
    return get_wishlist()

@app.post("/api/reserve")
def reserve(item_ids: List[str], total_rub: int):
    if not item_ids or total_rub <= 0:
        raise HTTPException(status_code=400, detail="Некорректные данные")
    
    reservation = reserve_gifts(item_ids, total_rub)
    return {"reservation": reservation}

@app.get("/api/goals")
def goals():
    return get_goals()

@app.post("/api/contribute")
def contribute(goal_id: str, amount_rub: int, contributor_name: str = None):
    if amount_rub <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть больше 0")
    
    result = contribute_to_goal(goal_id, amount_rub, contributor_name)
    return {"contribution": result}

if __name__ == "__main__":
    import uvicorn
    print("Starting ZAKATATOR.EXE...", flush=True)
    try:
        uvicorn.run(app, host="0.0.0.0", port=5000, reload=False)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        sys.exit(1)