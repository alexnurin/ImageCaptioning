import telebot
from telebot import types
import numpy as np
import os
import time
from collections import Counter
import secret
from logg import *
from system import *

if os.name == 'nt':
    tg_tk = secret.token2  # Тестирование
    python_run = 'python'
else:
    tg_tk = secret.token
    python_run = 'python3'

bot = telebot.TeleBot(tg_tk, threaded=False)
new_tags = dict()
image_tag = dict()
search_dict = dict()
admins = secret.admins
boss_id = admins[0]


@bot.message_handler(func=lambda message: message.chat.id in admins and message.text and message.text[0] != '/')
def admin_message(message):
    boss_id = save_mess(message)
    t = message.text.split()
    cmd = t[0].lower()
    if cmd == "send":
        send(t[1], t[2])
    elif cmd == "all":
        users = all_for_boss(t[1])
        send(boss_id, users)
    elif cmd == 'len':
        users = all_for_boss(t[1])
        send(boss_id, len(users))
    elif cmd == 'sys':
        con = sqlite3.connect(f)
        db = con.cursor()

        cmd = "ALTER TABLE images ADD COLUMN cluster"
        db.execute(cmd)

        cmd = 'UPDATE images SET cluster = -1'
        db.execute(cmd)

        con.commit()
        con.close()

    elif cmd == 'cluster':
        send(boss_id, 'Go!!')
        os.system("{} clustering/clustering.py".format(python_run))
        send(boss_id, 'Done!')
    elif cmd == "image":
        send_image(boss_id, t[1])
    elif cmd == 'break' and int(time.time()) - message.date < 5:
        send_boss("Я упаль")
        exit(0)
    else:
        send(boss_id, message.text)


def all_for_boss(table_name):
    db = sqlite3.connect(f).cursor()
    q = 'SELECT * FROM {}'.format(table_name)
    db.execute(q, )
    res = ''
    for i in db.fetchall():
        res += str(i) + '\n'
    return res


@bot.message_handler(commands=['help', 'start'])
def help_message(message):
    id = save_mess(message, printing=0)
    send(id, '''
/help - все команды
/register - регистрация (в 1 клик)
/me - информация о пользователе
/image - получить случайное изображение
/tag - начать ставить теги
/support - техподдержка
/search - поиск по тегам (alpha)
''')


@bot.message_handler(commands=['tag'])
def start_tags(message):
    id = save_mess(message)
    image_ids = get_random_images()
    if not image_ids:
        send(id, "Упс, картинки для тегов закончились...")
        return
    image_id = None
    for i in image_ids:
        olds = id2tags(i)
        print(i, olds)
        if (id != boss_id and not already_check(id, i)) or (id == boss_id and len(olds) > 0):
            image_id = i
            break
    if not image_id:
        send(id, "Упс, картинки для тегов закончились...")
        return
    send_image(id, '{}'.format(image_id))
    new_tags[id] = []
    image_tag[id] = image_id
    send(id, '''Ставь теги! Для завершения отправь точку (.), для перехода к некст картинке - запятую (,)
Оптимальное число тегов - 5-10.''')
    bot.register_next_step_handler(message, get_tag)


def already_check(id, image_id):
    db = sqlite3.connect(f).cursor()
    q = 'SELECT * FROM tags WHERE image_id = ? AND from_id = ?'
    db.execute(q, (image_id, id))
    return len(db.fetchall())


def get_tag(message):
    id = save_mess(message)
    text = message.text
    if not text:
        return
    if text == '.':
        end_tags(id, image_tag[id])
        help_message(message)
    elif text == ',':
        send(id, "Ок, переходим к следующему...")
        end_tags(id, image_tag[id])
        start_tags(message)
    elif text[0] == '/':
        end_tags(id, image_tag[id])
        help_message(message)
    else:
        new_tags[id] += text.lower().split()
        send(id, 'Принято')
        bot.register_next_step_handler(message, get_tag)


def save_tag(text, from_id, image_id):
    conn = sqlite3.connect(f)
    db = conn.cursor()
    q = 'INSERT INTO tags (image_id, from_id, text) VALUES (?, ?, ?)'
    db.execute(q, (image_id, from_id, text))
    conn.commit()
    conn.close()


