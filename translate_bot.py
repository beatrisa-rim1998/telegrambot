

import logging, random

from database import (create_database, update_leaderboard, get_leaderboard, get_user_record,
        get_categories, get_words)


from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


START_MENU, GAMETYPE, THEME, LEADERBOARD, MENU = range(5)
WORDS_FILE = 'words.txt'

print('Checking/creating database...')
if create_database(WORDS_FILE):
    print('OK!')
else:
    print('Not OK! Shutting down...')
    raise

def start(update, context):
    new_user = update_leaderboard(update, 0)
    reply_keyboard_start = [['Играть'],
                            ['Рекорды']]

    msg = ''
    if new_user:
        msg += 'Привет! В этой игре ты сможешь проверить своё знание английского языка. '
    else:
        msg += 'Рад видеть тебя снова! '
    msg += 'Отправь /cancel если хочешь закончить разговор.\n\nПоехали? :)\n'
    update.message.reply_text(msg,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard_start, one_time_keyboard=True))

    return START_MENU

def menu(update, context):
    reply_keyboard_menu = [['Играть'],
                           ['Рекорды']]
    update.message.reply_text(
        'Играем?\n'
        'Отправь /cancel если хочешь закончить разговор.\n\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard_menu, one_time_keyboard=True))
    return START_MENU

def leaderboard(update, context):
    # print leaderboard
    leaderboard = get_leaderboard()
    lb_list = [(str(i + 1) + '. ' + str(record[2]) + ' - ' + str(record[3]) + '\n') for i, record in enumerate(leaderboard)]

    reply_keyboard_leaderboard = [['Назад']]
    update.message.reply_text('Текущие рекорды:\n' + ''.join(lb_list), reply_markup=ReplyKeyboardMarkup(reply_keyboard_leaderboard, one_time_keyboard=True))
    return MENU

def gametype(update, context):
    reply_keyboard_gametype = [['Случайная тема']] + get_categories()
            
    update.message.reply_text(
            'Отлично! Правила просты: ты получаешь слово на английском и варианты его перевода на русский. Если выбираешь правильный - получаешь балл. Ошибаешься - игра окончена.\n\n'
            'Слова, которые я предлагаю, разбиты по темам. Выбирай!\n\n',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard_gametype, one_time_keyboard=True))

    return THEME


def game(update, context):
    msg = ''
    user_data = context.user_data
    if not 'category' in user_data:
        # New game
        category = update.message.text
        random_theme = False
        if category == 'Случайная тема':
            random_theme = True
        words, category = get_words(category)
        if random_theme:
            update.message.reply_text('Выбрана случайная тема "{}".\n\n'.format(category))
        random.shuffle(words)
    
        user_data['category'] = category
        user_data['words'] = words
        user_data['score'] = 0
        user_data['cur_index'] = 0
    else:
        # Continuing game
        if update.message.text == user_data['answer']:
            user_data['score'] += 1
            user_data['cur_index'] += 1
            update.message.reply_text('Верно! Ты заработал {} очков.\n'.format(user_data['score']))
            if user_data['cur_index'] >= len(user_data['words']):
                msg += 'Поздравляю, ты верно ответил весь раздел "{}"!\n'.format(user_data['category'])

                new_record = update_leaderboard(update, user_data['score'])
                if new_record:
                    msg += 'Это твой новый рекорд, поздравляю!\n'

                user_data.clear()

                msg += '\nУ тебя неплохо получается, попробуй себя в других разделах!\n'

                reply_keyboard_back = [['Меню']]
                update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(reply_keyboard_back, one_time_keyboard=True))
                return THEME
        else:
            reply_keyboard_back = [['Меню']]

            msg += 'Ошибка! Твой результат - {}.\n'.format(user_data['score'])
            max_score = get_user_record(update.message.from_user.id)
            new_record = update_leaderboard(update, user_data['score'])
            if new_record:
                msg += 'Это твой новый рекорд, поздравляю!'
            msg += '\nПопробуем ещё раз? Уверен, сейчас тебе повезёт сильнее!\n'
            
            user_data.clear()

            update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(reply_keyboard_back, one_time_keyboard=True))
            context.user_data.update(user_data)
            return THEME

    index = user_data['cur_index']
    words = user_data['words']
    word = words[index]
    msg += '\nКак переводится "{}"?\n'.format(word[0])
    sample = words[:index] + words[index + 1:]
    sample = random.sample(sample, k=3)

    reply_keyboard_choice = [[word[1]]] + [[pair[1]] for pair in sample]
    random.shuffle(reply_keyboard_choice)

    user_data['answer'] = word[1]
    update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(reply_keyboard_choice, one_time_keyboard=True))

    context.user_data.update(user_data)
    return THEME
            
            
def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Пока! Надеюсь, ты ещё вернёшься.\n',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    REQUEST_KWARGS={
        #'proxy_url': 'socks5://144.202.74.97:443/',
        #'proxy_url': 'socks5://72.11.148.222:56533/',
    }
    updater = Updater("833799448:AAHSOljNCa8mAkJfs_f-cw3bYHxRDArViJA", use_context=True, request_kwargs=REQUEST_KWARGS)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states = {
            START_MENU: [MessageHandler(Filters.regex('^(Играть)$'), gametype),
                         MessageHandler(Filters.regex('^(Рекорды)$'), leaderboard)],

            MENU: [MessageHandler(Filters.regex('^(Назад)$'), menu)],

            THEME: [MessageHandler(Filters.regex('^(Меню)$'), menu),
                    MessageHandler(Filters.text, game, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()


    updater.idle()


if __name__ == '__main__':
    main()

