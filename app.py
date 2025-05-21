from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

import sqlite3
from datetime import datetime
import re
import matplotlib.pyplot as plt
import io
import os

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

def init_db():
    conn = sqlite3.connect("records.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            note TEXT,
            amount INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY,
            amount INTEGER
        )
    ''')
    conn.commit()
    conn.close()

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
    detected_func = detect_function(text)

    if detected_func == "查詢":
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        c.execute("SELECT id, date, category, note, amount FROM records ORDER BY id DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()

        if not rows:
            reply = "📭 沒有任何記錄喔！"
        else:
            reply = "📋 最近 5 筆記錄：\n"
            for row in rows:
                reply += f"ID:{row[0]}｜{row[1]}｜{row[3]}｜{row[4]}元｜{row[2]}\n"

    elif detected_func == "刪除" and text.startswith("刪除"):
        try:
            target_id = int(text.split()[1])
            conn = sqlite3.connect("records.db")
            c = conn.cursor()
            c.execute("SELECT * FROM records WHERE id=?", (target_id,))
            record = c.fetchone()
            if record:
                c.execute("DELETE FROM records WHERE id=?", (target_id,))
                conn.commit()
                reply = f"🗑️ 已刪除：ID:{record[0]}｜{record[1]}｜{record[3]}｜{record[4]}元｜{record[2]}"
            else:
                reply = f"❌ 找不到 ID 為 {target_id} 的紀錄喔～"
            conn.close()
        except (IndexError, ValueError):
            reply = "⚠️ 指令錯誤，請輸入：刪除 [ID]，例如：刪除 3"

    elif text.startswith("查詢 "):
        category = text.split()[1]
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        c.execute("SELECT id, date, category, note, amount FROM records WHERE category=? ORDER BY id DESC LIMIT 5", (category,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            reply = f"📭 沒有找到分類【{category}】的紀錄喔！"
        else:
            reply = f"📋 最近的【{category}】紀錄：\n"
            for row in rows:
                reply += f"ID:{row[0]}｜{row[1]}｜{row[3]}｜{row[4]}元｜{row[2]}\n"

    elif detected_func == "統計":
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        c.execute("SELECT category, SUM(amount) FROM records GROUP BY category")
        rows = c.fetchall()
        conn.close()
        if not rows:
            reply = "📭 沒有任何記錄可以統計喔～"
        else:
            reply = "📊 各分類總花費：\n"
            for row in rows:
                reply += f"{row[0]}：{row[1]} 元\n"

    elif detected_func == "查詢日期" and text.startswith("查詢日期"):
        try:
            parts = text.split()
            start_date = parts[1]
            end_date = parts[2]
            conn = sqlite3.connect("records.db")
            c = conn.cursor()
            c.execute("SELECT id, date, category, note, amount FROM records WHERE date BETWEEN ? AND ? ORDER BY date ASC", (start_date, end_date))
            rows = c.fetchall()
            conn.close()
            if not rows:
                reply = f"📭 {start_date} 到 {end_date} 之間沒有記錄喔！"
            else:
                reply = f"📅 {start_date} ～ {end_date} 的紀錄：\n"
                for row in rows:
                    reply += f"ID:{row[0]}｜{row[1]}｜{row[3]}｜{row[4]}元｜{row[2]}\n"
        except:
            reply = "⚠️ 格式錯誤，請輸入：查詢日期 [起日] [迄日]，例如：查詢日期 2025-04-01 2025-04-20"

    elif detected_func == "圖表":
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        c.execute("SELECT category, SUM(amount) FROM records WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now') GROUP BY category")
        data = c.fetchall()
        conn.close()
        if not data:
            reply = "📭 本月還沒有任何記錄喔～"
        else:
            labels = [row[0] for row in data]
            amounts = [row[1] for row in data]
            plt.figure(figsize=(6, 6))
            plt.pie(amounts, labels=labels, autopct='%1.1f%%')
            plt.title("本月支出分類比例")
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode()
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
            conn = sqlite3.connect("records.db")
            c = conn.cursor()
            c.execute("DELETE FROM budget")
            c.execute("INSERT INTO budget (id, amount) VALUES (1, ?)", (budget,))
            conn.commit()
            conn.close()
            reply = f"💸 每月預算已設定為 {budget} 元"
        except:
            reply = "⚠️ 請用正確格式：設定預算 [金額]，例如：設定預算 5000"

    elif detected_func == "本月剩餘":
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        c.execute("SELECT amount FROM budget WHERE id = 1")
        row = c.fetchone()
        if row:
            budget = row[0]
            c.execute("SELECT SUM(amount) FROM records WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
            spent = c.fetchone()[0] or 0
            remaining = budget - spent
            reply = f"📅 本月預算：{budget} 元\n🧾 已花費：{spent} 元\n💰 剩餘：{remaining} 元"
        else:
            reply = "⚠️ 尚未設定預算，請先輸入：設定預算 [金額]"
        conn.close()

    else:
        note, amount = extract_note_and_amount(text)
        if note and amount:
            date = datetime.now().strftime("%Y-%m-%d")
            category = classify(text)
            user_id = event.source.user_id
            conn = sqlite3.connect("records.db")
            c = conn.cursor()
            c.execute("INSERT INTO records (date, category, note, amount) VALUES (?, ?, ?, ?)",
                      (date, category, note, amount))
            conn.commit()
            conn.close()
            reply = f"✅ 已記錄：{note}｜{amount}元｜分類：{category}"
        else:
            reply = "❌ 抱歉，我沒看懂金額或類別，你可以這樣說：\n『吃壽司180』或『剛搭捷運20元』"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
