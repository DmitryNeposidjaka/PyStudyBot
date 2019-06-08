import telebot
import pymongo
import json

myclient = pymongo.MongoClient("mongodb://mongo:27017/")

mydb = myclient.study
collection = mydb.users

bot = telebot.TeleBot("771166532:AAEB_Sa7dQbk8XeNnmeCoWqkPebucqfmKXc")
commands = dict(json.load(open('./config/commands.json')))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user.__dict__
        x = collection.update({'id': user['id']}, user, upsert=True)
    except:
        bot.reply_to(message, 'We got problems, try later.')

    bot.reply_to(message, 'Your account has been saved!')

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

@bot.message_handler(commands=['contacts'])
def start_message(message):
    bot.reply_to(message, commands['contacts']['data'], parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
        bot.reply_to(message, message.text)

bot.polling()