def end_tags(id, image_id):
    if len(new_tags[id]) < 1:
        return
    points = 5
    print(new_tags[id])
    olds = id2tags(image_id)
    omega_olds = ''
    print(olds)
    cluster_olds = cluster2ids(id2cluster(image_id))
    print(cluster_olds, id2cluster(image_id), )
    for i in cluster_olds:
        omega_olds += ' '.join(id2tags(i))
    print(omega_olds)

    with open("./tmp/tags/{}.txt".format(image_id), 'a', encoding='utf-8') as f:
        f.write(('\n'.join(new_tags[id])) + "\n")
    for i in new_tags[id]:
        save_tag(i, id, image_id)
        if i in olds:
            points += 5
        points += (omega_olds.count(i) + 1) // 2
    send(id, "Вот что получилось: " + ', '.join(new_tags[id]))
    send_boss("$Картинка {} получила теги: ".format(image_id) + ', '.join(new_tags[id]))
    new_tags[id] = []
    add_points(id, points)


def id2tags(image_id):
    if os.path.isfile("./tmp/tags/{}.txt".format(image_id)):
        return open("./tmp/tags/{}.txt".format(image_id), 'r', encoding='utf-8').read().split('\n')
    return []


def id2cluster(image_id):
    db = sqlite3.connect(f).cursor()
    q = 'SELECT cluster FROM images WHERE image_id = ?'
    db.execute(q, (image_id,))
    return db.fetchall()[0][0]


def cluster2ids(cluster):
    db = sqlite3.connect(f).cursor()
    q = 'SELECT image_id FROM images WHERE cluster = ?'
    db.execute(q, (cluster,))
    return [i[0] for i in db.fetchall()]


@bot.message_handler(commands=['register'])
def register_message(message):
    id = save_mess(message)
    register(id, message.chat.username)


def register(id, login):
    if not login:
        login = "NoName"
    conn = sqlite3.connect(f)
    db = conn.cursor()
    now = id2user(id)
    if not now:
        q = 'INSERT INTO users (user, login, points, rating) VALUES (?, ?, 0, 1000)'
        db.execute(q, (id, login,))
        send(id, 'Регистрация успешна! Отныне вы - {}. \n/me для полной информации'.format(login))
    else:
        send(id, 'Вы уже зарегистрированы. Ваше имя - {}. \n/me для полной информации'.format(id2name(id)))
    conn.commit()
    conn.close()


@bot.message_handler(commands=['support'])
def support_message(message):
    id = save_mess(message)
    send(id, 'Введите фразу, она уйдёт в техподдержку. "." для выхода')
    bot.register_next_step_handler(message, support)


def support(message):
    id = save_mess(message)
    if message.text == '.':
        help_message(message)
        return
    with open("support.txt", "a", encoding='utf-8') as sup:
        sup.write("{} сказал: ".format(id2name(id)) + message.text + "\n")
    send(id, "Успешно!")


@bot.message_handler(commands=['me'])
def me_message(message):
    id = save_mess(message)
    kek = list(map(lambda m: str(m), id2user(id)))
    if len(kek) == 0:
        resp = 'Я ничего о тебе не знаю! Зарегистрируйся: /register'
    else:
        resp = 'Имя: {}\nПойнты: {}\nРейтинг: {}\n'.format(kek[2], kek[3], kek[4])
    send(id, resp)


@bot.message_handler(content_types=['photo'])
def new_image(message):
    id = save_mess(message, t='Photo')
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    olds = open('tmp/data.txt', 'r').readlines()
    if len(olds) > 10000:
        send(id, "Кажется, у нас проблемы с памятью сервера... Специалисты уже выехали")
        return
    if file_id + '\n' in olds:
        bot.reply_to(message, "Такая картинка уже есть!")
        return
    downloaded_file = bot.download_file(file_info.file_path)
    file = len(olds) + 1
    src = 'tmp/new/{}.png'.format(file)
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    image_save(message, file)
    with open("tmp/data.txt", 'a') as add:
        add.write(file_id + '\n')


def image_save(message, file):
    conn = sqlite3.connect(f)
    db = conn.cursor()
    q = 'INSERT INTO images (image_id, from_id, username, status, cluster) VALUES (?,?,?,0,-1)'
    db.execute(q, (file, message.chat.id, id2name(message.chat.id)))
    conn.commit()
    conn.close()
    bot.reply_to(message, "Фото добавлено")
    add_points(message.chat.id, 5)


@bot.message_handler(commands=['image', 'mem'])
def print_random_image(message):
    id = save_mess(message)
    image_id = get_random_images()
    if not image_id:
        send(id, "У нас закончились картинки... Печально.")
        return
    send_image(id, image_id[0])


