import logging

from telegram import TelegramError, ParseMode
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

import config

logger = logging.getLogger('main')


def spam(bot, ids, msg, parse_mode=None, **kwargs):
    logger.info('Spam to admins')
    for id in ids:
        try:
            bot.send_message(id, msg, parse_mode=parse_mode, **kwargs)
        except TelegramError as e:
            logger.info('TelegramError: send message to {}, {}'.format(id, e), exc_info=True)


def forward_message_to_admins(bot, message):
    for admin_chat_id in config.ADMINS_ID:
        try:
            bot.forward_message(admin_chat_id, message.chat_id, message.message_id)
        except TelegramError as e:
            logger.info('TelegramError: forward message to admin {}, {}'.format(admin_chat_id, e), exc_info=True)


def get_message_info(message):
    if message.forward_from:
        return message.forward_from.id, None
    # text should be "User 123456 send message 123"
    splitted = (message.text or '').split()
    return int(splitted[1]), int(splitted[4])


def reply(bot, update):
    message = update.message
    if message is None:
        return

    if message.chat_id not in config.ADMINS_ID:
        spam(bot, config.ADMINS_ID, "User {} send message {}".format(message.chat_id, message.message_id))
        forward_message_to_admins(bot, message)
    else:
        if message.reply_to_message:
            try:
                reply_chat_id, reply_to_message_id = get_message_info(message.reply_to_message)
                try:
                    bot.send_message(reply_chat_id, message.text, reply_to_message_id=reply_to_message_id)
                except TelegramError as t_e:
                    try:
                        message.reply_text('TelegramError: {}'.format(t_e))
                    except TelegramError as e:
                        logger.info('TelegramError: {}'.format(e), exc_info=True)

                spam(bot,
                     config.ADMINS_ID - {message.chat_id},
                     config.ADMIN_ANSWER.format(message.reply_to_message.forward_from.first_name or '',
                                                message.reply_to_message.forward_from.last_name or '',
                                                message.reply_to_message.text,
                                                message.from_user.first_name or '',
                                                message.from_user.last_name or '',
                                                message.text),
                     ParseMode.HTML)
            except ValueError:
                message.reply_text("Stupid admin, it's not forward")
        else:
            message.reply_text('Admin, reply something!')


if __name__ == '__main__':
    logging.basicConfig(format="%(name)s -- [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s",
                        level=logging.DEBUG)

    updater = Updater(token=config.BOT_TOKEN)
    dispatcher = updater.dispatcher
    updater.dispatcher.add_handler(MessageHandler(Filters.all & (~ Filters.command), reply))

    updater.start_polling(read_latency=4., bootstrap_retries=3)  # start bot
    updater.idle()
