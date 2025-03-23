from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URITemplateAction, StickerSendMessage, ImageSendMessage
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
    
    # 處理自定義指令
    if mtext == '商品訂購':
        try:
            message = TemplateSendMessage(
                alt_text="商品訂購",
                template=ButtonsTemplate(
                    thumbnail_image_url='https://i.imgur.com/H253Dss.jpg',
                    title='商品訂購',
                    text='歡迎訂購coldstone冰品。',
                    actions=[
                        URITemplateAction(label='商品訂購', uri='https://liff.line.me/' + liffid)  # 開啟 LIFF 讓使用者輸入訂購資料
                    ]
                )
            )
            line_bot_api.reply_message(event.reply_token, message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

    elif mtext == '推薦品項':
        sendCarousel(event)

    elif mtext == '新品介紹':
        try:
            messages = [
                StickerSendMessage(package_id='1', sticker_id='2'),
                TextSendMessage(text="酷黑女王!\n\n口味\n極濃黑牛奶冰淇淋\n配料\n草莓+覆盆莓+小麻糬"),
                ImageSendMessage(original_content_url="https://i.imgur.com/H253Dss.jpeg", preview_image_url="https://i.imgur.com/H253Dss.jpeg")
            ]
            line_bot_api.reply_message(event.reply_token, messages)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

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
                        thumbnail_image_url='https://i.imgur.com/u0O4lst.jpeg',
                        text='酷黑女王',
                        actions=[
                            URITemplateAction(
                                label='產品連結',
                                uri='https://www.coldstone.com.tw/product/product_detail.aspx?p_id=IC130'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/IvsRhW6.jpeg',
                        text='酷黑法師',
                        actions=[
                            URITemplateAction(
                                label='產品連結',
                                uri='https://www.coldstone.com.tw/product/product_detail.aspx?p_id=IC131'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/H7SacYz.jpeg',
                        text='酷黑鬥士',
                        actions=[
                            URITemplateAction(
                                label='產品連結',
                                uri='https://www.coldstone.com.tw/product/product_detail.aspx?p_id=IC132'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://i.imgur.com/EnQE5j9.jpeg',
                        text='焙香蜜QQ',
                        actions=[
                            URITemplateAction(
                                label='產品連結',
                                uri='https://www.coldstone.com.tw/product/product_detail.aspx?p_id=IC129'
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
