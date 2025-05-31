from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

from supabase import create_client, Client

from datetime import datetime
import re
import matplotlib.pyplot as plt
import io
import os
import base64
import matplotlib

SUPABASE_URL = "https://kounvedczvpdiajozfkq.supabase.co"  # ✅ 你的專案 URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvdW52ZWRjenZwZGlham96ZmtxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MDQ1NzMsImV4cCI6MjA2MzM4MDU3M30.yk7NkHy1xc5JNKLIHMLCheLKBf_-AwAtQpN4MZyyUDk"                               # ✅ 請填入你自己的 key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

# LINE 開發者憑證
LINE_CHANNEL_ACCESS_TOKEN = '2tK5quYJYwlR/2uN7CogozuHjD9loG2PefW2CY6lMD03rwrsDuu5h5lPEnhG4wsvCEFZdwv3CcnHdX1mwTOkj8G5MN74E22LhPRsim9ZRuXAJ2/35UGcbdZBlhVDgNx4btN+CnF1CM7wFAbInSO/IwdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'ca7cc07caea768880f35df61d64ac80d'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 分類對照表
category_keywords = {
  "飲食": [
        "早餐", "午餐", "晚餐", "宵夜", "早午餐", "便當", "自助餐", "簡餐", "套餐", "快餐",
        "滷肉飯", "雞排", "鐵板燒", "壽司", "拉麵", "牛排", "義大利麵", "火鍋", "燒烤", "炸雞",
        "韓式料理", "泰式料理", "越南河粉", "咖哩飯", "丼飯", "炒飯", "炒麵", "燴飯", "蚵仔煎", "鹹酥雞",
        "麥當勞", "肯德基", "摩斯", "漢堡王", "必勝客", "達美樂", "頂呱呱",
        "肉圓", "米糕", "粽子", "燒賣", "鍋貼", "水餃", "湯包", "滷味", "油飯", "燒餅",
        "甜點", "蛋糕", "布丁", "奶酪", "豆花", "仙草", "芋圓", "麻糬", "蛋塔", "車輪餅",
        "糖葫蘆", "鬆餅", "銅鑼燒", "蛋糕卷", "可麗餅", "冰淇淋", "霜淇淋", "泡芙", "甜湯", "紅豆湯",
        "飲料", "珍奶", "奶茶", "紅茶", "綠茶", "烏龍茶", "水果茶", "冬瓜茶", "可樂", "汽水",
        "果汁", "柳橙汁", "檸檬汁", "冰沙", "咖啡", "拿鐵", "美式", "卡布奇諾", "熱可可", "豆漿",
        "超商便當", "御飯糰", "茶葉蛋", "涼麵", "三明治", "關東煮", "即食麵", "泡麵", "麵包", "零食",
        "吃飯", "吃東西", "吃飽", "吃宵夜", "點餐", "外送", "Uber Eats", "Foodpanda", "叫外賣", "外帶"
    ],
    "交通": [
        "捷運", "公車", "火車", "高鐵", "客運", "機車", "汽車", "騎車", "腳踏車", "停車費",
        "加油", "油錢", "保養", "機油", "輪胎", "洗車", "過路費", "車資", "搭車", "租車",
        "計程車", "Uber", "Lyft", "搭機", "機票", "車票", "月票", "通勤", "上下班", "交通卡",
        "悠遊卡", "icash", "加值", "儲值", "車站", "車廂", "出站", "入站", "等車", "誤點",
        "交通罰單", "交通事故", "地鐵", "接駁車", "共乘", "共享機車", "共享單車", "導航", "開車", "載人"
    ],
    "娛樂": [
        "電影", "戲院", "影城", "爆米花", "遊戲", "手遊", "線上遊戲", "Steam", "Switch", "PS5",
        "打電動", "電競", "實況", "直播", "YouTube", "Netflix", "Disney+", "串流", "追劇", "漫畫",
        "漫畫店", "租書", "小說", "桌遊", "密室逃脫", "唱歌", "KTV", "音樂", "演唱會", "展覽",
        "表演", "舞台劇", "劇場", "表演票", "節目", "電視", "偶像", "明星", "打牌", "麻將",
        "交友App", "社交平台", "Cosplay", "角色扮演", "攝影", "拍照", "運動賽事", "健身", "跳舞", "跳繩"
    ],
    "購物": [
        "購物", "網購", "蝦皮", "momo", "PChome", "淘寶", "Amazon", "蝦皮店到店", "百貨", "超商",
        "超市", "全聯", "家樂福", "大潤發", "小北百貨", "生活用品", "文具", "日用品", "保養品", "化妝品",
        "衣服", "褲子", "鞋子", "外套", "包包", "飾品", "手錶", "耳環", "項鍊", "帽子",
        "手機殼", "滑鼠", "鍵盤", "電腦", "耳機", "相機", "3C產品", "家電", "飲水機", "電風扇",
        "書籍", "筆記本", "原子筆", "背包", "衛生紙", "牙刷", "牙膏", "清潔劑", "毛巾", "化妝棉"
    ],
    "其他": []
}


