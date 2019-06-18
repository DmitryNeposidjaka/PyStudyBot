import telebot
import pymongo
import json
import datetime
from time import sleep
from Task import Task
from bson.objectid import ObjectId
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


task_by_chat = {}
myclient = pymongo.MongoClient("mongodb://mongo:27017/")

mydb = myclient.study
users = mydb.users
tasks = mydb.tasks

bot = telebot.TeleBot("771166532:AAEB_Sa7dQbk8XeNnmeCoWqkPebucqfmKXc")
commands = dict(json.load(open('./config/commands.json')))

admins_list = json.load(open('./config/admins.json'))

menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
menu_board.row(
    KeyboardButton(text='/start ▶️️'),
    KeyboardButton(text='/add ➕'),
    KeyboardButton(text='/delete 🗑')
).row(
    KeyboardButton(text='/users 👥️'),
    KeyboardButton(text='/test 🧾'),
    KeyboardButton(text='/tasks 🔖')
).row(
    KeyboardButton(text='/timer ⏱️'),
    KeyboardButton(text='/contacts ☎️'),
    KeyboardButton(text='/help ❓️')
)

categories_board = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
categories_board.row('Basic', 'OOP', 'Other')

task_menu = ReplyKeyboardMarkup(resize_keyboard=True)
task_menu.row('Stop ✋', 'Next 👉')

approve_menu = ReplyKeyboardMarkup(resize_keyboard=True)
approve_menu.row('Later 👋', 'Denied 👎', 'Approve 👍')

testing_categories = ReplyKeyboardMarkup(resize_keyboard=True)
testing_categories.row('Basic', 'OOP', 'Other', 'All')

tasks_count = ReplyKeyboardMarkup(resize_keyboard=True)
tasks_count.row('Short (5)', 'Middle (15)', 'Long (30)')


def send_to_approve(chat_id, task):
    message = bot.send_message(chat_id, '**{_id}**\n{content}'.format(**task), reply_markup=approve_menu)
    bot.register_next_step_handler(message, register_approved, task)


def register_approved(message, task):
    if message.text == 'Approve 👍':
        tasks.update_one({'_id': ObjectId(task['_id'])}, {'$set': {'approved': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'approved_by': message.from_user.id}})
        bot.send_message(message.chat.id, 'Task {_id} was approved'.format(**task), reply_markup=menu_board)
    elif message.text == 'Denied 👎':
        bot.send_message(message.chat.id, 'Task {_id} was denied'.format(**task), reply_markup=menu_board)
    elif message.text == 'Later 👋':
        bot.send_message(message.chat.id, 'Lets work', reply_markup=menu_board)
    else:
        bot.send_message(message.chat.id, 'Try again')
        send_to_approve(message.chat.id, task)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user.__dict__
        user['is_admin'] = user['id'] in admins_list

        user['chat_id'] = message.chat.id
        x = users.update({'id': user['id']}, user, upsert=True)
        bot.send_message(message.chat.id, 'Your account has been saved!', reply_markup=menu_board)
    except:
        bot.reply_to(message, 'We got problems, try later.')


@bot.message_handler(commands=['users'])
def start_message(message):
    bot.reply_to(message,
                 '\n'.join(
                     map(
                         lambda user: '{username} {last_name} {first_name}'.format(**user), users.find()
                     )
                 )
                 )


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.reply_to(message, commands['help']['data'])


@bot.message_handler(commands=['timer'])
def start_message(message):
    timer = list('🕛🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛💣💥')
    message = bot.send_message(message.chat.id, timer[0])
    for hour in timer[1:]:
        sleep(1)
        bot.edit_message_text(hour, chat_id=message.chat.id, message_id=message.message_id)
    sleep(1)
    bot.send_message(message.chat.id, 'BUSTED', reply_markup=menu_board)


@bot.message_handler(commands=['add'])
def start_message(message):
    task_by_chat[message.chat.id] = Task()
    message = bot.reply_to(message, 'Choose category', reply_markup=categories_board)
    bot.register_next_step_handler(message, set_category)


def set_category(message):
    if message.text in ['Basic', 'OOP', 'Other']:
        task_by_chat[message.chat.id].category = message.text
        message = bot.reply_to(message, 'Set your task')
        bot.register_next_step_handler(message, set_comment)
    else:
        message = bot.reply_to(message, 'Only our variants: Basic, OOP or Other!')
        bot.register_next_step_handler(message, set_category)


def set_comment(message):
    task_by_chat[message.chat.id].content = message.text
    message = bot.reply_to(message, 'Set your comment')
    bot.register_next_step_handler(message, task_finish)


