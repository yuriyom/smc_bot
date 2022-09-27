import datetime
import time
from pdf2image import convert_from_bytes
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import logging
from key import token, link
import pytz
import requests
import gspread
import re
from dateutil.relativedelta import *
from io import BytesIO


updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher


def creds():
    sa = gspread.service_account(filename="service-account-google.json")
    sh = sa.open("Статистика проведенных мероприятий new")
    wks = sh.worksheet("!Для чат-бота")
    return (wks)


def sheets_set(date_start, date_end, granularity = ""):
    print(date_start,date_end)
    wks = creds()
    global date_start_init, date_end_init
    date_start_init = wks.acell("D6").value
    date_end_init = wks.acell("D7").value

    wks.update("D6", date_start, raw=False)
    wks.update("D7", date_end, raw=False)
    days = (datetime.datetime.strptime(date_end, "%d.%m.%Y").date()-datetime.datetime.strptime(date_start, "%d.%m.%Y").date()).days
    print(days)
    #установка гранулярности (дни/недели)
    if granularity == "":
        #если в начале функции гранулярность не задана, то преиод более 25 дней будет отражаться по неделям, а менее — по дням
        if days>25:
            print()
            wks.update("E10", "неделям", raw=False)
        else:
            wks.update("E10", "дням", raw=False)
    #если гранулярность задана в функции, до будет использоваться заданное значение
    else: wks.update("E10", granularity, raw=False)

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
        start_cur = (end_cur - datetime.timedelta(days=14))
        end_cur = end_cur.strftime("%d.%m.%Y")
        start_cur = start_cur.strftime("%d.%m.%Y")
        sheets_set(start_cur, end_cur)
    elif mode == "current_30":
        end_cur = (datetime.date.today())
        # start_cur = (end_cur - datetime.timedelta(days=30))
        print(end_cur.day)
        start_cur = end_cur+relativedelta(months=-1)
        end_cur = end_cur.strftime("%d.%m.%Y")
        start_cur = start_cur.strftime("%d.%m.%Y")
        sheets_set(start_cur, end_cur)
    elif mode == "nakop":
        end_cur = (datetime.date.today())
        start_cur = datetime.date(2022,8,1)
        end_cur = end_cur.strftime("%d.%m.%Y")
        start_cur = start_cur.strftime("%d.%m.%Y")
        sheets_set(start_cur, end_cur)
    img = download_as_png()
    bio = BytesIO()
    bio.name = 'image.png'
    img.save(bio, 'png')
    bio.seek(0)
    img = bio.getvalue()
    text = get_texts()
    return img, text

b = False
chats = []
def auto_report(update, context):
    global b, chats
    command = context.args[0].lower()
    if("on" == command):
        b = True
        chats.append(update.effective_chat.id)
        update.message.reply_text("Проверочный отчет будет отправлен в среду в 13:00 ✅")
        # update.message.reply_text("Теперь отчет будет автоматически отправляться каждый понедельник в 13:00 ✅")
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
    print(chats)
    img1, text1 = take_photo("current_14")
    img2, text2 = take_photo("nakop")
    for id in chats:
        context.bot.send_photo(chat_id=id, photo=img1, caption=text1)
        context.bot.send_photo(chat_id=id, photo=img2, caption=text2)
    sheets_set(date_start_init, date_end_init)
job_daily = j.run_daily(planned, days=[2], time=datetime.time(hour=12, minute=59, second=45, tzinfo=pytz.timezone("Europe/Moscow")))
# job_daily = j.run_repeating(planned, 30)


def start(update, context):
    message = 'Привет!'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    print(update.effective_chat)
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def sub_id_list(update, context):
    if not chats: message = "Пока никто не подписался на рассылку"
    else: message = ",".join(map(str,chats))
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
dispatcher.add_handler(CommandHandler('sub_id_list', sub_id_list))


def report_2_weeks(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Готовлю отчет об использовани СУМ за последние 14 дней ⏱")
    try:
        img, text = take_photo("current_14")
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
        sheets_set(date_start_init, date_end_init)
    except:
        try:
            sheets_set(date_start_init, date_end_init)
        except:
            pass
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")
dispatcher.add_handler(CommandHandler('report_2_weeks', report_2_weeks))

def report_month(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Готовлю отчет об использовани СУМ за последний месяц ⏱")
    try:
        img, text = take_photo("current_30")
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
        sheets_set(date_start_init, date_end_init)
    except Exception as e:
        print(e)
        try:
            sheets_set(date_start_init, date_end_init)
        except:
            pass
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")
dispatcher.add_handler(CommandHandler('report_month', report_month))

def report_custom(update, context):
    context.bot.send_message(update.effective_chat.id,
                             "Введите дату начала и конца периода через запятую в формате:\n_дд.мм.гггг, дд.мм.гггг_",parse_mode='Markdown' )
    context.user_data[report_custom] = True

def report_custom_send(update, context):
    if context.user_data[report_custom]:
        try:
            global start_inp, end_inp
            print("jjj")
            date_inp = re.split(r'\s*,\s*',update.message.text)
            print(date_inp)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Готовлю отчет об использовани СУМ за указанный период ⏱", reply_to_message_id=update.message.message_id)
            # update.message.reply_text(text="Готовлю отчет об использовани СУМ за указанный период ⏱")
            start_inp = date_inp[0]
            end_inp = date_inp[1]
            img, text = take_photo("custom")
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
            sheets_set(date_start_init, date_end_init)
        except Exception as e:
            print(e)
            try:
                sheets_set(date_start_init, date_end_init)
            except Exception as e:
                print(e)
                pass
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")
        context.user_data[report_custom] = False

dispatcher.add_handler(CommandHandler('report_custom', report_custom))
dispatcher.add_handler(MessageHandler(Filters.regex("^[0-9\.\,\s]*$"), report_custom_send))



def help(update, context):
    command_list = []
    try:
        for i in dispatcher.handlers[0]:
            command_list.append('/'+i.command[0])
    except Exception:
        pass
    text = "Список доступных команд:\n"+"\n".join(command_list)+"\n/help"
    context.bot.send_message(chat_id = update.effective_chat.id, text = text)
dispatcher.add_handler(CommandHandler('help', help))

updater.start_polling()
updater.idle()