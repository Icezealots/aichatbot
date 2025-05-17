from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URITemplateAction, StickerSendMessage, ImageSendMessage,CarouselTemplate, CarouselColumn, QuickReply, QuickReplyButton, MessageAction
)
import psycopg2
import google.generativeai as genai
import os
from urllib.parse import quote_plus
from datetime import datetime


# 初始化 Flask 應用程式
app = Flask(__name__)

# LINE Bot API 和 Webhook Handler 設定
line_bot_api = LineBotApi(os.environ.get('LinebotToken'))
handler = WebhookHandler(os.environ.get('LinebotSecret'))

# Google Generative AI 配置
genai.configure(api_key=os.environ.get('geminiapikey'))



# 溫柔問答題目
questions = [
    "🌿 1. 壓力與焦慮管理\n「嗨，歡迎你來到這裡。感覺你可能有點累了，或者心裡有點壓力，對嗎？\n想跟我聊聊最近讓你覺得焦慮或壓力大的事情嗎？」",
    
    "🌸 2. 自我探索與內在成長\n「有時候，我們會突然停下腳步，問自己：『我到底是誰？我真正想要的是什麼？』\n你最近也有這樣的感覺嗎？」",

    "💞 3. 人際關係與情感困擾\n「有些情感放在心裡久了會變得沉重，尤其是在人際關係中。\n你最近在人與人之間的連結上，有什麼讓你感到難過或困擾的嗎？」",

    "🍃 4. 身體健康與能量平衡\n「你的身體最近還好嗎？有時候我們忙著照顧別人，會忘了自己也需要被好好照顧。」",

    "✨ 5. 靈性連結與心靈成長\n「有時候，我們會感覺自己想找回與內在或宇宙的連結。\n你最近是否有這種渴望？想要更靠近那份寧靜與光？」"
]

# 心得生成
questions2 = [
    "🌿 1. 課程哪部分最有幫助？",
    
    "🌸 2. 有沒有哪裡可以改進？",

    "💞 3. 老師教學風格如何？",

    "🍃 4. 今天學到的重點是什麼？",

    "✨ 5. 推薦程度（1-5 顆星）"
]

# 儲存課後心得狀態用
course_feedback_states = {}
course_feedback_answers = {}


