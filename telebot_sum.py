import datetime
from pdf2image import convert_from_bytes
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import logging
from key import token, link
import pytz
import requests
import gspread
from io import BytesIO


updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    message = 'Привет!'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    print(update.effective_chat.id)
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)



def creds():
    sa = gspread.service_account(filename="service-account-google.json")
    sh = sa.open("Статистика проведенных мероприятий new")
    wks = sh.worksheet("!Для чат-бота")
    return (wks)


def sheets_set(date_start, date_end, granularity = "дням"):
    wks = creds()
    global date_start_init, date_end_init
    date_start_init = wks.acell("D6").value
    date_end_init = wks.acell("D7").value

    wks.update("D6", date_start, raw=False)
    wks.update("D7", date_end, raw=False)
    wks.update("E10", granularity, raw=False)

def get_texts():
    wks = creds()
    date_start = wks.acell("D6").value
    date_end = wks.acell("D7").value
    v_sc = int(wks.acell("H7").value)
    v_sum = int(wks.acell("I7").value)
    try:
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
            v_sum) + " мероприятий в СУМ " + str(
            v_sum_zamech) + " были с замечаниями (" + v_sum_zamech_procent + ") " + tag_2 + "\n\nИтого успешных мероприятий с использованием СУМ: " + v_sum_success_procent)
    except:
        text = str("С " + date_start + " по " + date_end + ":\n\nВсего в СЦ проведено " + str(v_sc) + " мероприятий, из них в СУМ — " + "0 🔴")
    return (text)

def download_as_png():
    response = requests.get(
        link)
    image = convert_from_bytes(response.content)[1].crop((100, 100, 1630, 1000))
    return (image)

def take_photo(mode):
    if mode == "custom":
        global start_inp, end_inp
        sheets_set(start_inp, end_inp)
    elif mode == "current_14":
        end_cur = (datetime.date.today())
        start_cur = (end_cur - datetime.timedelta(days=15))
        end_cur = end_cur.strftime("%d.%m.%Y")
        start_cur = start_cur.strftime("%d.%m.%Y")
        sheets_set(start_cur, end_cur)
    elif mode == "current_30":
        end_cur = (datetime.date.today())
        start_cur = (end_cur - datetime.timedelta(days=30))
        end_cur = end_cur.strftime("%d.%m.%Y")
        start_cur = start_cur.strftime("%d.%m.%Y")
        sheets_set(start_cur, end_cur)
    elif mode == "nakop":
        end_cur = (datetime.date.today())
        start_cur = datetime.date(2022,8,1)
        end_cur = end_cur.strftime("%d.%m.%Y")
        start_cur = start_cur.strftime("%d.%m.%Y")
        sheets_set(start_cur, end_cur, "неделям")
    img = download_as_png()
    text = get_texts()
    return img, text
    # bot.send_photo(chat_id = chatid, photo=img, caption=text)


b = False
chats = []
def auto_report(update, context):
    global b, chats
    command = context.args[0].lower()
    print(command)
    if("on" == command):
        b = True
        chats.append(update.effective_chat.id)
        print("on")
        update.message.reply_text("Теперь отчет будет отправляться каждый поредельник в 13:00")
    elif("off" == command):
        b = False
        update.message.reply_text("Теперь авто-отчёт отправляться не будет")
        try:
            chats.remove(update.effective_chat.id)
        except:
            pass
dispatcher.add_handler(CommandHandler('auto_report', auto_report))
j = updater.job_queue

def planned(context: CallbackContext):
    global b, chats
    print('lll')
    print(chats)

    img1, text1 = take_photo("current_14")
    img2, text2 = take_photo("nakop")
    bio1 = BytesIO()
    bio1.name = 'image1.png'
    img1.save(bio1, 'png')
    bio1.seek(0)
    bio2 = BytesIO()
    bio2.name = 'image2.png'
    img2.save(bio2, 'png')
    bio2.seek(0)
    print('lll2')
    for id in chats:
        context.bot.send_photo(chat_id=id, photo=bio1, caption=text1)
        context.bot.send_photo(chat_id=id, photo=bio2, caption=text2)
    sheets_set(date_start_init, date_end_init)
# job_daily = j.run_daily(planned, days=(0,1,6), time=datetime.time(hour=8, minute=47, second=00, tzinfo=pytz.timezone("Europe/Moscow")))
job_daily = j.run_repeating(planned, 30)


def start(update, context):
    message = 'Привет!'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    print(update.effective_chat.id)
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def report_2_weeks(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Готовлю отчет об использовани СУМ за последние 14 дней ⏱")
    try:
        img, text = take_photo("current_14")
        bio = BytesIO()
        bio.name = 'image.png'
        img.save(bio, 'png')
        bio.seek(0)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio, caption=text)
        sheets_set(date_start_init, date_end_init)
    except:
        try:
            sheets_set(date_start_init, date_end_init)
        except:
            pass
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")

report_2_weeks_handler = CommandHandler('report_2_weeks', report_2_weeks)
dispatcher.add_handler(report_2_weeks_handler)

def report_month(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Готовлю отчет об использовани СУМ за последний месяц ⏱")
    try:
        img, text = take_photo("current_30")
        bio = BytesIO()
        bio.name = 'image.png'
        img.save(bio, 'png')
        bio.seek(0)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio, caption=text)
        sheets_set(date_start_init, date_end_init)
    except:
        try:
            sheets_set(date_start_init, date_end_init)
        except:
            pass
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")

report_month_handler = CommandHandler('report_month', report_month)
dispatcher.add_handler(report_month_handler)

def report_custom(update, context):
    context.bot.send_message(update.effective_chat.id,
                             "Введите дату начала и конца периода через запятую в формате:\n_дд.мм.гггг, дд.мм.гггг_",parse_mode='Markdown' )
    context.user_data[report_custom] = True

def report_custom_send(update, context):
    if context.user_data[report_custom]:
        try:
            global start_inp, end_inp
            date_inp = update.message.text.split(',')
            start_inp = date_inp[0]
            end_inp = date_inp[1]
            img, text = take_photo("custom")
            bio = BytesIO()
            bio.name = 'image.png'
            img.save(bio, 'png')
            bio.seek(0)
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio, caption=text)
            sheets_set(date_start_init, date_end_init)
        except:
            try:
                sheets_set(date_start_init, date_end_init)
            except:
                pass
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")
        context.user_data[report_custom] = False

dispatcher.add_handler(CommandHandler('report_custom', report_custom))
dispatcher.add_handler(MessageHandler(Filters.text, report_custom_send))

updater.start_polling()
updater.idle()