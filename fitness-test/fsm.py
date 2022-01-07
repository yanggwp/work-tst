from transitions.extensions import GraphMachine
from linebot.models import ImageCarouselColumn, URITemplateAction, MessageTemplateAction
from utils import send_text_message, send_carousel_message, send_button_message, send_image_message
from bs4 import BeautifulSoup
import requests


#variable
gender = ''
gen = 0 #boy = 1 girl = 0
age_height_weight =[] 
age = 0
height = 0
weight = 0
days = 0
BMR = 0
TDEE = 0


class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    def is_going_to_gender(self, event):
        text = event.message.text
        return text.lower() == 'workout'

    def on_enter_gender(self, event):
        title = '請先提供您的基本資訊'
        text = '生理性別『男生』還是『女生』'
        btn = [
            MessageTemplateAction(
                label = '男生',
                text ='男生'
            ),
            MessageTemplateAction(
                label = '女生',
                text = '女生'
            ),
        ]
        url = 'https://i.imgur.com/KHzzaXD.jpg'
        send_button_message(event.reply_token, title, text, btn, url)

    def is_going_to_input_age(self, event):
        global gender
        text = event.message.text

        if text == '男生':
            gender = '男生'
            return True
        elif text == '女生':
            gender = '女生'
            return True
        return False

    def on_enter_input_age(self, event):
        send_text_message(event.reply_token, '請輸入您的年齡(整數)')

    def is_going_to_input_height(self, event):
        global age
        text = event.message.text

        if text.lower().isnumeric():
            age = int(text)
            return True
        return False

    def on_enter_input_height(self, event):
        send_text_message(event.reply_token, '請輸入您的身高(整數)')

    def is_going_to_input_weight(self, event):
        global height
        text = event.message.text

        if text.lower().isnumeric():
            height = int(text)
            return True
        return False

    def on_enter_input_weight(self, event):
        send_text_message(event.reply_token, '請輸入您的體重(整數)')

    def is_going_to_input_days(self, event):
        global weight
        text = event.message.text

        if text.lower().isnumeric():
            weight = int(text)
            return True
        return False

    def on_enter_input_days(self, event):
        send_text_message(event.reply_token, '請輸入您一週運動的天數(0~7的整數)')

    def is_going_to_choose(self, event):
        global days
        text = event.message.text

        if text.lower().isnumeric():
            days = int(text)
            if days >=0 and days <=7:
                return True

        if text.lower() == 'back':
            return True

        return False

    def on_enter_choose(self, event):
        global age, gender, height, weight, days
        title = '您想要查看『運動』還是『熱量』'
        text = '年齡: ' + str(age) + '歲，性別: ' + gender + '，\n身高: ' + str(height) + '公分，體重: ' + str(weight) + '公斤，\n一週運動' + str(days) + '天'
        btn = [
            MessageTemplateAction(
                label = '運動',
                text ='運動'
            ),
            MessageTemplateAction(
                label = '熱量',
                text = '熱量'
            ),
        ]
        url = 'https://i.imgur.com/aprk8tj.jpg'
        send_button_message(event.reply_token, title, text, btn, url)

    def is_going_to_exercise(self, event):
        global diet_type
        text = event.message.text
        if (text == '運動') or ((self.state == 'show_cal' or self.state == 'show_video' or self.state == 'get_video') and (text.lower() == 'back')):
            return True
        return False

    def on_enter_exercise(self, event):
        title = '運動選單'
        text = '輸入『影片』可以觀看健身影片。'
        btn = [
            MessageTemplateAction(
                label = '影片',
                text = '影片'
            ),
            MessageTemplateAction(
                label = 'back',
                text = 'back'
            ),
        ]
        url = 'https://i.imgur.com/1qkfFhN.jpg'
        send_button_message(event.reply_token, title, text, btn, url)

    def is_going_to_show_kcal(self, event):
        text = event.message.text
        if text == '熱量':
            return True
        return False

    def on_enter_show_kcal(self, event):
        global age, gender, height, weight, days, BMR, TDEE
        if gender == '男生':
            gen = 1
            BMR = 9.99*weight + 6.25*height - 4.92*age + (166*gen-161)
        else:
            gen = 0
            BMR = 9.99*weight + 6.25*height - 4.92*age + (166*gen-161)

        if days ==0:
             TDEE = BMR*1.2
        elif days >0 and days <=3:
            TDEE = BMR*1.375
        elif days >3 and days <=5:
            TDEE = BMR*1.55
        elif days >5 and days <=7:
            TDEE = BMR*1.72

        title = 'BMR: ' + '{:.1f}'.format(BMR) + '大卡\nTDEE: ' + '{:.1f}'.format(TDEE) + '大卡'
        text = '輸入『BMR』或『TDEE』有說明'
        btn = [
            MessageTemplateAction(
                label = 'BMR',
                text = 'BMR'
            ),
            MessageTemplateAction(
                label = 'TDEE',
                text ='TDEE'
            ),
            MessageTemplateAction(
                label = 'back',
                text = 'back'
            ),
        ]
        url = 'https://i.imgur.com/ZCFXEgp.jpg'
        send_button_message(event.reply_token, title, text, btn, url)

    def is_going_to_showvideo(self, event):
        text = event.message.text
        if text == '影片':
            return True
        return False
    
    def on_enter_showvideo(self, event):
        url = 'https://www.youtube.com/results?search_query=' + '健身'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')

        url_list = []
        img_list = []
        for i in range(5):
            url_list.append('https://www.youtube.com' + soup.select('.yt-lockup-video')[i].select("a[rel='spf-prefetch']")[0].get("href"))
            img_list.append(soup.select('.yt-lockup-video')[i].select('img')[0].get('src'))

        col = []
        for i in range(5):
            c = ImageCarouselColumn(
                image_url = img_list[i],
                action = URITemplateAction(
                    label = '點我觀看影片',
                    uri = url_list[i]
                )
            )
            col.append(c)

        send_carousel_message(event.reply_token, col)