# 分類關鍵字
category_keywords = {
    "body": [
        "累", "疲倦", "疲憊", "無力", "睡", "睡不好", "睡不著", "失眠",
        "身體", "頭痛", "胃痛", "背痛", "肩膀緊", "心悸", "頭暈", "不舒服", "疼痛",
        "沒精神", "倦怠", "身體沉重", "感冒", "生理痛", "月經不順",
        "睡眠品質", "鬆不開", "呼吸困難", "心跳加快", "胃脹氣", "頭悶", "肩頸痠痛",
        "腸胃不適", "皮膚過敏", "過敏", "手腳冰冷", "食慾不振", "嗜睡", "常生病",
        "免疫力差", "腰痠", "肌肉緊繃", "身體卡卡", "睡醒更累", "長痘痘",
        "覺得身體怪怪的", "哪裡都不舒服", "整個人軟掉", "提不起精神","全身無力","眼睛疲勞","嗜睡","睡不飽","容易醒來","難入睡","排便不順","突然健忘",
    ],
    "mind": [
        "焦慮", "壓力", "孤單", "低落", "沮喪", "煩惱", "情緒", "緊張", "不安",
        "憂鬱", "難過", "委屈", "崩潰", "不想動", "情緒化", "內耗", "煩躁",
        "失落", "心煩", "恐懼", "沒有動力", "覺得累", "想逃避",
        "想太多", "心累", "無助", "忍不住哭", "無力感", "沒有方向",
        "情緒低潮", "難以專注", "壓抑", "繃緊", "常常發呆", "思緒混亂",
        "被否定", "沒人懂", "覺得被討厭", "失控", "想消失", "不被理解",
        "自我懷疑", "過度努力","無法專注","心神不寧","提不起勁",
        "腦袋停不下來", "一直轉念頭", "心裡很雜", "卡住出不來", "很煩很煩", "腦子打結","情緒起伏大"
    ],
    "spirit": [
        "意義", "人生", "存在", "靈魂", "心靈", "空虛", "迷惘", "自我", "覺醒",
        "靈性", "宇宙", "高我", "內在聲音", "使命", "方向", "冥想", "連結",
        "能量", "轉化", "療癒", "覺察", "成長", "覺知", "找不到自己",
        "找不到意義", "覺得空洞", "活著為什麼", "無所歸屬", "心靈空虛",
        "宇宙訊息", "指引", "宇宙法則", "靈魂契約", "身心靈", "通靈", "昇華",
        "靈魂旅程", "與自己對話", "內在小孩", "靜心", "宇宙連線", "內在指引",
        "意識擴展", "靈魂碎片", "醒來的感覺",
        "覺得被困住", "不知道我到底是誰", "覺得空空的", "對什麼都沒感覺",
        "一直在找答案", "想要找回自己", "感覺不到熱情", "心好遠"
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
        "body": "你可以看看這個身體保健的溫柔角落 🌿 https://www.soulv.fun/forum/pu-tong-tao-lun?rc=test-site",
        "mind": "這裡有一些心理支持的溫暖資源 🧠 https://www.soulv.fun/forum/wen-yu-da?rc=test-site",
        "spirit": "想探索心靈與自我，可以看看這個空間 ✨ https://www.soulv.fun/forum/zhi-xian-yuan-gong?rc=test-site"
    }
    return forums.get(category, "希望這段對話有帶給你一些溫暖 💖")

def basic_emotion_analysis(answer):
    answer = answer.lower()

    emotion_keywords = {
        "金錢壓力": [
            '錢', '沒錢', '薪水', '經濟', '月底', '房租', '負擔', '工作薪資', '破產', '卡債',
            '繳不出來', '支出', '花費', '信用卡', '貸款', '收支', '財務', '投資失利', '存款', '超支',
            '繳學貸', '收入太低', '生計', '財務壓力', '賺錢', '被裁員', '通膨', '生活費', '零用錢', '錢不夠用',
            '欠錢', '金錢焦慮', '高物價', '購物壓力', '繳帳單', '負債累累', '省錢', '窮', '錢包空空',
            '失業', '斷炊', '物價上漲', '經濟困境', '財務狀況', '買不起', '理財失敗', '入不敷出', '經濟壓力', '欠債'
        ],
        "情感困擾": [
            '男友', '女友', '感情', '愛情', '分手', '戀愛', '前任', '伴侶', '失戀', '情人',
            '在一起', '吵架', '爭執', '冷淡', '不愛了', '曖昧', '情緒勒索', '出軌', '不回訊息', '拉黑',
            '沒感覺', '變心', '不被重視', '曖昧對象', '心碎', '失望', '沒有安全感', '情緒不穩', '被劈腿', '冷處理',
            '溝通困難', '想復合', '戀愛煩惱', '不適合', '遠距離', '沒有話題', '對方不理我', '被忽視', '曖昧期', '太黏',
            '被拒絕', '求而不得', '不信任', '太快進展', '沒有共識', '感覺變了', '彼此疲乏', '沒激情', '對方變了', '愛而不得'
        ],
        "人際孤獨": [
            '孤單', '寂寞', '沒人懂', '朋友', '人際', '吵架', '冷戰', '被排擠', '沒有朋友', '被討厭',
            '誤解', '被忽略', '社交', '覺得孤單', '邊緣人', '社交恐懼', '不被接納', '孤立', '自己一個人', '無人關心',
            '無人傾聽', '尷尬', '不合群', '不融入', '朋友很少', '不被喜歡', '被冷落', '怕尷尬', '話不投機', '被當空氣',
            '不想社交', '社交壓力', '說話卡卡', '講話沒人聽', '內向', '人際壓力', '覺得多餘', '不想出門', '假朋友', '社交焦慮',
            '朋友圈小', '朋友都忙', '沒人陪', '講話被打斷', '被排除', '沒共鳴', '尷尬癌', '孤僻', '交不到朋友', '邊緣化'
        ],
        "低能量": [
            '不知道', '還好', '沒有', '普通', '沒什麼', '就這樣', '無感', '不想說', '不知道為什麼', '不知道該怎麼辦',
            '隨便', '都好', '還行', '無聊', '不在乎', '無所謂', '提不起勁', '懶得想', '不想動', '沒想法',
            '沒有動力', '一成不變', '太平淡', '好無趣', '沒有期待', '不驚不喜', '無聊到爆', '不想做事', '只是在過日子', '毫無情緒',
            '心如止水', '空白', '覺得無趣', '好像機器人', '每天都一樣', '沒情緒起伏', '沒火花', '好累', '人生沒勁', '沒有想法',
            '無聊透頂', '過一天算一天', '提不起精神', '沒感覺', '不知道怎麼辦', '想躺平', '心很淡', '腦袋空空', '提不起興趣', '無波無瀾'
        ],
        "焦慮": [
            '壓力', '焦慮', '緊張', '疲憊', '擔心', '煩躁', '煩', '手忙腳亂', '喘不過氣', '恐慌',
            '無法控制', '心跳很快', '情緒緊繃', '憂鬱', '失控', '心煩', '煩惱', '過度思考', '負面思考', '壓得喘不過氣',
            '壓力大', '生活好累', '累到想哭', '心好亂', '睡不好', '緊繃', '壓力爆棚', '心情差', '想爆炸', '有點崩潰',
            '頭很痛', '控制不了', '時間不夠', '事情太多', '怕出錯', '被責備', '做不好', '怕被罵', '怕被討厭', '怕失敗',
            '怕面對', '焦頭爛額', '搞砸了', '緊迫', '沒辦法休息', '累炸', '情緒上來了', '壓力來源', '煩得要命', '不知所措'
        ],
        "穩定": [
            '快樂', '開心', '平靜', '放鬆', '自在', '穩定', '喜悅', '滿足', '幸福', '感恩',
            '心情好', '被療癒', '安心', '安定', '放空', '舒服', '療癒', '微笑', '被理解', '被接納',
            '有陪伴', '被支持', '被肯定', '達成目標', '喜歡現在的狀態', '生活很棒', '心情穩', '正能量', '被照顧', '感到自由',
            '輕鬆', '愉悅', '自在生活', '心裡舒服', '感到溫暖', '覺得幸福', '心中有光', '美好的一天', '笑容滿面', '感覺良好',
            '有安全感', '正面情緒', '無憂無慮', '沒壓力', '平穩', '和諧', '情緒平衡', '悠閒', '心情穩定', '舒服自在'
        ],
        "身體不適": [
            '生病', '頭痛', '身體不舒服', '感冒', '不想動', '發燒', '喉嚨痛', '咳嗽', '胃痛', '全身痠痛',
            '沒力氣', '不舒服', '肚子痛', '頭暈', '想吐', '過敏', '拉肚子', '手腳無力', '發冷', '打噴嚏',
            '喉嚨卡卡', '胸悶', '心悸', '腳痛', '腰痠', '感覺虛弱', '免疫力低', '一直想睡', '腸胃炎', '四肢無力',
            '冒冷汗', '不想吃東西', '食慾不振', '感覺暈', '發炎', '全身無力', '流鼻水', '鼻塞', '肢體痠痛', '肌肉緊繃',
            '精神不濟', '嗜睡', '虛脫', '喉嚨癢', '胸口悶', '有點燒', '失去味覺', '耳鳴', '全身重重的', '體溫上升'
        ],
        "熬夜疲勞": [
            '熬夜', '睡不著', '太晚睡', '沒睡好', '睡很少', '作息亂', '黑眼圈', '好累', '醒來很累', '失眠',
            '腦袋昏', '白天很睏', '睡眠不足', '補眠', '夜貓子', '翻來覆去', '數羊', '難入睡', '壓力大睡不好', '早醒',
            '一直醒來', '睡不深', '夜晚清醒', '整晚沒睡', '沒有睡意', '睡不沉', '淺眠', '晚睡早起', '作息不正常', '賴床',
            '白天想睡', '上班很睏', '精神不濟', '不想起床', '醒太早', '半夜驚醒', '被夢吵醒', '太早起', '沒精神', '沒動力',
            '覺得疲憊', '早上頭昏', '昏昏沉沉', '疲累', '眼睛睜不開', '想補眠', '精神差', '整天累', '沒活力', '累炸了'
        ],
        "靈性迷惘": [
            '沒意義', '空虛', '迷失', '人生', '存在', '想法混亂', '意義', '方向', '不知道為了什麼', '想消失',
            '想放棄', '內在掙扎', '心靈空洞', '內耗', '靈魂疲憊', '找不到方向', '自我懷疑', '覺得虛無', '找不到自己', '覺得沒價值',
            '沒有目標', '人生卡關', '自我迷失', '對未來迷茫', '靈魂迷惘', '人生黑洞', '被困住', '人生迷路', '沒有答案', '找不到意義',
            '覺得渺小', '無法專注', '對生命無感', '想遠離人群', '沒有歸屬', '懷疑人生', '心靈封閉', '內在混亂', '問自己是誰', '沒有熱情',
            '靈性困惑', '找不到方向感', '被現實壓垮', '覺得不存在', '缺乏使命感', '想逃避現實', '對未來無感', '迷失自己', '精神空轉', '覺得沒救'
        ],
        "自我否定": [
            '自卑', '沒自信', '沒價值', '我很爛', '不值得', '覺得自己不好', '無能', '沒用', '一直失敗', '做不好',
            '我不好', '討厭自己', '自我否定', '總是搞砸', '自責', '自我懷疑', '覺得自己是負擔', '不配', '不夠好', '很差勁', '被看不起'
        ],
        "生活混亂": [
            '亂', '生活好亂', '家裡很亂', '東西到處都是', '沒規律', '太多事情', '行程太滿', '時間不夠', '生活失控', '一直拖延',
            '做不完', '忘東忘西', '沒效率', '拖延症', '很混亂', '收不回來', '無法安排', '焦頭爛額', '雜亂無章', '計畫趕不上變化'
        ],
        "目標迷失": [
            '不知道目標', '沒方向', '不知道想做什麼', '目標模糊', '不知道未來', '沒有夢想', '迷惘', '不知道人生要什麼', '覺得人生卡住了',
            '沒志向', '失去動力', '沒有野心', '沒有企圖心', '沒熱情', '覺得浪費人生', '走一步算一步', '未來很模糊', '每天都很茫然'
        ],
        "情緒壓抑": [
            '憋著', '不敢說', '壓在心裡', '好難受', '委屈', '壓抑', '想哭又哭不出來', '不知道怎麼說', '一直忍', '不能表達',
            '太壓抑', '悶', '裝沒事', '裝堅強', '卡住了', '表面平靜', '內心很亂', '假笑', '不敢發脾氣', '情緒低落'
        ],
        "現實壓力": [
            '活不下去', '社會壓力', '太競爭', '現實太殘酷', '生活太累', '扛太多', '被期待壓垮', '要求太多', '壓力來源',
            '身邊的人都在進步', '社會步調太快', '被比較', '跟不上別人', '現實殘酷', '活得好累', '好想逃', '不能停下來', '扛不住'
        ]
    }

    for emotion, keywords in emotion_keywords.items():
        if any(keyword in answer for keyword in keywords):
            return emotion

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
        "自我否定": "有時候我們對自己太嚴格了，其實你已經很努力了，願你能看見自己的珍貴 🌷",
        "生活混亂": "生活有時真的會變得一團亂，沒關係的，慢慢來，一件一件來，我們會一起釐清 💫",
        "目標迷失": "當方向感模糊時，不代表你沒有在前進，也許你只是需要多一點時間和自己對話 🌌",
        "情緒壓抑": "把那些藏起來的情緒輕輕放下也沒關係，我會在這裡接住你，慢慢地陪你走出來 🫧",
        "現實壓力": "現實真的常常太重了，願這一刻你能感受到一點點的輕盈與被理解 🤍",
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
    if mtext == '進入Soulv':
        try:
            user_id = event.source.user_id
            role = get_user_role(user_id)  # ← 檢查資料庫中有沒有這位使用者的角色
    
            if role:  # 如果已經設定過角色，顯示簡版歡迎訊息
                text = (
                    f"🌟 歡迎回來，{role}！\n"
                    "感謝你再次回到 Soulv 🌀\n\n"
                    "你可以輸入：\n"
                    "👉『開始使用』查看功能\n"
                    "👉『熱門體驗』探索課程"
                )
                message = TextSendMessage(text=text)
            else:
                # 如果還沒有選擇過角色，顯示完整歡迎並附上 quick reply
                text = (
                    "Soulv \n身心靈界的米其林指南\n全球首個身心靈開箱與評鑑指南\n幫助你找到真正值得信賴的療癒體驗與課程\n"
                    "不只是要創造一個平台\n而是一場身心靈療癒界的透明化運動。\n"
                    "Soulv 如何運作？\n真實用戶評價機制確保每則評價來自真實參與者\n拒絕灌水與虛假評論。\n"
                    "頂級療癒師評審團由業界領袖組成的專業評審團，\n確保高品質的療癒體驗。\n"
                    "透明數據與公正推薦參考米其林評鑑標準\n以公平、透明的數據分析，幫助用戶找到最適合的療癒課程與療癒師\n"
                    "🌐 Soulv網址：https://www.soulv.fun/\n\n👉 請選擇你的身分以下開始："
                )
                message = TextSendMessage(
                    text=text,
                    quick_reply=QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label="我是學員 👩‍🎓", text="我是學員")),
                        QuickReplyButton(action=MessageAction(label="我是療癒師 🧘‍♀️", text="我是療癒師"))
                    ])
                )
    
            line_bot_api.reply_message(event.reply_token, message)
    
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

    
    elif mtext == '開始使用':
        user_id = event.source.user_id
        role = get_user_role(user_id)
        
        if role == '學員':
            text = (
                "🌀 [Soulv Bot] 嗨，親愛的學員 💫 感謝你參與這次的療癒體驗，我們希望知道：它對你的改變是什麼？\n\n"
                "🌱【立即完成 1 分鐘靈性回饋】 就能解鎖以下好禮：\n"
                "👉 問卷連結：https://www.soulv.fun/feedback\n\n"
                "🎁 解鎖報告／抽獎／成長紀錄等\n\n"
                "👇 你還可以選擇：\n"
                "1️⃣ 查看我的靈性成長紀錄\n"
                "2️⃣ 查看下一個推薦課程\n"
                "3️⃣ 回報體驗問題"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))

        elif role == '療癒師':
            text = (
                "🔔 [Soulv Bot] 嗨，老師 🌿 Soulv 為您準備好提升「靈性影響力」的秘密武器了！\n\n"
                "✨【你專屬的問卷回饋任務已啟動】\n"
                "✅ 獲得五星導師徽章\n"
                "✅ 系統自動優先推薦\n"
                "✅ 問卷數據成為認證依據\n\n"
                "👉 這是你專屬的問卷連結：https://www.soulv.fun/form?teacher_id={user_id}\n\n"
                "👇 請選擇：\n"
                "1️⃣ 我的問卷完成率\n"
                "2️⃣ 我要修改介紹頁面\n"
                "3️⃣ 瞭解如何取得更多推薦"
            )
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
    
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先選擇你的身分 🙏"))
        
            
    elif mtext == '我是學員' or mtext == '我是療癒師':
        role = '學員' if mtext == '我是學員' else '療癒師'
        user_id = event.source.user_id
        try:
            save_user_role_to_db(user_id, role)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"✅ 你已選擇「{role}」身分，感謝你加入 Soulv 🙏")
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ 儲存身分失敗，請稍後再試：{str(e)}")
            )
        
    elif mtext == '熱門體驗':
        sendCarousel(event)
        
    
    
    # 指令：基礎問答啟動
    elif mtext == '和我聊聊':
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
    
    # 啟動課後心得問答流程
    elif mtext == '體驗分享':
        course_feedback_states[user_id] = 0
        course_feedback_answers[user_id] = []
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=questions2[0])
        )
        return
    
    # 若使用者正在進行課後心得問答
    elif user_id in course_feedback_states:
        answer = mtext.strip()
        course_feedback_answers[user_id].append(answer)
    
        current_index = course_feedback_states[user_id] + 1
    
        if current_index < len(questions2):
            course_feedback_states[user_id] = current_index
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=questions2[current_index])
            )
        else:
            # 問卷完成，準備生成心得
            student_answers = course_feedback_answers[user_id]
            prompt = f"根據以下體驗後問卷回答，請幫我整理成一段100到150字的心得紀錄，用溫柔、靈性陪伴的語氣撰寫，避免太商業化\n"
            for idx, ans in enumerate(student_answers, 1):
                prompt += f"{idx}. {ans}\n"
    
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                summary = response.text.strip()
    
                # 清除狀態
                del course_feedback_states[user_id]
                del course_feedback_answers[user_id]

                # 編碼 summary 以便放入網址參數
                encoded_summary = quote_plus(summary)

                # 組合網址，將 summary 當作參數帶入網站
                forum_url = f"https://www.soulv.fun/forum/zhi-xian-yuan-gong/create-post?rc=test-site&content={encoded_summary}"
                # 儲存心得至資料庫
                #save_feedback_to_db(user_id, summary)
    
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text="📝 以下是為你自動生成的課後心得："),
                        TextSendMessage(text=summary),
                        TextSendMessage(text="請點選以下連結，將這段心得貼到網站上與大家分享：\nhttps://www.soulv.fun/forum/zhi-xian-yuan-gong/create-post?rc=test-site")
                    ]
                )
    
                # 可在這邊先暫存 summary 綁定 user_id，待確認發布
                # e.g., pending_summaries[user_id] = summary
    
            except Exception as e:
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text="😢 很抱歉，產生心得時出了點小狀況，請稍後再試一次，或直接將你的分享貼到網站上。"),
                        TextSendMessage(text=f"🛠️ 技術訊息（請截圖給開發者）：{str(e)}")
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

#取得身分
def get_user_role(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM user_roles WHERE line_id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return result[0]  # 回傳角色字串
    return None

        # 設定資料庫連接
def get_db_connection():
    conn = psycopg2.connect(
        dbname="soulvdb", 
        user="soulv", 
        password="W2Gv0pOvwSVbPLjUiCTOwMEVpwItArfT",
        host="dpg-d0k968nfte5s738frv4g-a.oregon-postgres.render.com", 
        port="5432"
    )
    return conn

# 儲存心得到資料庫
def save_feedback_to_db(user_id, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO feedbacks (user_id, feedback) VALUES (%s, %s)"
    cursor.execute(query, (user_id, feedback))
    conn.commit()
    cursor.close()
    conn.close()
    
# 儲存身分到資料庫
def save_user_role_to_db(user_id, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO user_roles (line_id, role)
        VALUES (%s, %s)
        ON CONFLICT (line_id)
        DO UPDATE SET role = EXCLUDED.role;
    """
    cursor.execute(query, (user_id, role))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    app.run()
