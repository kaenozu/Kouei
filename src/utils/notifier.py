import requests
import json

def send_discord_notification(webhook_url, message):
    """
    Sends a message to a Discord channel via webhook.
    """
    if not webhook_url or webhook_url == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("Discord Webhook URL not configured. Skipping notification.")
        return False
        
    payload = {
        "content": message
    }
    
    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Discord notification: {e}")
        return False

def format_race_message(date, stadium, race_no, predictions):
    """
    Formats a race prediction into a readable Discord message.
    """
    # predictions is expected to be a list of dicts or a DataFrame
    # Let's assume it's the top predictions from get_prediction
    
    msg = f"🚀 **高確率レース予報** 🚀\n"
    msg += f"📅 日付: {date}\n"
    msg += f"📍 会場: {stadium} {race_no}R\n"
    msg += f"-----------------\n"
    
    for p in predictions:
        boat = p.get('boat_no')
        name = p.get('racer_name', '')
        prob = p.get('prob_win', 0)
        msg += f"🚤 {boat}号艇: {name} (的中確率: {prob*100:.1f}%)\n"
    
    msg += f"-----------------\n"
    msg += f"🔗 アプリで詳細を確認: http://localhost:5173"
    
    return msg
