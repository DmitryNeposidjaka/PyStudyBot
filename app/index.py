import telebot
import pymongo
import json
from time import sleep


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


menu_board = ReplyKeyboardMarkup(resize_keyboard=True)
menu_board.row(
    KeyboardButton(text='/start ▶️️'),
    KeyboardButton(text='/add ➕')
).row(
    KeyboardButton(text='/users 👥️'),
    KeyboardButton(text='/test 🧾')
).row(
    KeyboardButton(text='/timer ⏱️'),
    KeyboardButton(text='/contacts ☎️'),
    KeyboardButton(text='/help ❓️')
)


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
    bot.send_message(message.chat.id, 'Your task was created', reply_markup=menu_board)


@bot.message_handler(commands=['contacts'])
def start_message(message):
    bot.reply_to(message, commands['contacts']['data'], parse_mode='Markdown')


@bot.message_handler(commands=['test'])
def start_message(message):
    testing_categories = ReplyKeyboardMarkup(resize_keyboard=True)
    testing_categories.row('Basic', 'OOP', 'Other', 'All')
    message = bot.send_message(message.chat.id, 'Choose category to start testing 📝', reply_markup=testing_categories)
    bot.register_next_step_handler(message, choose_category)


def choose_category(message):
    category = message.text
    tasks_count = ReplyKeyboardMarkup(resize_keyboard=True)
    tasks_count.row('Short (5)', 'Middle (15)', 'Long (30)')
    message = bot.send_message(message.chat.id, 'How match questions do you want?', reply_markup=tasks_count)
    bot.register_next_step_handler(message, start_testing, category)


def start_testing(message, category):
    tasks_count_map = {'Short (5)': 5, 'Middle (15)': 5, 'Long (30)': 30}
    if message.text in tasks_count_map:
        count = tasks_count_map[message.text]
        tasks_iterator = tasks.find({"category": category}).limit(count)
        for task in tasks_iterator:
            message = bot.send_message(message.chat.id, '{content}'.format(**task))

        #process_task(message, tasks_iterator)
        #bot.register_next_step_handler(message, process_task, tasks_iterator)

    else:
        bot.send_message(message.chat.id, 'Only MY variants, you asshole!', reply_markup=menu_board)


def process_task(message, tasks_iterator):
    task_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    task_menu.row('Stop ⏹', 'Next ▶️️')
    if message.text is 'Next ▶️️':
        try:
            message = bot.send_message(message.chat.id, '{content}'.format(**tasks_iterator.next()), reply_markup=task_menu)
            bot.register_next_step_handler(message, process_task, tasks_iterator)
        except:
            bot.send_message(message.chat.id, 'Finish!', reply_markup=menu_board)
    elif message.text is 'Stop ⏹':
        bot.send_message(message.chat.id, 'Come back later)', reply_markup=menu_board)


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
    bot.send_message(message.chat.id, 'Try functions in menu!', reply_markup=menu_board)


bot.polling()