def task_finish(message):
    admins = users.find({"is_admin": True})
    task_by_chat[message.chat.id].comment = message.text
    task_by_chat[message.chat.id].user_id = message.from_user.id
    task = tasks.insert_one(task_by_chat[message.chat.id].to_dict())
    bot.send_message(message.chat.id, 'Your task was created', reply_markup=menu_board)
    for admin in admins:
        send_to_approve(admin['chat_id'], tasks.find_one({'_id': ObjectId(task)}))


@bot.message_handler(commands=['delete'])
def start_message(message):
    message = bot.send_message(message.chat.id, 'Send task id')
    bot.register_next_step_handler(message, deleting_task)


def deleting_task(message):
    if message.text != 'exit':
        try:
            task = tasks.find_one({'_id': ObjectId(message.text)})
            user = users.find_one({'id': message.from_user.id})
            if task is not None and task['user_id'] == user['id'] or user['is_admin'] == True:
                tasks.update_one({'_id': task['_id']},
                                 {'$set': {'deleted': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}})
                bot.reply_to(message, 'Task {_id} was deleted!'.format(**task), reply_markup=menu_board)
            else:
                bot.reply_to(message, 'You have no rights to delete!', reply_markup=menu_board)
        except:
            bot.reply_to(message, 'The id is invalid!', reply_markup=menu_board)
    else:
        bot.send_message(message.chat.id, 'Lets work', reply_markup=menu_board)


@bot.message_handler(commands=['contacts'])
def start_message(message):
    bot.reply_to(message, commands['contacts']['data'], parse_mode='Markdown')


@bot.message_handler(commands=['test'])
def start_message(message):
    message = bot.send_message(message.chat.id, 'Choose category to start testing 📝', reply_markup=testing_categories)
    bot.register_next_step_handler(message, choose_category)


def choose_category(message):
    categories_map = ['Basic', 'OOP', 'Other', 'All']
    category = message.text
    if category in categories_map:
        message = bot.send_message(message.chat.id, 'How match questions do you want?', reply_markup=tasks_count)
        bot.register_next_step_handler(message, start_testing, category)
    else:
        bot.send_message(message.chat.id, 'Only MY variants, you asshole!', reply_markup=testing_categories)
        bot.register_next_step_handler(message, choose_category)


def start_testing(message, category):
    tasks_count_map = {'Short (5)': 5, 'Middle (15)': 5, 'Long (30)': 30}
    categories_map = {
        'Basic': 'Basic',
        'OOP': 'OOP',
        'Other': 'Other',
        'All': {
            "$in": ['OOP', 'Basic', 'Other']
        }
    }
    if message.text in tasks_count_map:
        count = tasks_count_map[message.text]
        tasks_iterator = tasks.find({
            "category": categories_map[category],
            "deleted": False,
            "approved": {"$ne": False}
        }).limit(count)
        message = bot.send_message(message.chat.id, '**{_id}**\n\n{content}'.format(**tasks_iterator.next()), reply_markup=task_menu)
        bot.register_next_step_handler(message, process_task, tasks_iterator)
    else:
        bot.send_message(message.chat.id, 'Only MY variants, you asshole!', reply_markup=tasks_count)
        bot.register_next_step_handler(message, start_testing, category)


def process_task(message, tasks_iterator):
    try:
        if message.text == 'Next 👉':
            message = bot.send_message(message.chat.id, '**{_id}**\n\n{content}'.format(**tasks_iterator.next()), reply_markup=task_menu)
            bot.register_next_step_handler(message, process_task, tasks_iterator)
        elif message.text == 'Stop ✋':
            bot.send_message(message.chat.id, 'Come back later)', reply_markup=menu_board)
        else:
            message = bot.send_message(message.chat.id, '{content}'.format(**tasks_iterator.next()), reply_markup=task_menu)
            bot.register_next_step_handler(message, process_task, tasks_iterator)
    except:
        bot.send_message(message.chat.id, 'Finish!', reply_markup=menu_board)


@bot.message_handler(commands=['tasks'])
def start_message(message):
    if message.from_user.id in admins_list:
        template = 'Id: {_id}\nUser: {user[0][first_name]} {user[0][last_name]}\n{content}'
        tasks_list = tasks.aggregate(
            [{"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "user"}}])
    else:
        template = 'Id: {_id}\n{content}\n\n{comment}'
        tasks_list = tasks.find({"user_id": message.from_user.id})

    bot.send_message(message.chat.id,
                 '\n'.join(
                     map(
                         lambda task: template.format(**task), tasks_list
                     )
                 ), reply_markup=menu_board)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_message(message.chat.id, 'Try functions in menu!', reply_markup=menu_board)


bot.polling()
