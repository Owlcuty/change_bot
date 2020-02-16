import telebot
import requests

from enum import Enum, auto

import datetime as dt
import time
import dateutil.relativedelta as dt_rdelta

from dbase import *
from hstr_plot import *


class Command(Enum):
    LIST = auto()
    EXCHANGE = auto()
    HISTORY = auto()
    END_COMMAND = auto()


def get_data(command, url, params, base, second_cur = ""):
    assert (command < Command.END_COMMAND.value)

    if (Command.LIST.value <= command <= Command.EXCHANGE.value):
        url += f"latest/?base={base}"
        if command == Command.EXCHANGE.value:
            url += f"&symbols={second_cur}"
    elif (command == Command.HISTORY.value):
        assert (second_cur != '')

        end = dt.datetime.now() + dt_rdelta.relativedelta(days = -7)
        url += "history?start_at="  + end.strftime('%Y-%m-%d') \
                    +   "&end_at=" + time.strftime('%Y-%m-%d') \
            + "&base=" + base + "&symbols=" + second_cur

    req = requests.get(url = url, params = params)
    return req.json()

def work_bot(token, url, base, params, filename_bd):
    conn = my_create_connection(filename_bd)
    my_drop_table(conn, "rates_t")
    my_create_table(conn,
            '''CREATE TABLE IF NOT EXISTS rates_t (
                id integer PRIMARY KEY AUTOINCREMENT,
                name text NOT NULL,
                rate real NOT NULL
            );''')

    #  my_drop_table(conn, "time_last")
    my_create_table(conn,
            '''CREATE TABLE IF NOT EXISTS time_last (
                id int UNIQUE,
                time real
            );''')
    my_insert_into(conn, "time_last", "id, time", 2, [(1, 0)])

    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start", "help"])
    def hable_start_help(message):
        chat_id = message.chat.id

        out = "That's change bot\n\n" +\
               "You can control me by these commands:\n\n" +\
               "/list or /lst - listview of rates (are quoted against USD)\n\n" +\
               "/exchange $[num] to [to_currency] or\n/exchange [num] to [from_currency] to [to_currency] - convert num of from_currency to to_currency\n" +\
               "Example: /exchange 10 USD to CAD\n\n" +\
               "/history [first_currency]/[second_currency] - graph of the historical rates against a second_currency\n" +\
               "Example: /hisory USD/CAD"
        bot.send_message(chat_id, out)

    @bot.message_handler(commands=["list", "lst"])
    def handle_list(message):
        now = time.time()
        con_thread = my_create_connection(filename_bd)
        last_time = my_get_data(con_thread, "time_last")[0][1]
        chat_id = message.chat.id
        pnt = "• "

        if now - last_time < 600:
            data = my_get_data(con_thread, "rates_t")
            rates = {el[1]: el[2] for el in data}
        else:
            my_insert_into(con_thread, "time_last", "id, time", 2, [(1, now)])

            data = get_data(Command.LIST.value, url, params, base)
            rates = data['rates']
            to_insert = [(key, value) for key, value in rates.items()]
            my_insert_into(con_thread, "rates_t", "name, rate", 2, to_insert)
        out = ""
        for key, value in rates.items():
            out += pnt + key + ": " + str(round(value, 2)) + '\n'

        bot.send_message(chat_id, out)

    @bot.message_handler(commands=["exchange"])
    def handle_exchange(message):
        chat_id = message.chat.id

        text = message.text.split()
        is_ok = True
        if len(text) == 4:
            if not text[1][1:].isnumeric():
                is_ok = False
            else:
                mul = int(text[1][1:])
                base = 'USD'
                seccur = text[3]
        elif len(text) == 5:
            if not text[1].isnumeric():
                is_ok = False
            else:
                mul = int(text[1])
                base = text[2]
                seccur = text[4]
        else:
            is_ok = False
        if not is_ok:
            bot.send_message(chat_id, "Please, use stamp like '/exchange [num] [from_currency] to [to_currency]' or '/exchange $[num] to [to_currency]'")
            bot.send_message(chat_id, "Examples:\n/exchange $10 to CAD\n/exchange 10 USD to CAD")
            return

        data = get_data(Command.EXCHANGE.value, url, params, base, seccur)
        if "error" in data:
            bot.send_message(chat_id, f"Error: {data['error']}")
            return
        bot.send_message(chat_id, str(round(data['rates'][seccur], 2)) + " " + seccur)

    @bot.message_handler(commands=["history"])
    def handle_history(message):
        chat_id = message.chat.id
        is_ok = True

        text = message.text.split()
        if len(text) != 2:
            is_ok = False
        else:
            curs = text[1].split('/')
            if len(curs) != 2:
                is_ok = Fasle

        if not is_ok:
            bot.send_message(chat_id, "Please, use stamp like '/history [base_currency]/[to_currency]'")
            bot.send_message(chat_id, "Example: /history USD/CAD")
            return

        data = get_data(Command.HISTORY.value, url, params, curs[0], curs[1])
        if "error" in data:
            bot.send_message(chat_id, f"Error: {data['error']}")
            return
        rates = data['rates']
        if not len(rates):
            bot.answer_callback_query(callback_query_id = chat_id,
                                                   text = "No exchange rate data is available for the selected currency")
        else:
            xdata = list(rates.keys())
            ydata = [dct[curs[1]] for dct in rates.values()]
            fig = my_plot(xdata, ydata, "Days", curs[1], "The historical rates against a different currency")
            my_save_plot(fig, "plot.png")
            bot.send_photo(chat_id, open("plot.png", 'rb'))



    while True:
        try:
            bot.polling()
        except Exception as err:
            print("main.py::work_bot:: ", err)
            time.sleep(15)


def main():
    url = "https://api.exchangeratesapi.io/"
    base = "USD"
    location = "European Central Bank"

    params = {'address': location}

    # TELEBOT JOB
    token = "1041297473:AAGonZmv6xDKdhJn-3RmiZCYhkGv7YLQVOE"
    work_bot(token, url, base, params, "tel_rate.db")

    data = get_data(Command.HISTORY.value, url, params, base, 'CAD')








if __name__ == '__main__':
    main()
