import telebot
import config
import pydantic_models
import client
import json

from math import ceil


bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=['start'])
def start_message(message):
    print(f'/start message.from_user.full_name: {message.from_user.full_name}')
    print(message.from_user.to_dict())
    username = message.from_user.username if message.from_user.username else message.from_user.full_name
    pydantic_user_create = pydantic_models.UserToCreate.validate({'tg_ID': message.from_user.id, 'nick': username})
    try:
        client.create_user(pydantic_user_create)
    except Exception as ex:
        # bot.send_message(message.chat.id, f'Возникла ошибка: {ex.args}')
        pass

    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)

    btn1 = telebot.types.KeyboardButton('Кошелек')
    btn2 = telebot.types.KeyboardButton('Перевести')
    btn3 = telebot.types.KeyboardButton('История')

    markup.add(btn1, btn2, btn3)

    text = f'Привет, {message.from_user.full_name}, я - твой бот-криптокошелек,\nу меня ты можешь хранить и отправлять биткоины.'

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Кошелек')
def wallet(message):
    wallet_client = client.get_user_wallet_by_tg_id(message.from_user.id)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Ваш баланс: {wallet_client["balance"] / 100000000} BTC\nВаш адрес: {wallet_client["address"]}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='История')
def history(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    transactions = client.get_user_transactions(client.get_user_by_tg_id(message.from_user.id)['id'])
    text = f'Ваши транзакции:\nОтправленные: {transactions[0]}\nПолученные: {transactions[1]}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Меню')
def menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Кошелек')
    btn2 = telebot.types.KeyboardButton('Перевести')
    btn3 = telebot.types.KeyboardButton('История')
    markup.add(btn1, btn2, btn3)
    text = f'Главное меню'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(regexp='Я в консоли')
def print_me(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    print(message.from_user.to_dict())
    text = f'Ты: {message.from_user.to_dict()}'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id == int(config.tg_admin_id) and message.text == 'Админка')
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Общий баланс')
    btn2 = telebot.types.KeyboardButton('Все юзеры')
    btn3 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1, btn2, btn3)
    text = f'Админ панель'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id == int(config.tg_admin_id) and message.text == 'Все юзеры')
def all_users(message):
    print(f'message from all_users: {message}')
    text = f'Юзеры: '
    users = client.get_users()
    print(type(users), users)
    inline_markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    for idx, user in enumerate(users):
        if idx == 4:
            break
        inline_markup.add(telebot.types.InlineKeyboardButton(
            text=f'Юзер {user["nick"]}',
            callback_data=f'user_{user["tg_ID"]}'))

    btn_pages = telebot.types.InlineKeyboardButton(
        text=f'1 / {ceil(len(users) / 4)}',
        callback_data=f'pages'
    )
    btn_forward = telebot.types.InlineKeyboardButton(
        text=f'Вперед',
        callback_data=f'users_4'
    )
    inline_markup.add(btn_pages, btn_forward)

    bot.send_message(message.chat.id, text, reply_markup=inline_markup)


