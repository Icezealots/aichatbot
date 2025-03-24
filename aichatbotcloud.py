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
    if mtext == '平台介紹':
        try:
            message = TextSendMessage(
                text="Soulv \n身心靈界的米其林指南\n全球首個身心靈開箱與評鑑指南\n幫助你找到真正值得信賴的療癒體驗與課程\n不只是要創造一個平台\n而是一場身心靈療癒界的透明化運動。\nSoulv 如何運作？\n真實用戶評價機制確保每則評價來自真實參與者\n拒絕灌水與虛假評論。\n頂級療癒師評審團由業界領袖組成的專業評審團，確保高品質的療癒體驗。\n透明數據與公正推薦參考米其林評鑑標準，以公平、透明的數據分析，幫助用戶找到最適合的療癒課程與療癒師。"
            )
            line_bot_api.reply_message(event.reply_token, message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))

    elif mtext == '課程資訊':
        sendCarousel(event)
    elif mtext == '著名講師':
        sendCarousel2(event)
        
    elif mtext == '身體':
       
        try:
            messages = [
                TextSendMessage(text="身體健康!\n\n維持良好的身體健康需要適當的運動、均衡的飲食和充足的休息\n身體狀況良好時，心理和精神狀態也會更穩定，幫助我們面對生活中的各種挑戰"),
                #ImageSendMessage(original_content_url="https://i.imgur.com/H253Dss.jpeg", preview_image_url="https://i.imgur.com/H253Dss.jpeg"),
                TemplateSendMessage(
                    alt_text='身體健康資訊',
                    template=ButtonsTemplate(
                        title='更多資訊',
                        text='點擊下方按鈕查看網站',
                        actions=[
                            URITemplateAction(
                                label='訪問網站',
                                uri='https://a111221038.wixstudio.com/my-site-3/forum/pu-tong-tao-lun?rc=test-site'
                            )
                        ]
                    )
                )
            ]
            line_bot_api.reply_message(event.reply_token, messages)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))
               
    elif mtext == '心理':
        try:
            messages = [
                TextSendMessage(text="心靈平靜!\n\n是一種內心的寧靜和安穩狀態，當我們的內心不再被外界的壓力和焦慮所打擾，便能感受到這份平和。\n保持心靈平靜的方式包括冥想、正念練習和自我反思。\n這些方法能幫助我們放下煩惱，專注當下，進而減少焦慮和壓力。\n心靈的平靜不僅能讓我們處理生活中的困難更加冷靜，也能讓我們在日常生活中感受到更多的幸福與滿足。\n在快速變化的世界中，保持心靈平靜是每個人都可以努力實踐的目標。"),
                #ImageSendMessage(original_content_url="https://i.imgur.com/H253Dss.jpeg", preview_image_url="https://i.imgur.com/H253Dss.jpeg"),
                TemplateSendMessage(
                    alt_text='靈性成長資訊',
                    template=ButtonsTemplate(
                        title='更多資訊',
                        text='點擊下方按鈕查看網站',
                        actions=[
                            URITemplateAction(
                                label='訪問網站',
                                uri='https://a111221038.wixstudio.com/my-site-3/forum/wen-yu-da?rc=test-site'
                            )
                        ]
                    )
                )
            ]
            line_bot_api.reply_message(event.reply_token, messages)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'發生錯誤: {str(e)}'))
    elif mtext == '靈性':
        try:
            messages = [
                TextSendMessage(text="靈性成長!\n\n靈性成長是指在個人內在世界的探索過程中，尋找生命的深層意義和目的。\n透過冥想、反思和學習，人們能夠拓展自己的心智與靈性，增進對宇宙和人生的感悟。\n靈性成長的過程幫助我們理解自己的內心需求，並能提升我們的同理心和對他人的愛。\n這種成長不僅能讓我們達到內心的平靜，也能讓我們在生活中更加有方向感，過得更有意義。"),
                #ImageSendMessage(original_content_url="https://i.imgur.com/H253Dss.jpeg", preview_image_url="https://i.imgur.com/H253Dss.jpeg"),
                TemplateSendMessage(
                    alt_text='靈性成長資訊',
                    template=ButtonsTemplate(
                        title='更多資訊',
                        text='點擊下方按鈕查看網站',
                        actions=[
                            URITemplateAction(
                                label='訪問網站',
                                uri='https://a111221038.wixstudio.com/my-site-3/forum/zhi-xian-yuan-gong?rc=test-site'
                            )
                        ]
                    )
                )
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
