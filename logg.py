import system


def save_me(id, text):
    s = '{} <---- me: {}\n'.format(system.id2name(id), text).replace('\n', '  ') + '\n'
    print(s, end='')


def visual_log(message, n, t):
    s = mess_visual(message, n, t).replace('\n', '  ') + '\n'
    return s


def mess_visual(message, n='Anon', t='None'):
    time = message.date
    name = system.id2name(message.chat.id)
    text = message.text
    if not text:
        text = t
    if not name:
        name = n
    return "{} {}: {}".format(system.date_format(time-3), name, text)
