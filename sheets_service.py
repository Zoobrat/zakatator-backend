from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import random
from datetime import datetime
import uuid

KEY_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'service-account-key.json')

def get_sheets_client():
    creds = service_account.Credentials.from_service_account_file(
        KEY_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

def get_wishlist() -> List[Dict[str, Any]]:
    client = get_sheets_client()
    sheet = client.spreadsheets()
    
    SPREADSHEET_ID = "1BJq5S49Bi_Qqmu2WPkkFUyd8iwaCVl9lKpgzbBWGU7c"
    RANGE = "Wishlist!A2:K"
    
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
    rows = result.get("values", [])
    
    wishlist = []
    for row in rows:
        wishlist.append({
            "id": row[0] if len(row) > 0 else "",
            "name": row[1] if len(row) > 1 else "",
            "category": row[2] if len(row) > 2 else "",
            "price_rub": row[3] if len(row) > 3 else "0",
            "url": row[4] if len(row) > 4 else "",
            "priority": row[5] if len(row) > 5 else "1",
            "status": row[6] if len(row) > 6 else "available",
            "note": row[7] if len(row) > 7 else "",
            "reserved_at": row[8] if len(row) > 8 else "",
            "reservation_id": row[9] if len(row) > 9 else "",
            "image_url": row[10] if len(row) > 10 else "",
        })
    
    return wishlist

def spin_gift(budget: int, category: str = None, limit: int = 5, previous_ids: List[str] = None):
    wishlist = get_wishlist()
    
    if category:
        wishlist = [item for item in wishlist if item.get("category", "").lower() == category.lower()]
    
    wishlist = [item for item in wishlist if item.get("status") == "available"]
    
    if previous_ids:
        wishlist = [item for item in wishlist if item.get("id") not in previous_ids]
    
    if not wishlist:
        return []
    
    wishlist = [item for item in wishlist if int(item.get("price_rub", 0)) <= budget]
    
    if not wishlist:
        return []
    
    wishlist.sort(key=lambda x: -int(x.get("price_rub", 0)))
    
    min_single_price = int(budget * 0.8)
    single_gifts = [item for item in wishlist if int(item.get("price_rub", 0)) >= min_single_price]
    
    if single_gifts:
        selected = random.choice(single_gifts)
        return [selected]
    
    random.shuffle(wishlist)
    
    for item in wishlist:
        priority = int(item.get("priority", 1))
        random_boost = random.uniform(0, 2)
        item["_score"] = priority + random_boost
    
    wishlist.sort(key=lambda x: -x.get("_score", 0))
    
    result = []
    total = 0
    
    for item in wishlist:
        price = int(item.get("price_rub", 0))
        if total + price <= budget and len(result) < limit:
            result.append(item)
            total += price
    
    if not result:
        num_items = random.randint(1, min(3, len(wishlist)))
        result = random.sample(wishlist, num_items)
    
    for item in result:
        if "_score" in item:
            del item["_score"]
    
    return result

def reserve_gifts(item_ids: List[str], total_rub: int):
    client = get_sheets_client()
    sheet = client.spreadsheets()
    
    SPREADSHEET_ID = "1BJq5S49Bi_Qqmu2WPkkFUyd8iwaCVl9lKpgzbBWGU7c"
    reservation_id = str(uuid.uuid4())
    reserved_at = datetime.now().isoformat()
    
    range_all = "Wishlist!A2:K"
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_all).execute()
    all_rows = result.get("values", [])
    
    rows_to_update = []
    for row_idx, row in enumerate(all_rows, start=2):
        if len(row) > 0 and row[0] in item_ids:
            rows_to_update.append(row_idx)
    
    for row_idx in rows_to_update:
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Wishlist!G{row_idx}",
            valueInputOption="RAW",
            body={"values": [["reserved"]]}
        ).execute()
        
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Wishlist!I{row_idx}",
            valueInputOption="RAW",
            body={"values": [[reserved_at]]}
        ).execute()
        
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"Wishlist!J{row_idx}",
            valueInputOption="RAW",
            body={"values": [[reservation_id]]}
        ).execute()
    
    reservations_range = "Reservations!A:E"
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=reservations_range,
        valueInputOption="RAW",
        body={
            "values": [[
                reservation_id,
                reserved_at,
                ",".join(item_ids),
                total_rub,
                "reserved"
            ]]
        }
    ).execute()
    
    return {
        "reservation_id": reservation_id,
        "item_ids": ",".join(item_ids),
        "total_rub": total_rub,
        "status": "reserved"
    }

def get_goals() -> List[Dict[str, Any]]:
    client = get_sheets_client()
    sheet = client.spreadsheets()
    
    SPREADSHEET_ID = "1BJq5S49Bi_Qqmu2WPkkFUyd8iwaCVl9lKpgzbBWGU7c"
    RANGE = "FundGoals!A2:K"
    
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
    rows = result.get("values", [])
    
    goals = []
    for row in rows:
        target_rub = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
        pledged_rub = int(row[4]) if len(row) > 4 and row[4].isdigit() else 0
        progress = (pledged_rub / target_rub * 100) if target_rub > 0 else 0
        
        goals.append({
            "id": row[0] if len(row) > 0 else "",
            "title": row[1] if len(row) > 1 else "",
            "category": row[2] if len(row) > 2 else "",
            "target_rub": target_rub,
            "pledged_rub": pledged_rub,
            "progress": round(progress, 1),
            "url": row[5] if len(row) > 5 else "",
            "image_url": row[6] if len(row) > 6 else "",
            "priority": row[7] if len(row) > 7 else "1",
            "status": row[8] if len(row) > 8 else "open",
            "note": row[9] if len(row) > 9 else "",
        })
    
    return goals

def contribute_to_goal(goal_id: str, amount_rub: int, contributor_name: str = None):
    client = get_sheets_client()
    sheet = client.spreadsheets()
    
    SPREADSHEET_ID = "1BJq5S49Bi_Qqmu2WPkkFUyd8iwaCVl9lKpgzbBWGU7c"
    contribution_id = str(uuid.uuid4())
    contributed_at = datetime.now().isoformat()
    
    # Находим цель в таблице
    range_all = "FundGoals!A2:K"
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_all).execute()
    all_rows = result.get("values", [])
    
    goal_row_idx = None
    for row_idx, row in enumerate(all_rows, start=2):
        if len(row) > 0 and row[0] == goal_id:
            goal_row_idx = row_idx
            break
    
    if not goal_row_idx:
        raise Exception("Цель не найдена")
    
    # Обновляем pledged_rub (колонка E)
    current_pledged = int(all_rows[goal_row_idx - 2][4]) if len(all_rows[goal_row_idx - 2]) > 4 and all_rows[goal_row_idx - 2][4].isdigit() else 0
    new_pledged = current_pledged + amount_rub
    
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"FundGoals!E{goal_row_idx}",
        valueInputOption="RAW",
        body={"values": [[str(new_pledged)]]}
    ).execute()
    
    # Добавляем запись в Contributions
    contributions_range = "Contributions!A:E"
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=contributions_range,
        valueInputOption="RAW",
        body={
            "values": [[
                contribution_id,
                goal_id,
                contributed_at,
                amount_rub,
                contributor_name or "Аноним"
            ]]
        }
    ).execute()
    
    return {
        "contribution_id": contribution_id,
        "goal_id": goal_id,
        "amount_rub": amount_rub,
        "contributor_name": contributor_name or "Аноним",
        "contributed_at": contributed_at
    }