import datetime
from pdf2image import convert_from_bytes
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from key import token, link
import requests
import gspread
import shutil
from dateutil.relativedelta import *
import pytz
from io import BytesIO
import re
import os
import pandas as pd


updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher


def creds():
    sa = gspread.service_account(filename="service-account-google.json")
    sh = sa.open("Статистика проведенных мероприятий new")
    wks = sh.worksheet("!Для чат-бота")
    return (wks)


def sheets_set(date_start, date_end, granularity = ""):
    wks = creds()
    global date_start_init, date_end_init
    date_start_init = wks.acell("D6").value
    date_end_init = wks.acell("D7").value

    wks.update("D6", date_start, raw=False)
    wks.update("D7", date_end, raw=False)
    days = (datetime.datetime.strptime(date_end, "%d.%m.%Y").date()-datetime.datetime.strptime(date_start, "%d.%m.%Y").date()).days
    #установка гранулярности (дни/недели)
    if granularity == "":
        #если в начале функции гранулярность не задана, то преиод более 25 дней будет отражаться по неделям, а менее — по дням
        if days>25:
            wks.update("E10", "неделям", raw=False)
        else:
            wks.update("E10", "дням", raw=False)
    #если гранулярность задана в функции, до будет использоваться заданное значение
    else: wks.update("E10", granularity, raw=False)

def get_texts():
    try:
        wks = creds()
        date_start = wks.acell("D6").value
        date_end = wks.acell("D7").value
        v_sc = int(wks.acell("I7").value)
        v_sum_possible = int(wks.acell("J7").value)
        v_sum = int(wks.acell("K7").value)
        re1 = str(wks.acell("P19").value or '')
        re2 = str(wks.acell("P20").value or '')
        re3 = str(wks.acell("P21").value or '')
        val1 = f'{int(wks.acell("Q19").value or 0)/(v_sc-v_sum):.0%}'.replace("0%", '')
        val2 = f'{int(wks.acell("Q20").value or 0)/(v_sc-v_sum):.0%}'.replace("0%", '')
        val3 = f'{int(wks.acell("Q21").value or 0)/(v_sc-v_sum):.0%}'.replace("0%", '')
        # val1 = f'{wks.acell('Q19').value:.0%}'
        # val2 = f"{wks.acell('Q20').value:.0%}"ъ
        # val3 = f"{wks.acell('Q21').value:.0%}"
    except Exception as e:
        print(e)
        pass
    try:
    #     v_sum_zamech = int(wks.acell("L7").value)
        if v_sum / v_sum_possible < 0.3:
            tag_1 = "🔴"
        elif v_sum / v_sum_possible < 0.6:
            tag_1 = "🟠"
        else:
            tag_1 = "🟢"
        # if v_sum_zamech / v_sum > 0.5:
        #     tag_2 = "🔴"
        # elif v_sum_zamech / v_sum > 0.2:
        #     tag_2 = "🟠"
        # else:
        #     tag_2 = "🟢"
        v_sum_all_procent = f"{v_sum / v_sum_possible:.0%}"
        text = "С " + date_start + " по " + date_end + ":\n\nВсего в СЦ проведено: " + str(v_sc) + " мероприятий" + "\n\nВ СУМ проведено: "+str(v_sum)+ " из "+ str(v_sum_possible)+" возможных (" + v_sum_all_procent + ") "+tag_1+"\n\nТоп-3 причины проведения мероприятий без СУМ:\n1. "+re1+": "+val1+"\n2. "+re2+": "+val2+"\n3. "+re3+": "+val3
                   # "\n\nИтого успешных мероприятий с использованием СУМ: " + v_sum_success_procent
        # v_sum_zamech_procent = f"{v_sum_zamech / v_sum:.0%}"
        # v_sum_success_procent = f"{(v_sum - v_sum_zamech) / v_sc:.0%}"
        # text = str("С " + date_start + " по " + date_end + ":\n\nВсего в СЦ проведено " + str(
        #     v_sc) + " мероприятий, из них в СУМ — " + str(
        #     v_sum) + " (" + v_sum_all_procent + ") " + tag_1 + "\n\nИз " + str(
        #     v_sum) + " мероприятий в СУМ " + str(
        #     v_sum_zamech) + " были с замечаниями (" + v_sum_zamech_procent + ") " + tag_2)
        #            # "\n\nИтого успешных мероприятий с использованием СУМ: " + v_sum_success_procent
    except Exception as e:
        print(e)
        text = str("С " + date_start + " по " + date_end + ":\n\nВсего в СЦ проведено " + str(v_sc) + " мероприятий, из них в СУМ — " + "0 🔴")
    return (text)

def download_as_png():
    response = requests.get(
        link)
    image = convert_from_bytes(response.content)[-2].crop((100, 100, 1630, 1000))
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

