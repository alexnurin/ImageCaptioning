import sqlite3
from main import bot, admins, boss_id
import logg

f = 'DragonBall.sqlite'


def send(id, text, reply=None):
    logg.save_me(id, text)
    bot.send_message(id, text, reply_markup=reply)


def send_boss(text):
    bot.send_message(boss_id, text)


def send_image(id, img):
    try:
        logg.save_me(id, "Image: {}.png".format(int(img)))
        image = open('tmp/new/{}.png'.format(int(img)), 'rb')
        bot.send_photo(id, image)
    except FileNotFoundError:
        send(id, "Какая-то ошибка, попробуйте позже")
        return "NotFound"


def date_format(time):
    hr = time % 86400 // 3600
    min = time % 3600 // 60
    sec = time % 60
    return "{:02d}:{:02d}:{:02d}".format((int(hr) + 3) % 24, min, sec)


def all_ids():
    db = sqlite3.connect(f).cursor()
    q = 'SELECT user FROM users'
    db.execute(q, )
    resp = db.fetchall()
    res = set()
    for i in resp:
        if i[0]:
            res.add(i[0])
    return list(res)


def id2name(id):
    res = id2user(id)
    if not res:
        return 'Anonimus'
    return res[2]


def id2user(id):
    db = sqlite3.connect(f).cursor()
    q = 'SELECT * FROM users WHERE user = ?'
    db.execute(q, (id,))
    resp = db.fetchone()
    if not resp:
        res = ''
    else:
        res = resp
    return res
