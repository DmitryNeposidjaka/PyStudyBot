import telebot
import pymongo
import json
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

task_by_chat = {}
myclient = pymongo.MongoClient("mongodb://mongo:27017/")

mydb = myclient.study
collection = mydb.users
tasks = mydb.tasks

bot = telebot.TeleBot("771166532:AAEB_Sa7dQbk8XeNnmeCoWqkPebucqfmKXc")
commands = dict(json.load(open('./config/commands.json')))


class Task:
    category = ''
    content = ''
    comment = ''
    user_id = ''

    def to_dict(self):
        return self.__dict__


@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user.__dict__
        x = collection.update({'id': user['id']}, user, upsert=True)
        bot.reply_to(message, 'Your account has been saved!')
    except:
        bot.reply_to(message, 'We got problems, try later.')


@bot.message_handler(commands=['users'])
def start_message(message):
    bot.reply_to(message,
                 '\n'.join(
                     map(
                         lambda user: '{username} {last_name} {first_name}'.format(**user), collection.find()
                     )
                 )
                 )


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.reply_to(message, commands['help']['data'])


@bot.message_handler(commands=['add'])
def start_message(message):
    task_by_chat[message.chat.id] = Task()
    categories_board = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    categories_board.row('Basic', 'OOP', 'Other')
    message = bot.reply_to(message, 'Choose category', reply_markup=categories_board)
    bot.register_next_step_handler(message, set_category)


def set_category(message):
    task_by_chat[message.chat.id].category = message.text
    message = bot.reply_to(message, 'Set your task')
    bot.register_next_step_handler(message, set_comment)


def set_comment(message):
    task_by_chat[message.chat.id].content = message.text
    message = bot.reply_to(message, 'Set your comment')
    bot.register_next_step_handler(message, task_finish)


def task_finish(message):
    task_by_chat[message.chat.id].comment = message.text
    task_by_chat[message.chat.id].user_id = message.from_user.id
    tasks.insert(task_by_chat[message.chat.id].to_dict())
    bot.reply_to(message, 'Your task was created')


@bot.message_handler(commands=['contacts'])
def start_message(message):
    bot.reply_to(message, commands['contacts']['data'], parse_mode='Markdown')


@bot.message_handler(commands=['tasks'])
def start_message(message):
    bot.reply_to(message,
                 '\n'.join(
                     map(
                         lambda task: 'User: {user[0][first_name]} {user[0][last_name]}\n{content}'.format(**task), tasks.aggregate([{"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "user"}}])
                     )
                 )
                 )


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
    menu_board.row(
        KeyboardButton(text='/start ▶️️'),
        KeyboardButton(text='/users 👥️'),
        KeyboardButton(text='/add ➕'),
        KeyboardButton(text='/contacts ☎️'),
        KeyboardButton(text='/help ❓️')
    )
    bot.send_message(message.chat.id, 'Try functions in menu!', reply_markup=menu_board)


bot.polling()