@bot.message_handler(func=lambda message: message.from_user.id == int(config.tg_admin_id) and message.text == 'Общий баланс')
def total_balance(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    btn2 = telebot.types.KeyboardButton('Админка')
    markup.add(btn1, btn2)
    balance = client.get_total_balance()
    text = f'Общий баланс: {balance / 100000000} BTC'
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    query_type = call.data.split('_')[0]
    users = client.get_users()
    print(query_type)
    print(f'call.data: {call.data}')
    if query_type == 'user':
        user_id = call.data.split('_')[1]
        inline_markup = telebot.types.InlineKeyboardMarkup()
        for user in users:
            if str(user['tg_ID']) == user_id:
                inline_markup.add(
                    telebot.types.InlineKeyboardButton(text='Назад', callback_data='users_0'),
                    telebot.types.InlineKeyboardButton(text='Удалить юзера', callback_data=f'delete_user_{user_id}')
                )
                bot.edit_message_text(
                    text=f'Данные по юзеру:\n'
                    f'ID: {user["tg_ID"]}\n'
                    f'Ник: {user["nick"]}\n'
                    f'Баланс: {client.get_user_balance_by_id(user["id"])}',
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=inline_markup
                )
                print(f'Запрошен: {user}')
                break

    if query_type == 'users':
        inline_markup = telebot.types.InlineKeyboardMarkup()
        users_count = int(call.data.split('_')[1])
        counts = int(call.data.split('_')[1])
        for user in users[users_count:users_count + 4]:
            counts += 1
            inline_markup.add(telebot.types.InlineKeyboardButton(
                text=f'Юзер: {user["nick"]}',
                callback_data=f'user_{user["tg_ID"]}'
            ))

        btn_pages = telebot.types.InlineKeyboardButton(
            text=f'{ceil(counts / 4)} / {ceil(len(users) / 4)}',
            callback_data='pages'
        )
        btn_back = telebot.types.InlineKeyboardButton(
            text='Назад',
            callback_data=f'users_{users_count-4}'
        )
        btn_forward = telebot.types.InlineKeyboardButton(
            text='Вперед',
            callback_data=f'users_{counts}'
        )
        if users_count == 0:
            inline_markup.add(btn_pages, btn_forward)
        elif counts - users_count != 4:
            inline_markup.add(btn_back, btn_pages)
        else:
            inline_markup.add(btn_back, btn_pages, btn_forward)

        bot.edit_message_text(
            text=f'Юзеры: ',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=inline_markup
        )

    if query_type == 'delete' and call.data.split('_')[1] == 'user':
        user_id = int(call.data.split('_')[2])
        user = None
        for i, user in enumerate(users):
            if user['tg_ID'] == user_id:
                print(f'Удален юзер {users[i]}')
                user = users.pop(i)
                client.delete_user(user['id'])
                break
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton('Общий баланс')
        btn2 = telebot.types.KeyboardButton('Все юзеры')
        btn3 = telebot.types.KeyboardButton('Данные по юзеру')
        btn4 = telebot.types.KeyboardButton('Удалить юзера')
        markup.add(btn1, btn2, btn3, btn4)
        text = f'Пользователь {user["nick"]} успешно удален!'
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


states_list = ['ADDRESS', 'AMOUNT', 'CONFIRM']
states_of_users = {}


@bot.message_handler(regexp='Перевести')
def transaction(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Введите адрес кошелька, куда хотите перевести: '
    bot.send_message(message.chat.id, text, reply_markup=markup)
    states_of_users[message.from_user.id] = {'STATE': 'ADDRESS'}


@bot.message_handler(func=lambda message: states_of_users.get(message.from_user.id)['STATE'] == 'ADDRESS')
def get_amount_of_transaction(message):
    if message.text == 'Меню':
        del states_of_users[message.from_user.id]
        menu(message)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Введите сумму в сатоши, которую хотите перевести:'
    bot.send_message(message.chat.id, text, reply_markup=markup)
    states_of_users[message.from_user.id]['STATE'] = 'AMOUNT'
    states_of_users[message.from_user.id]['ADDRESS'] = message.text


@bot.message_handler(func=lambda message: states_of_users.get(message.from_user.id)['STATE'] == 'AMOUNT')
def get_confirmation_of_transaction(message):
    print(states_of_users)
    if message.text == 'Меню':
        del states_of_users[message.from_user.id]
        menu(message)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('Меню')
    markup.add(btn1)
    if message.text.isdigit():
        text = f'Вы хотите перевести {message.text} сатоши,\nна биткоин адресс {states_of_users[message.from_user.id]["ADDRESS"]:}'
        confirm_btn = telebot.types.KeyboardButton('Подтверждаю')
        markup.add(confirm_btn)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        states_of_users[message.from_user.id]['STATE'] = 'CONFIRM'
        states_of_users[message.from_user.id]['AMOUNT'] = int(message.text)
    else:
        text = f'Вы ввели не число {message.text}, попробуйте еще раз'
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(func=lambda message: states_of_users.get(message.from_user.id)['STATE'] == 'CONFIRM')
def get_hash_of_transaction(message):
    if message.text == 'Меню':
        del states_of_users[message.from_user.id]
        menu(message)
    elif message.text == 'Подтверждаю':
        text = f'Ваша транзакция: ' + str(client.create_transaction(message.from_user.id, states_of_users[message.from_user.id]['ADDRESS'], states_of_users[message.from_user.id]['AMOUNT']))
        bot.send_message(message.chat.id, text)
        del states_of_users[message.from_user.id]
        menu(message)


bot.infinity_polling()