def detect_function(text):
    function_keywords = {
        "查詢": ["查詢", "我要查", "看看紀錄", "找一下帳", "最近的帳", "記帳紀錄", "紀錄"],
        "刪除": ["刪除", "移除", "取消紀錄", "刪掉"],
        "設定預算": ["設定預算", "這個月預算", "預算提醒"],
        "統計": ["統計", "分類總額", "花費統計", "統計一下"],
        "查詢日期": ["查詢日期", "日期範圍", "時間區間", "日期查詢"],
        "圖表": ["圖表", "支出圖", "餅圖", "看一下圖表"],
        "本月剩餘": ["剩餘預算", "還剩多少", "預算剩多少","本月剩餘"]
    }

    for func, keywords in function_keywords.items():
        for kw in keywords:
            if kw in text:
                return func
    return None


def classify(text):
    for cat, keywords in category_keywords.items():
        if any(k in text for k in keywords):
            return cat
    return "其他"

def extract_note_and_amount(text):
    match = re.search(r"([^\d\s]{1,10})?[^\d]*(\d{1,5})", text)
    if match:
        note = match.group(1) if match.group(1) else "未分類"
        amount = int(match.group(2))
        return note, amount
    return None, None

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    detected_func = detect_function(text)

    if detected_func == "查詢":
        res = supabase.table("records").select("id, date, category, note, amount").eq("user_id", user_id).order("id", desc=True).limit(5).execute()
        rows = res.data
        if not rows:
            reply = "📭 沒有任何記錄喔！"
        else:
            reply = "📋 最近 5 筆記錄：\n"
            for row in rows:
                reply += f"ID:{row['id']}｜{row['date']}｜{row['note']}｜{row['amount']}元｜{row['category']}\n"

    elif detected_func == "刪除" and text.startswith("刪除"):
        try:
            target_id = int(text.split()[1])
            res = supabase.table("records").select("*").eq("id", target_id).eq("user_id", user_id).execute()
            if res.data:
                supabase.table("records").delete().eq("id", target_id).execute()
                row = res.data[0]
                reply = f"🗑️ 已刪除：ID:{row['id']}｜{row['date']}｜{row['note']}｜{row['amount']}元｜{row['category']}"
            else:
                reply = f"❌ 找不到 ID 為 {target_id} 的紀錄喔～"
        except:
            reply = "⚠️ 指令錯誤，請輸入：刪除 [ID]，例如：刪除 3"

    elif text.startswith("查詢 "):
        category = text.split()[1]
        res = supabase.table("records").select("id, date, category, note, amount").eq("category", category).eq("user_id", user_id).order("id", desc=True).limit(5).execute()
        rows = res.data
        if not rows:
            reply = f"📭 沒有找到分類【{category}】的紀錄喔！"
        else:
            reply = f"📋 最近的【{category}】紀錄：\n"
            for row in rows:
                reply += f"ID:{row['id']}｜{row['date']}｜{row['note']}｜{row['amount']}元｜{row['category']}\n"

    elif detected_func == "統計":
        res = supabase.table("records").select("category, amount").eq("user_id", user_id).execute()
        rows = res.data
        if not rows:
            reply = "📭 沒有任何記錄可以統計喔～"
        else:
            summary = {}
            for row in rows:
                summary[row['category']] = summary.get(row['category'], 0) + row['amount']
            reply = "📊 各分類總花費：\n"
            for cat, total in summary.items():
                reply += f"{cat}：{total} 元\n"

    elif detected_func == "查詢日期" and text.startswith("查詢日期"):
        try:
            parts = text.split()
            start_date, end_date = parts[1], parts[2]
            res = supabase.table("records").select("id, date, category, note, amount").eq("user_id", user_id).gte("date", start_date).lte("date", end_date).order("date").execute()
            rows = res.data
            if not rows:
                reply = f"📭 {start_date} 到 {end_date} 之間沒有記錄喔！"
            else:
                reply = f"📅 {start_date} ～ {end_date} 的紀錄：\n"
                for row in rows:
                    reply += f"ID:{row['id']}｜{row['date']}｜{row['note']}｜{row['amount']}元｜{row['category']}\n"
        except:
            reply = "⚠️ 格式錯誤，請輸入：查詢日期 [起日] [迄日]，例如：查詢日期 2025-04-01 2025-04-20"

    elif detected_func == "圖表":
        now_month = datetime.now().strftime("%Y-%m")
        res = supabase.table("records").select("category, amount").eq("user_id", user_id).like("date", f"{now_month}%").execute()
        rows = res.data
        if not rows:
            reply = "📭 本月還沒有任何記錄喔～"
        else:
            summary = {}
            for row in rows:
                summary[row['category']] = summary.get(row['category'], 0) + row['amount']
            labels = list(summary.keys())
            amounts = list(summary.values())
            from matplotlib import font_manager
            font_path = "NotoSansTC-VariableFont_wght.ttf"
            font_prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
            plt.figure(figsize=(6, 6))
            def make_autopct(values):
                def my_autopct(pct):
                    total = sum(values)
                    val = int(round(pct * total / 100.0))
                    return f'{pct:.1f}%\n({val}元)'
                return my_autopct
            plt.pie(amounts, labels=labels, autopct=make_autopct(amounts), textprops={'fontproperties': font_prop})
            plt.title("本月支出分類比例", fontproperties=font_prop)
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            if not os.path.exists("static"):
                os.makedirs("static")
            with open("static/chart.png", "wb") as f:
                f.write(buf.read())
            image_url = "https://linebot-uj1t.onrender.com/static/chart.png"
            buf.close()
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            )
            return

    elif detected_func == "設定預算":
        try:
            budget = int(text.split()[1])
            supabase.table("budget").upsert({"user_id": user_id, "amount": budget}).execute()
            reply = f"💸 每月預算已設定為 {budget} 元"
        except:
            reply = "⚠️ 請用正確格式：設定預算 [金額]，例如：設定預算 5000"

    elif detected_func == "本月剩餘":
        budget_res = supabase.table("budget").select("amount").eq("user_id", user_id).execute()
        if not budget_res.data:
            reply = "⚠️ 尚未設定預算，請先輸入：設定預算 [金額]"
        else:
            budget = budget_res.data[0]['amount']
            spent_res = supabase.table("records").select("amount").eq("user_id", user_id).like("date", f"{datetime.now().strftime('%Y-%m')}%").execute()
            spent = sum([r['amount'] for r in spent_res.data])
            remaining = budget - spent
            reply = f"📅 本月預算：{budget} 元\n🧾 已花費：{spent} 元\n💰 剩餘：{remaining} 元"

    else:
        note, amount = extract_note_and_amount(text)
        if note and amount:
            date = datetime.now().strftime("%Y-%m-%d")
            category = classify(text)
            supabase.table("records").insert({
                "date": date,
                "category": category,
                "note": note,
                "amount": amount,
                "user_id": user_id
            }).execute()
            reply = f"✅ 已記錄：{note}｜{amount}元｜分類：{category}"
        else:
            reply = "❌ 抱歉，我沒看懂金額或類別，你可以這樣說：\n『吃壽司180』或『剛搭捷運20元』"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

