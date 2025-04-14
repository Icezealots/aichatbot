from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URITemplateAction, StickerSendMessage, ImageSendMessage,CarouselTemplate, CarouselColumn
)
import google.generativeai as genai
import os

# 初始化 Flask 應用程式
app = Flask(__name__)

# LINE Bot API 和 Webhook Handler 設定
line_bot_api = LineBotApi(os.environ.get('LinebotToken'))
handler = WebhookHandler(os.environ.get('LinebotSecret'))

# Google Generative AI 配置
genai.configure(api_key=os.environ.get('geminiapikey'))

# LIFF ID（你的特定 URL）
liffid = '2006620225-p5Ae3ykb'

# 溫柔問答題目
questions = [
    "🌿 1. 壓力與焦慮管理\n「嗨，歡迎你來到這裡。感覺你可能有點累了，或者心裡有點壓力，對嗎？\n想跟我聊聊最近讓你覺得焦慮或壓力大的事情嗎？」",
    
    "🌸 2. 自我探索與內在成長\n「有時候，我們會突然停下腳步，問自己：『我到底是誰？我真正想要的是什麼？』\n你最近也有這樣的感覺嗎？」",

    "💞 3. 人際關係與情感困擾\n「有些情感放在心裡久了會變得沉重，尤其是在人際關係中。\n你最近在人與人之間的連結上，有什麼讓你感到難過或困擾的嗎？」",

    "🍃 4. 身體健康與能量平衡\n「你的身體最近還好嗎？有時候我們忙著照顧別人，會忘了自己也需要被好好照顧。」",

    "✨ 5. 靈性連結與心靈成長\n「有時候，我們會感覺自己想找回與內在或宇宙的連結。\n你最近是否有這種渴望？想要更靠近那份寧靜與光？」"
]


# 分類關鍵字
category_keywords = {
    "body": [
        "累", "疲倦", "疲憊", "無力", "睡", "睡不好", "睡不著", "失眠",
        "身體", "頭痛", "胃痛", "背痛", "肩膀緊", "心悸", "頭暈", "不舒服", "疼痛",
        "沒精神", "倦怠", "身體沉重", "感冒", "生理痛", "月經不順"
    ],
    "mind": [
        "焦慮", "壓力", "孤單", "低落", "沮喪", "煩惱", "情緒", "緊張", "不安",
        "憂鬱", "難過", "委屈", "崩潰", "不想動", "情緒化", "內耗", "煩躁",
        "失落", "心煩", "恐懼", "沒有動力", "覺得累", "想逃避"
    ],
    "spirit": [
        "意義", "人生", "存在", "靈魂", "心靈", "空虛", "迷惘", "自我", "覺醒",
        "靈性", "宇宙", "高我", "內在聲音", "使命", "方向", "冥想", "連結",
        "能量", "轉化", "療癒", "覺察", "成長", "覺知", "找不到自己"
    ]
}

# 使用者狀態與回答紀錄

user_states = {}      # {user_id: 問題進度}
user_answers = {}     # {user_id: [回答串]}

def classify_user(answers):
    scores = {"body": 0, "mind": 0, "spirit": 0}
    for ans in answers:
        for category, keywords in category_keywords.items():
            if any(kw in ans.lower() for kw in keywords):
                scores[category] += 1
    return max(scores, key=scores.get)

def recommend_forum(category):
    forums = {
        "body": "你可以看看這個身體保健的溫柔角落 🌿 https://a111221038.wixstudio.com/my-site-3/forum/pu-tong-tao-lun?rc=test-site",
        "mind": "這裡有一些心理支持的溫暖資源 🧠 https://a111221038.wixstudio.com/my-site-3/forum/wen-yu-da?rc=test-site",
        "spirit": "想探索心靈與自我，可以看看這個空間 ✨ https://a111221038.wixstudio.com/my-site-3/forum/zhi-xian-yuan-gong?rc=test-site"
    }
    return forums.get(category, "希望這段對話有帶給你一些溫暖 💖")

def basic_emotion_analysis(answer):
    answer = answer.lower()
    if any(keyword in answer for keyword in ['錢', '沒錢', '薪水', '經濟', '月底', '房租', '負擔', '工作薪資']):
        return "金錢壓力"
    elif any(keyword in answer for keyword in ['男友', '女友', '感情', '愛情', '分手', '戀愛', '前任', '伴侶', '失戀', '情人']):
        return "情感困擾"
    elif any(keyword in answer for keyword in ['孤單', '寂寞', '沒人懂', '朋友', '人際', '吵架', '冷戰']):
        return "人際孤獨"
    elif any(keyword in answer for keyword in ['不知道', '還好', '沒有', '普通', '沒什麼', '就這樣']):
        return "低能量"
    elif any(keyword in answer for keyword in ['壓力', '焦慮', '緊張', '疲憊', '擔心', '煩躁', '煩']):
        return "焦慮"
    elif any(keyword in answer for keyword in ['快樂', '開心', '平靜', '放鬆', '自在', '穩定']):
        return "穩定"
    elif any(keyword in answer for keyword in ['生病', '頭痛', '身體不舒服', '感冒', '不想動']):
        return "身體不適"
    elif any(keyword in answer for keyword in ['熬夜', '睡不著', '太晚睡', '沒睡好', '睡很少', '作息亂']):
        return "熬夜疲勞"
    elif any(keyword in answer for keyword in ['沒意義', '空虛', '迷失', '人生', '存在', '想法混亂']):
        return "靈性迷惘"
    else:
        return "未知"


