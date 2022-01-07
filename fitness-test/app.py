import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from fsm import TocMachine
from utils import send_text_message, send_carousel_message, send_button_message, send_image_message

load_dotenv()


machine = TocMachine(
    states=[
        'gender',
        'input_age',
        'input_height',
        'input_weight',
        'input_days',
        'choose',
        'exercise',
        'show_kcal',
        'showvideo',
        'output_BMR_TDEE'
    ],
    transitions=[
        {'trigger': 'advance', 'source': 'user', 'dest': 'gender', 'conditions': 'is_going_to_gender'},
        {'trigger': 'advance', 'source': 'gender', 'dest': 'input_age', 'conditions': 'is_going_to_input_age'},
        {'trigger': 'advance', 'source': 'input_age', 'dest': 'input_height', 'conditions': 'is_going_to_input_height'},
        {'trigger': 'advance', 'source': 'input_height', 'dest': 'input_weight', 'conditions': 'is_going_to_input_weight'},
        {'trigger': 'advance', 'source': 'input_weight', 'dest': 'input_days', 'conditions': 'is_going_to_input_days'},
        {'trigger': 'advance', 'source': 'input_days', 'dest': 'choose', 'conditions': 'is_going_to_choose'},
        {'trigger': 'advance', 'source': 'choose', 'dest': 'exercise', 'conditions': 'is_going_to_exercise'},
        {'trigger': 'advance', 'source': 'choose', 'dest': 'show_kcal', 'conditions': 'is_going_to_show_kcal'},
        {'trigger': 'advance', 'source': 'exercise', 'dest': 'showvideo', 'conditions': 'is_going_to_showvideo'},
        {'trigger': 'advance', 'source': 'showvideo', 'dest': 'exercise', 'conditions': 'is_going_to_exercise'},
        {'trigger': 'advance', 'source': 'show_kcal', 'dest': 'choose', 'conditions': 'is_going_to_choose'},
        {'trigger': 'advance', 'source': 'exercise', 'dest': 'choose', 'conditions': 'is_going_to_choose'},

        {
            'trigger': 'go_back',
            'source': [
                'gender',
                'input_age',
                'input_height',
                'input_weight',
                'input_days',
                'choose',
                'exercise',
                'show_kcal',
                'showvideo',
                'output_BMR_TDEE'
            ],
            'dest': 'user'
        },
    ],
    initial="user",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path='')


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"



@app.route("/webhook", methods=["POST"])
def webhook_handler():
    global mode
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")

        if event.message.text.lower() == 'fsm':
                send_image_message(event.reply_token, 'https://d510-111-242-75-87.ngrok.io/show-fsm')
        response = machine.advance(event)
        if response == False:
            if event.message.text.lower() == 'fsm':
                send_image_message(event.reply_token, 'https://d510-111-242-75-87.ngrok.io/show-fsm')
            elif machine.state != 'user' and event.message.text.lower() == 'restart':
                send_text_message(event.reply_token, 'c輸入 『workout』即可開始使用健身小幫手。\n輸入『restart』可以從頭開始。\n輸入『fsm』可以得到當下的狀態圖。')
                machine.go_back()
            elif machine.state == 'user':
                send_text_message(event.reply_token, 'f輸入『workout』即可開始使用健身小幫手。\n輸入『restart』可以從頭開始。\n輸入『fsm』可以得到當下的狀態圖。')
            elif machine.state == 'gender':
                send_text_message(event.reply_token, '請輸入『男生』或『女生』')
            elif machine.state == 'input_age' or machine.state == 'input_height' or machine.state == 'input_weight':
                send_text_message(event.reply_token, '請輸入一個整數')
            elif machine.state == 'input_days':
                send_text_message(event.reply_token, '請輸入一個『0~7的整數』')
            elif machine.state == 'choose':
                send_text_message(event.reply_token, '請輸入『運動』或『熱量』')
            elif machine.state == 'exercise':
                send_text_message(event.reply_token, '輸入『影片』可以觀看健身影片。\n輸入『back』可重新選擇目標。')
            elif machine.state == 'show_kcal':
                if event.message.text.lower() == 'bmr':
                    text = '即基礎代謝率，全名為 Basal Metabolic Rate。指人體在清醒而極度安靜情況下，例如靜臥的狀態，不受精神緊張，肌肉活動，食物和環境溫度等因素影響時，所消耗的最低熱量，基礎代謝率會隨著年紀增加或體重減輕而降低，會隨著肌肉量增加而上升。'
                    send_text_message(event.reply_token, text)
                elif event.message.text.lower() == 'tdee':
                    text = '即每日總消耗熱量，全名為 Total Daily Energy Expenditure。指的是人體在一天內消耗的熱量，除了基礎代謝率所需的能量以外，還包括運動和其他活動消耗的熱量，像是走路、上下樓梯、活動肌肉等等。通常運動量愈大，TDEE也會愈高。'
                    send_text_message(event.reply_token, text)
                elif event.message.text.lower() != 'back':
                    send_text_message(event.reply_token, '輸入『BMR』或『TDEE』會有文字說明。\n輸入『back』返回選單。')
            elif machine.state == 'show_video' and event.message.text.lower() != 'back':
                send_text_message(event.reply_token, '輸入『back』返回選單。')
    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.jpg", prog="dot", format="jpg")
    return send_file("fsm.jpg", mimetype="image/jpg")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