#import speech_recognition as sr
#from pydub import AudioSegment
#import os

#def handle_voice(update: Update, context: CallbackContext):
    #file = update.message.voice.get_file()
    #file_path = "voice.ogg"
    #wav_path = "voice.wav"

    # 下載語音檔
    #file.download(file_path)

    # 轉檔 ogg → wav
    #audio = AudioSegment.from_ogg(file_path)
    #audio.export(wav_path, format="wav")

    # 使用 SpeechRecognition 辨識
    #recognizer = sr.Recognizer()
    #with sr.AudioFile(wav_path) as source:
        #audio_data = recognizer.record(source)

    #try:
        #text = recognizer.recognize_google(audio_data, language="zh-TW")
        #update.message.reply_text(f"🗣️ 你說的是：「{text}」")

        # 把語音轉文字後，交給原本的 handle_message 處理
        #message = type("Message", (), {"text": text, "chat": update.message.chat, "reply_text": update.message.reply_text})
        #update_voice = type("Update", (), {"message": message})
        #handle_message(update_voice, context)

    #except sr.UnknownValueError:
        #update.message.reply_text("⚠️ 無法辨識語音，請再試一次。")
    #except Exception as e:
        #update.message.reply_text(f"⚠️ 發生錯誤：{e}")

#@app.route("/reminder", methods=["GET", "POST"])
#def reminder():
    #user_id = "a22556"  # 換成你自己的
    #line_bot_api.push_message(
        #user_id,
        #TextSendMessage(text="📣 今天記帳了嗎？記得花費要紀錄喔！")
    )
    return "OK"


    # 清理暫存檔案
    os.remove(file_path)
    os.remove(wav_path)