def generate_mid_reply(emotion):
    replies = {
        "金錢壓力": "經濟壓力真的會壓得人喘不過氣…願你在煩惱之中，也能找到一點點喘息的空間 🌿",
        "情感困擾": "感情的世界總是特別深…謝謝你願意說出口，我會一直在 💞",
        "人際孤獨": "人與人的距離有時真的會讓人感到好孤單…但你不是一個人，我在這裡陪你 🍃",
        "低能量": "沒關係的，就算什麼都不想說也沒關係～我會一直在這裡陪你 🌙",
        "焦慮": "感覺你最近真的很辛苦呢…深呼吸一下，我們一步一步慢慢來 🌸",
        "穩定": "聽你這麼說我也覺得好安心～希望這樣的感覺可以一直持續 ✨",
        "身體不適": "身體不舒服的時候，什麼事都變得好困難。要記得好好休息喔 🛌",
        "熬夜疲勞": "最近常熬夜嗎？知道有時就是無法入眠，希望你今晚能早點休息，讓身體好好充電 🌙🛏️",
        "靈性迷惘": "對人生的迷惘是靈魂在對你說話，也許這段路會帶你去某個答案 ✨",
        "未知": "謝謝你願意分享這些…這裡是你可以慢慢說話的空間 🌼"
    }
    return replies.get(emotion, replies["未知"])




@app.route("/callback", methods=['POST'])

def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    mtext = event.message.text
    
    user_id = event.source.user_id
    
    # 處理自定義指令
    if mtext == '平台介紹':
        try:
            message = TextSendMessage(
                text="Soulv \n身心靈界的米其林指南\n全球首個身心靈開箱與評鑑指南\n幫助你找到真正值得信賴的療癒體驗與課程\n不只是要創造一個平台\n而是一場身心靈療癒界的透明化運動。\nSoulv 如何運作？\n真實用戶評價機制確保每則評價來自真實參與者\n拒絕灌水與虛假評論。\n頂級療癒師評審團由業界領袖組成的專業評審團，\n確保高品質的療癒體驗。\n透明數據與公正推薦參考米其林評鑑標準\n以公平、透明的數據分析，幫助用戶找到最適合的療癒課程與療癒師。"
            )
            line_bot_api.reply_message(event.reply_token, message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

    elif mtext == '課程資訊':
        sendCarousel(event)
    elif mtext == '著名講師':
        sendCarousel2(event)
        
    
    
    # 指令：基礎問答啟動
    elif mtext == '基礎問答':
        user_states[user_id] = 0
        user_answers[user_id] = []
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=questions[0])
        )
        return

    # 問答進行中
    elif user_id in user_states:
        answer = mtext.strip()
        user_answers[user_id].append(answer)

        # ➕ 分析情緒並產生溫柔回覆
        emotion = basic_emotion_analysis(answer)
        mid_reply = generate_mid_reply(emotion)

        current_index = user_states[user_id] + 1

        if current_index < len(questions):
            user_states[user_id] = current_index
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=mid_reply),
                    TextSendMessage(text=questions[current_index])
                ]
            )
        else:
            # 最後一題，進行分類與推薦
            category = classify_user(user_answers[user_id])
            final_reply = recommend_forum(category)

            # 清除用戶狀態
            del user_states[user_id]
            del user_answers[user_id]

            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=mid_reply),
                    TextSendMessage(text=final_reply)
                ]
            )
        return
        
    else:
        # 如果是其他文字，則使用 Google Generative AI 生成回應
        user_prompt = mtext
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(user_prompt)
            result = response.text
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

def sendCarousel(event):
    try:
        message = TemplateSendMessage(
            alt_text='轉盤樣板',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/R1J1zW7.jpeg',
                        text='皮拉提斯入門',
                        actions=[
                            URITemplateAction(
                                label='課程資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/BX7OMX2.jpeg',
                        text='塔羅牌進階',
                        actions=[
                            URITemplateAction(
                                label='課程資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/n18NrpL.jpeg',
                        text='自我心靈探索',
                        actions=[
                            URITemplateAction(
                                label='課程資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/2O7bCV7.jpeg',
                        text='感情算命',
                        actions=[
                            URITemplateAction(
                                label='課程資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

def sendCarousel2(event):
    try:
        message = TemplateSendMessage(
            alt_text='轉盤樣板',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/ZDb0U5y.jpeg',
                        text='王崇恩講師',
                        actions=[
                            URITemplateAction(
                                label='講師資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/j2Aju8v.jpeg',
                        text='玟明慧法師',
                        actions=[
                            URITemplateAction(
                                label='講師資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/ZDb0U5y.jpeg',
                        text='玉晴算命師',
                        actions=[
                            URITemplateAction(
                                label='講師資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/j2Aju8v.jpeg',
                        text='白忻月講師',
                        actions=[
                            URITemplateAction(
                                label='講師資訊連結',
                                uri='https://a111221038.wixstudio.com/my-site-3'
                            )
                        ]
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))


if __name__ == '__main__':
    app.run()
