import datetime
from pdf2image import convert_from_bytes
import telebot
from key import token, link
import requests
import gspread


def creds():
    sa = gspread.service_account(filename="service-account-google.json")
    sh = sa.open("Статистика проведенных мероприятий new")
    wks = sh.worksheet("Общая статистика v2")
    return (wks)


def sheets_update():
    wks = creds()
    global date_start_init, date_end_init
    date_start_init = wks.acell("D6").value
    date_end_init = wks.acell("D7").value

    date_end = datetime.date.today() - datetime.timedelta(days=1)
    date_start = (date_end - datetime.timedelta(days=15))
    # delta_days = 14
    # date_start = date_end - delta_days*24*60*60
    wks.update("D6", date_start.strftime("%d.%m.%Y"), raw=False)
    wks.update("D7", date_end.strftime("%d.%m.%Y"), raw=False)
    wks.update("E10", "дням", raw=False)


def sheets_set(date_start, date_end):
    wks = creds()
    global date_start_init, date_end_init
    date_start_init = wks.acell("D6").value
    date_end_init = wks.acell("D7").value
    wks.update("D6", date_start, raw=False)
    wks.update("D7", date_end, raw=False)
    wks.update("E10", "дням", raw=False)


def get_texts():
    wks = creds()
    date_start = wks.acell("D6").value
    date_end = wks.acell("D7").value
    v_sc = int(wks.acell("H7").value)
    v_sum = int(wks.acell("I7").value)
    v_sum_zamech = int(wks.acell("J7").value)

    if v_sc / v_sum < 0.3:
        tag_1 = "🔴"
    elif v_sc / v_sum < 0.6:
        tag_1 = "🟠"
    else:
        tag_1 = "🟢"

    if v_sc / v_sum > 0.5:
        tag_2 = "🔴"
    elif v_sc / v_sum > 0.2:
        tag_2 = "🟠"
    else:
        tag_2 = "🟢"
    v_sum_all_procent = f"{v_sum / v_sc:.0%}"
    v_sum_zamech_procent = f"{v_sum_zamech / v_sum:.0%}"
    v_sum_success_procent = f"{(v_sum - v_sum_zamech) / v_sc:.0%}"
    text = str("С " + date_start + " по " + date_end + ":\n\nВсего в СЦ проведено " + str(
        v_sc) + " мероприятий, из них в СУМ — " + str(
        v_sum) + " (" + v_sum_all_procent + ") " + tag_1 + "\n\nИз " + str(
        v_sum) + " мероприятий, проведенных в СУМ, " + str(
        v_sum_zamech) + " были с замечаниями (" + v_sum_zamech_procent + ") " + tag_2 + "\n\nИтого успешных мероприятий с использованием СУМ: " + v_sum_success_procent)
    return (text)


def download_as_png():
    response = requests.get(
        link)
    image = convert_from_bytes(response.content)[0].crop((100, 100, 1630, 1000))
    return (image)


def send_photo(mode, message):
    if mode == "custom":
        global start_inp, end_inp
        sheets_set(start_inp, end_inp)
    elif mode == "current":
        sheets_update()
        # import datetime
        # date_end = (datetime.date.today() - datetime.timedelta(days=1))
        # date_start = ((date_end - datetime.timedelta(days=15))).strftime("%d.%m.%Y")
        # sheets_set(date_start,date_end).strftime("%d.%m.%Y")

    # bot.send_photo(message.chat.id, photo=open("/Users/yuriy/Downloads/SUM/SUM_crop.png", "rb"))
    img = download_as_png()
    text = get_texts()
    bot.send_photo(message.chat.id, photo=img, caption=text)


bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     'Привет!')


@bot.message_handler(commands=['report_custom'])
def first(message):
    bot.send_message(message.chat.id,
                     "Привет! Я могу подготовить отчет об использовании СУМ.\n\nДля начала введите дату начала периода в формате: дд.мм.гггг")
    bot.register_next_step_handler(message, start_date)


def start_date(message):
    global start_inp, mode
    mode = "custom"
    start_inp = message.text
    bot.send_message(message.chat.id, "Теперь введите дату окончания периода в формате: дд.мм.гггг")
    bot.register_next_step_handler(message, end_date)


def end_date(message):
    global end_inp
    end_inp = message.text
    bot.send_message(message.chat.id, "Уже готовлю отчет. Подождите минуточку!")
    send_photo(mode, message)
    sheets_set(date_start_init, date_end_init)


@bot.message_handler(commands=['report_current'])
def ready(message):
    bot.send_message(message.chat.id, "Привет! Готовлю отчет об использовани СУМ за последние 14 дней")
    mode = "current"
    send_photo(mode, message)
    sheets_set(date_start_init, date_end_init)


bot.polling(none_stop=True)