def auto_report(update, context):
    command = context.args[0].lower()
    df = pd.read_csv('subscribers.txt', names=['id','name'], header=0)
    id = update.effective_chat.id
    if("on" == command):
        if id not in df['id'].values:
            if id < 0:
                name = update.effective_chat.title
            else:
                name = update.effective_chat.first_name + ' '+ (update.effective_chat.last_name or '')
            df.loc[len(df)] = [id,name]
            df.to_csv('subscribers.txt',index=False)
            # update.message.reply_text("Проверочный отчет будет отправлен в среду в 13:00 ✅")
            update.message.reply_text("Теперь отчет будет автоматически отправляться каждый понедельник в 13:00 ✅")
        else:
            # update.message.reply_text("Вы уже подписаны\nНапоминаю, проверочный отчет будет отправлен в среду в 13:00⏱")
            update.message.reply_text("Вы уже подписаны\nНапоминаю, отчет отправляется в понедельник в 13:00⏱")
    elif("off" == command):
        if id in df['id'].values:
            df = df[df['id']!=id]
            df.to_csv('subscribers.txt', index=False)
            update.message.reply_text("Теперь авто-отчёт отправляться не будет ⛔️")
        else:
            update.message.reply_text("Кажется, вы не были подписаны на рассылку")
dispatcher.add_handler(CommandHandler('auto_report', auto_report))
j = updater.job_queue

def planned(context: CallbackContext):
    df = pd.read_csv('subscribers.txt', names=['id','name'], header=0)
    sub_list = df['id']
    img1, text1 = take_photo("current_14")
    # img2, text2 = take_photo("nakop")
    for id in sub_list:
        try:
            # context.bot.send_message(chat_id=id, text = 'Подготовлен еженедельный отчет об использовании СУМ 📊 \n1. За последние 2 недели\n2. За период с 01.08 по текщую дату')
            context.bot.send_message(chat_id=id, text = 'Подготовлен еженедельный отчет об использовании СУМ за последние две недели 📊')
            context.bot.send_photo(chat_id=id, photo=img1, caption=text1)
        except:
            continue
        # context.bot.send_photo(chat_id=id, photo=img2, caption=text2)
    sheets_set(date_start_init, date_end_init)
job_daily = j.run_daily(planned, days=[0], time=datetime.time(hour=13, minute=00, second=00, tzinfo=pytz.timezone("Europe/Moscow")))
# job_daily = j.run_daily(planned, days=[1], time=datetime.time(hour=16, minute=39, second=00, tzinfo=pytz.timezone("Europe/Moscow")))
# job_daily = j.run_repeating(planned, 60)


def start(update, context):
    if update.effective_chat.id <0:
        message = 'Привет всем в чате «'+ update.effective_chat.title+'» 👋'
    else:
        message = 'Привет, '+ update.effective_chat.first_name+"!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def subs_list(update, context):
    with open('subscribers.txt', 'r') as f:
        message = f.read()
    if message == '':
        message = "Пока никто не подписался на рассылку"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
dispatcher.add_handler(CommandHandler('subs_list', subs_list))


def report_2_weeks(update, context):
    must_delete = context.bot.send_message(chat_id=update.effective_chat.id, text = "Готовлю отчет об использовани СУМ за последние 14 дней ⏱")
    try:
        img, text = take_photo("current_14")
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
        context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=update.message.chat_id)
        sheets_set(date_start_init, date_end_init)
    except Exception as e:
        # print(e)
        try:
            sheets_set(date_start_init, date_end_init)
        except:
            pass
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")
        context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=update.message.chat_id)
dispatcher.add_handler(CommandHandler('report_2_weeks', report_2_weeks))

def report_month(update, context):
    must_delete = context.bot.send_message(chat_id=update.effective_chat.id, text = "Готовлю отчет об использовани СУМ за последний месяц ⏱")
    try:
        img, text = take_photo("current_30")
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
        context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=update.message.chat_id)
        sheets_set(date_start_init, date_end_init)
    except Exception as e:
        print(e)
        try:
            sheets_set(date_start_init, date_end_init)
        except:
            pass
        context.bot.send_message(chat_id = update.effective_chat.id, text = "Что-то пошло не так...\nПопробуйте еще раз!\nОбратите внимание на формат дат")
        context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=update.message.chat_id)
dispatcher.add_handler(CommandHandler('report_month', report_month))

def report_custom(update, context):
    global must_delete_custom
    must_delete_custom = context.bot.send_message(update.effective_chat.id,
                             "Введите дату начала и конца периода через запятую в формате:\n_дд.мм.гггг, дд.мм.гггг_",parse_mode='Markdown' )
    context.user_data[report_custom] = True

def report_custom_send(update, context):
    if context.user_data[report_custom]:
        pattern = re.compile(r'\s*(\d{1,2})\D(\d{1,2})\D(\d{4})\n*.\s*(\d{1,2})\D(\d{1,2})\D(\d{4})', re.DOTALL)
        def repl(match):
            return '{:0>2}.{:0>2}.{:0>4},{:0>2}.{:0>2}.{:0>4}'.format(*match.groups())
        try:
            global start_inp, end_inp
            date_inp = pattern.sub(repl, update.message.text).split(',')
            context.bot.deleteMessage(message_id=must_delete_custom.message_id, chat_id=update.message.chat_id)
            must_delete = update.message.reply_text("Готовлю отчет об использовани СУМ за указанный период ⏱")
            start_inp = date_inp[0]
            end_inp = date_inp[1]
            img, text = take_photo("custom")
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
            context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=update.message.chat_id)
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
            context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=update.message.chat_id)
        context.user_data[report_custom] = False

