from flask import Flask, render_template, request, url_for
import requests
import urllib.parse
import re
from bs4 import BeautifulSoup
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

app = Flask(__name__)

URL_ROOT = 'http://mojim.com/'
line_bot_api = LineBotApi("API移除，請自行添加")
handler = WebhookHandler("Webhook移除，請自行添加")
line_bot_api.push_message("User ID移除，請自行添加", TextSendMessage(text="歡迎來到 NTU 歌詞姬!"))
help_txt = """
NTU 歌詞姬
---------------------------
使用教學：

歌詞查詢
------------
例：查詢 青花瓷

便會回傳與青花瓷相關的歌詞

目前支援的指令有：

1. 查詢  搜尋相關的歌詞
2. 教學  顯示教學 
"""

# 歌名搜尋 修改自https://github.com/zephyros0305/lyric_search
def search_song(song_name):
    song_name += '.html?t3'
    url = urllib.parse.urljoin(URL_ROOT, song_name)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    songs = soup.find_all('dd', re.compile('^mxsh_dd'))
    del songs[0]
    song_list = list()

    for song in songs:
        meta = song.find('span', 'mxsh_ss4').find('a')
        name_temp = meta.getText().split('.')
        # print('name_temp=' + str(name_temp))
        song_list.append({
            'name': ''.join(name_temp[1:]),
            'singer': song.find('span', 'mxsh_ss2').getText(),
            'album': song.find('span', 'mxsh_ss3').getText(),
            'link': 'lyric?link=' + meta.get('href')[1:],
        })
    # print(song_list)
    return song_list

# 取得歌詞 修改自https://github.com/zephyros0305/lyric_search
def get_lyric(url):
    url = urllib.parse.urljoin(URL_ROOT, url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    lyric = soup.find('dl', 'fsZx1')

    a = re.compile('^\[\d+')

    lyricist = ''
    composer = ''
    arranger = ''
    lyric_list = list()
    for sentence in lyric.stripped_strings:
        if 'Mojim' in sentence or '更多更詳盡' in sentence:
            continue
        elif '作詞' in sentence:
            lyricist = sentence
            continue
        elif '作曲' in sentence:
            composer = sentence
            continue
        elif '編曲' in sentence:
            arranger = sentence
            continue
        if a.match(sentence):
            break
        lyric_list.append(sentence)

    singer = lyric_list.pop(0)
    name = lyric_list.pop(0)

    # 連結 歌手 歌名 作詞 作曲 編曲 歌詞
    song_detail = {
        'url': url,
        'singer':singer,
        'name':name,
        'lyricist': lyricist,
        'composer': composer,
        'arranger': arranger,
        'lyric':lyric_list,
    }
    # print(song_detail)
    return song_detail

# 回覆訊息
def createReplyMessge(sid):
    song_list = search_song(sid)
    print(song_list[0]['link'][11:])
    song = get_lyric(song_list[0]['link'][11:]) #直接取第一筆
    
    replyCheckMessage = ("歌詞姬 \n"
                         f"歌手：{song['singer']}\n"
                         f"歌名：{song['name']}\n"
                         f"作詞：{song['lyricist']}\n"
                         f"作曲：{song['composer']}\n"
                         f"編曲：{song['arranger']}\n"
                         f"歌詞：{song['lyric']}"
                        )

    return replyCheckMessage

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 指令辨識
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if "查詢" in event.message.text or "check" in event.message.text: 
        sid = event.message.text.split()[1]
        line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=createReplyMessge(sid), type="text")
        )
    elif "help" in event.message.text or "教學" in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=help_txt, type="text")
        )

# 首頁
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method =='POST':
        if request.values['send']=='送出':
            songs = search_song(request.values['song_name'])
            return render_template('lyric.html', songs = songs)
    return render_template("index.html")

# 歌詞頁面 搜尋頁面 功能:顯示搜尋結果、顯示歌詞
@app.route("/lyric", methods=['GET'])
def lyric():
    error = None
    lyrics = None
    link = request.args.get("link")
    song_detail = get_lyric(link)
    return render_template("lyric.html", error=error, song_detail=song_detail)



# @app.route("/notify")
# def notify():
#     token = "oPoMjuI8NJC9zVrc0W1feIR96Feh8qmjxuDvI8S6ZIi"
#     content = "我來自 Flask App，啾咪！"
#     line_url = "https://notify-api.line.me/api/notify"
#     headers = {
#             "Authorization": "Bearer " + token, 
#             "Content-Type" : "application/x-www-form-urlencoded"
#         }

#     payload = {'message': content}
#     r = requests.post(line_url, headers = headers, params = payload)

#     return {
#         "msg": "notify sent!"
#     }

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5151)
