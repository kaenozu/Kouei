import random

class CommentaryGenerator:
    def __init__(self):
        self.templates = {
            "intro": [
                "このレースの注目ポイントは{focus_boat}号艇です。",
                "波乱の予感がする一戦。中心となるのは{focus_boat}号艇でしょう。",
                "堅実な展開が予想されます。本命は{focus_boat}号艇。"
            ],
            "motor_good": "モーター{motor_no}号機は2連対率{motor_val}%と非常に強力で、展示タイムも{exhibit}と好調。",
            "motor_bad": "モーター{motor_no}号機は数字が低く、足回りに不安が残ります。",
            "racer_good": "{racer_name}選手は当地勝率{win_rate}と相性が良く、期待できます。",
            "wind_head": "向かい風{wind}mの影響で、ダッシュ勢の出番が増えるかもしれません。",
            "conclusion": [
                "以上の要素から、{prediction}の展開を予想します。",
                "よって、{prediction}で勝負するのが妙味ありです。",
                "自信を持って{prediction}を推奨します。"
            ]
        }

    def generate(self, race_row, top_prediction_boat, feature_data=None):
        """
        Generates a commentary based on race features.
        race_row: DataFrame row for the focus boat (usually 1st place pred)
        """
        # Data Extraction
        boat = top_prediction_boat
        racer = race_row.get('racer_name', '選手')
        motor_no = race_row.get('motor_no', '??')
        motor_2ren = race_row.get('motor_2ren', 0)
        exhibit = race_row.get('exhibition_time', 6.80)
        win_rate = race_row.get('racer_win_rate', 0)
        wind = race_row.get('wind_speed', 0)
        
        # Build Text
        parts = []
        
        # 1. Intro
        parts.append(random.choice(self.templates["intro"]).format(focus_boat=boat))
        
        # 2. Motor Analysis
        if motor_2ren >= 40:
            parts.append(self.templates["motor_good"].format(motor_no=motor_no, motor_val=motor_2ren, exhibit=exhibit))
        elif motor_2ren <= 30:
            parts.append(self.templates["motor_bad"].format(motor_no=motor_no))
        
        # 3. Racer Analysis
        if win_rate >= 6.5:
             parts.append(self.templates["racer_good"].format(racer_name=racer, win_rate=win_rate))
             
        # 4. Wind
        if wind >= 4:
            parts.append(self.templates["wind_head"].format(wind=wind))
            
        # 5. Conclusion (Mock Prediction Text)
        pred_text = f"{boat}号艇の逃げ" if boat == 1 else f"{boat}号艇のまくり差し"
        parts.append(random.choice(self.templates["conclusion"]).format(prediction=pred_text))
        
        return "".join(parts)

    def generate_llm(self, race_data_dict, api_key):
        """
        Placeholder for Real GenAI (Gemini/OpenAI)
        """
        prompt = f"""
        あなたは競艇のプロ予想家です。以下のデータをもとに、展開予想を書いてください。
        データ: {race_data_dict}
        """
        # Call API here
        return "AIコメント生成機能はAPIキー設定後に有効になります。"