dispatcher.add_handler(CommandHandler('report_custom', report_custom))
# dispatcher.add_handler(MessageHandler(Filters.regex("^\s*(\d{1,2})\D(\d{1,2})\D(\d{4})\n*.\s*(\d{1,2})\D(\d{1,2})\D(\d{4})$"), report_custom_send))
pattern = re.compile(r'\s*(\d{1,2})\D(\d{1,2})\D(\d{4})\n*.\s*(\d{1,2})\D(\d{1,2})\D(\d{4})', re.DOTALL)
dispatcher.add_handler(MessageHandler(Filters.regex(pattern), report_custom_send))

# def get_file(update, context):
#     context.bot.send_message(update.effective_chat.id,
#                              "Пришлите файл Excel или zip-архив с паспортами проектов из Bitrix" )
#     context.user_data[get_file] = True
# def downloader(update, context):
#     if context.user_data[get_file]:
#         try:
#             os.mkdir('temp')
#             bot_path = os.path.split(context.bot.get_file(update.message.document)["file_path"])[1]
#             path = os.path.join('temp',bot_path)
#             with open(path, 'wb') as f:
#                 context.bot.get_file(update.message.document).download(out=f)
#                 context.bot.send_message(chat_id=update.effective_chat.id,
#                                          text="Файл скачан, подождите ⏱")
#             main_rest = pd.DataFrame()
#             main_po = pd.DataFrame()
#             path_to_save = os.path.split(path)[0]
#             if path.endswith('.xlsx'):
#                 files = []
#                 files.append(os.path.split(path)[1])
#                 path_fin = os.path.split(path)[0]
#             else:
#                 shutil.unpack_archive(path, "temp")
#                 os.remove(os.path.join("temp", bot_path))
#                 path = os.path.join("temp",os.listdir("temp")[0])
#                 files = os.listdir(path)
#                 path_fin = path
#             for file in files:
#                 if file != ".DS_Store":
#                     df = pd.read_excel(os.path.join(path_fin, file), header=None)
#                     df.replace({"\n{1,}": '\n', "\r{1,}": '\n', "\r\n{1,}": '\n', "\t{1,}": ' ', " +": " "}, regex=True,
#                                inplace=True)
#                     df.replace({" {2,}": ' '}, inplace=True)
#                     df.iloc[2][1] = str(df.iloc[2][0]).replace("&quot;", '"')
#                     df = df[df[0] != "Параметр проекта:"]
#                     df.iloc[2][0] = "Организация"
#                     df[1].str.strip()
#                     if (df.iloc[8][1] == "Комитет по развитию общесистемного и прикладного ПО") or (
#                             "Комитет" in df.iloc[8][1] and "ПО" in df.iloc[8][1] and "развит" in df.iloc[8][1]):
#                         flag = 1
#                     else:
#                         flag = 0
#
#                     df = df[1:]
#                     df = df.dropna()
#                     df = df.T
#                     df = df.rename(columns=df.iloc[0])
#                     df = df[1:]
#                     cols = pd.Series(df.columns)
#                     for dup in df.columns[df.columns.duplicated(keep=False)]:
#                         cols[df.columns.get_loc(dup)] = ([dup + '.' + str(d_idx)
#                                                           if d_idx != 0
#                                                           else dup
#                                                           for d_idx in range(df.columns.get_loc(dup).sum())]
#                         )
#                     df.columns = cols
#
#                     if flag == 1:
#                         main_po = pd.concat([main_po, df], axis=0)
#                     else:
#                         main_rest = pd.concat([main_rest, df], axis=0)
#             mark = datetime.datetime.now().strftime("%d-%m-%Y(%H-%M)")
#             save_to = os.path.join(path_to_save, "from_bitrix_" + mark + ".xlsx")
#
#             writer = pd.ExcelWriter(save_to, engine='xlsxwriter')
#             if not main_po.empty:
#                 main_po.to_excel(writer, sheet_name='ЦКР', index=False)
#             if not main_rest.empty:
#                 main_rest.to_excel(writer, sheet_name="ИЦК", index=False)
#             writer.close()
#             print(save_to)
#             context.bot.send_document(update.effective_chat.id,open(save_to,"rb"))
#
#         except Exception as e:
#             print(e)
#             context.bot.send_message(chat_id=update.effective_chat.id,
#                                      text="❌ Произошла непредвиденная ошибка:\n"+str(e))
#         shutil.rmtree('temp')
#         context.user_data[get_file] = False
#
# dispatcher.add_handler(CommandHandler('turn_bitrix', get_file))
# updater.dispatcher.add_handler(MessageHandler(Filters.document, downloader))

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