def get_random_images():
    db = sqlite3.connect(f).cursor()
    q = 'SELECT image_id FROM images'
    db.execute(q)
    resp = db.fetchall()
    np.random.shuffle(resp)
    return [el[0] for el in resp]


@bot.message_handler(commands=['sticker'])
def get_sticker(message):
    id = save_mess(message)
    stickers = list(set(open("top_stickers.txt", 'r').read().split('\n')[:-1]))
    s = np.random.choice(stickers, 1)
    for i in s:
        bot.send_sticker(id, i)


@bot.message_handler(content_types=['sticker'])
def new_sticker(message):
    id = save_mess(message, t='Sticker')
    sticker_id = message.json['sticker']['file_id']
    stickers = list(set(open("top_stickers.txt", 'r').read().split('\n')[:-1]))
    if sticker_id in stickers:
        bot.reply_to(message, 'Уже есть!')
    else:
        with open("top_stickers.txt", 'a') as top:
            top.write(sticker_id + "\n")
        send(id, 'Сохранено')
        add_points(message.chat.id, 5)


@bot.message_handler(commands=['search'])
def search_message(message):
    id = save_mess(message)
    search_dict[id] = []
    send(id, 'Вводите теги. "." для завершения')
    bot.register_next_step_handler(message, search_add)


def search_add(message):
    id = save_mess(message)
    text = message.text
    if text == '.':
        search_print(message)
    else:
        search_dict[id] += text.lower().split()
        bot.register_next_step_handler(message, search_add)


def search_print(message):
    id = save_mess(message, printing=0)
    db = sqlite3.connect(f).cursor()
    old = []
    new = []
    tags = search_dict.get(id)
    if not tags:
        send(id, "Не введено ни одного тега(")
        help_message(message)
        return
    for tag in search_dict[id]:
        q = 'SELECT image_id FROM tags WHERE text == ?'
        db.execute(q, (tag,))
        new = db.fetchall()
        new = [el for el in new if el in old or not old]
        if len(new) <= 1:
            break
    if not new and not old:
        send(id, "Не найдено ничего по тегам {}".format(' '.join(tags)))
    else:
        if not new:
            send_image(id, old[0][0])
        else:
            send_image(id, new[0][0])


@bot.message_handler(content_types=['text'])
def text_message(message):
    id = save_mess(message)
    help_message(message)


@bot.message_handler(lambda message: True)
def another_message(message):
    help_message(message)


def add_points(id, delta):
    conn = sqlite3.connect(f)
    db = conn.cursor()
    cur = id2user(id)
    if not cur:
        send(id, 'Кажется, вы не зарегистрированы... /register')
    else:
        cur = cur[-2] + delta
        send(id, "Очки пересчитаны. Добавлено {}. Теперь - {}".format(delta, cur))
        q = 'UPDATE users SET points = ? WHERE user = ?'
        db.execute(q, (cur, id))
    conn.commit()
    conn.close()


def add_rating(id, delta):
    conn = sqlite3.connect(f)
    db = conn.cursor()
    cur = id2user(id)
    if not cur:
        send(id, 'Кажется, вы не зарегистрированы... /register')
    else:
        cur = cur[-1] + delta
        send(id, "Рейтинг изменён. Добавлено {}. Теперь - {}".format(delta, cur))
        q = 'UPDATE users SET rating = ? WHERE user = ?'
        db.execute(q, (cur, id))
    conn.commit()
    conn.close()


def create_tables():
    conn_ = sqlite3.connect(f)
    db_ = conn_.cursor()
    init_query = 'CREATE TABLE IF NOT EXISTS users(id integer NOT NULL PRIMARY KEY AUTOINCREMENT, user integer,' \
                 ' login, points integer, rating integer)'
    db_.execute(init_query)
    init_query = 'CREATE TABLE IF NOT EXISTS images(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, image_id INTEGER, ' \
                 'from_id INTEGER, username, status INTEGER, cluster INTEGER)'
    db_.execute(init_query)
    init_query = 'CREATE TABLE IF NOT EXISTS tags(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, image_id INTEGER, ' \
                 'from_id INTEGER, username, text)'
    db_.execute(init_query)
    conn_.commit()
    conn_.close()


def save_mess(message, n='Anon', t='None', printing=1):
    if id2name(message.chat.id) == 'Anonimus':
        register(message.chat.id, message.chat.username)
    if printing:
        print(visual_log(message, n, t), end='')
    return message.chat.id


if __name__ == '__main__':
    create_tables()
    print('Start!\n')
    while 1:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            send(boss_id, "$ Вызвана ошибка: " + str(e))
