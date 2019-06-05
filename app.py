from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import configparser
import requests
import re
from bs4 import BeautifulSoup
import html
import random

app = Flask(__name__)

config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # get request body as text
    body = request.get_data(as_text=True)
    #print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

url = 'https://anime1.me'

def get_content(site):
    lst = []
    #headers = {'User-Agent':'Mozilla/5.0 (Linux; U; Android 4.1; en-us; GT-N7100 Build/JRO03C) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
    #User-Agent:Mozilla/5.0 (Linux; U; Android 4.1; en-us; GT-N7100 Build/JRO03C) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30
    res = requests.get(site)
    soup = BeautifulSoup(res.text,'html.parser')
    content = soup.find('main').find_all('iframe')
    
    for i in content:
        episode = re.search(r'src="(.*?)"',str(i)).group(1)
        lst.append(episode)

    if soup.find('div',{'class','nav-previous'}):
        page = soup.find('div',{'class','nav-previous'})
        #print(page)
        prev_url = re.search(r'<a href="(.*?)">',str(page)).group(1)
        return lst + get_content(prev_url)
    else:
        return lst


def search_anime(tar = ''):
    lst = []
    res = requests.get(url)
    soup = BeautifulSoup(res.text,'html.parser')
    soup = soup.find('table', attrs={'class','tablepress tablepress-id-1'}) 

    for i in soup.find_all('tr')[1:]:
        name = re.search(r'<a href="(.*?)">(.*?)</a>',str(i)).group(2)
        if tar in name:
            dic = {}
            dic['url'] = re.search(r'<a href="(.*?)">(.*?)</a>',str(i)).group(1)
            dic['name'] = name
            dic['stat'] = re.search(r'<td class="column-2">(.*?)</td>',str(i)).group(1)
            lst.append(dic)
    return lst
    
def latest_anime():
    lst = []
    res = requests.get(url)
    soup = BeautifulSoup(res.text,'html.parser')
    soup = soup.find('table', attrs={'class','tablepress tablepress-id-1'}) 

    for i in soup.find_all('tr')[1:11]:
        name = re.search(r'<a href="(.*?)">(.*?)</a>',str(i)).group(2)
        dic = {}
        dic['url'] = re.search(r'<a href="(.*?)">(.*?)</a>',str(i)).group(1)
        dic['name'] = name
        dic['stat'] = re.search(r'<td class="column-2">(.*?)</td>',str(i)).group(1)
        lst.append(dic)
    
    return lst


# def get_h_img():
#     #https://kukuo.nctu.me/anime/photo/index.php?min_width=&min_height=
#     img_url = 'http://konachan.com/post?tags=&page='
#     page = random.randrange(0, 9990,)
#     print(page)
#     res = requests.get(img_url+str(page))
#     soup = BeautifulSoup(res.text,'html.parser').find('div',attrs={'class','content'})
#     soup = soup.find_all('li')
#     soup = soup[random.randrange(len(soup))].find_all('a')[1]
#     return soup.get('href')

def get_h_img():
    n = str(random.randrange(1,333))
    img_url = 'https://kukuo.nctu.me/anime/photo/R18/'+n+'.png'
    return img_url

def get_anime_img(anime_name):
    url = 'https://tw.images.search.yahoo.com/search/images;_ylt=AwrtFGPRxg5bWioAMxZr1gt.;_ylu=X3oDMTE0NnEyOGxiBGNvbG8DdHcxBHBvcwMxBHZ0aWQDQjU1NTVfMQRzZWMDcGl2cw--?p='+anime_name+'&fr2=piv-web&fr=yfp-search-sb'
    res = requests.get(url)
    soup = BeautifulSoup(res.text,'html.parser').find('div',attrs={'class':'sres-cntr'}).find('li').find('a').find('noscript').find('img').get('src')
    return soup

def get_normal_img():
    #https://kukuo.nctu.me/anime/photo/original/6473.png
    n = str(random.randrange(1,6474))
    img_url = 'https://kukuo.nctu.me/anime/photo/original/'+n+'.png'
    return img_url



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)
    print("hello")
    if event.message.text.split(' ')[0] == '搜尋':
        tar = event.message.text.split(' ')[1]
        lst = search_anime(tar)
        message = TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url = get_anime_img(i['name']),
                        title=i['name'],
                        text=i['stat'],
                        actions=[
                            MessageTemplateAction(
                                label='開始觀看',
                                text='開始觀看'+i['url']
                            )
                        ]
                    )
                    for i in lst 
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0

    if event.message.text[:4] == '開始觀看':
        count = 1
        episode = ''
        for i in reversed(get_content(url+event.message.text[4:])):
            episode = episode+"第"+str(count)+"集"+'\n'+i+'\n'
            count = count + 1
        message = TextSendMessage(text=episode)
        line_bot_api.reply_message(event.reply_token, message)
        return 0 

    if event.message.text == '抓':
        img = get_h_img()
        message = ImageSendMessage(
            original_content_url=img,
            preview_image_url=img
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0

    if event.message.text == '圖':
        img = get_normal_img()
        message = ImageSendMessage(
            original_content_url=img,
            preview_image_url=img
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0
        
    if event.message.text == '最近更新':
        lst = latest_anime()
        message = TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url = get_anime_img(i['name']),
                        title=i['name'],
                        text=i['stat'],
                        actions=[
                            MessageTemplateAction(
                                label='開始觀看',
                                text='開始觀看'+i['url']
                            )
                        ]
                    )
                    for i in lst
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0
        
    
if __name__ == "__main__":
    app.run()