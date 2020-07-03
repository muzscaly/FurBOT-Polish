from functools import wraps
from typing import Optional

from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Bot, Update, ParseMode, Message, Chat
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, run_async
    from telegram.utils.helpers import escape_markdown

    from tg_bot import dispatcher, LOGGER
    from tg_bot.modules.helper_funcs.chat_status import user_admin
    from tg_bot.modules.sql import log_channel_sql as sql


    def loggable(func):
        @wraps(func)
        def log_action(bot: Bot, update: Update, *args, **kwargs):
            result = func(bot, update, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]
            if result:
                if chat.type == chat.SUPERGROUP and chat.username:
                    result += "\n<b>Link:</b> " \
                              "<a href=\"http://telegram.me/{}/{}\">kliknij tutaj</a>".format(chat.username,
                                                                                              message.message_id)
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(bot, log_chat, chat.id, result)
            elif result == "":
                pass
            else:
                LOGGER.warning("%s został ustawiony jako loggable, ale nie ma zwrotów.", func)

            return result

        return log_action


    def send_log(bot: Bot, log_chat_id: str, orig_chat_id: str, result: str):
        try:
            bot.send_message(log_chat_id, result, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(orig_chat_id, "Ten log channel został usunięty - unsetting.")
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(log_chat_id, result + "\n\nFormatowanie zostało wyłączone z powodu nieoczekiwanego błędu.")


    @run_async
    @user_admin
    def logging(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                "Wszystkie logi tej grupy zostały wysłane do: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                         log_channel),
                parse_mode=ParseMode.MARKDOWN)

        else:
            message.reply_text("Nie ma żadnego ustawionego log channelu dla tej grupy!")


    @run_async
    @user_admin
    def setlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == chat.CHANNEL:
            message.reply_text("Teraz, prześlij /setlog do grupy którą chcesz podpiąć!")

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("Błąd w usuwaniu wiadomości do log channelu. Powinno działać mimo wszystko.")

            try:
                bot.send_message(message.forward_from_chat.id,
                                 "Ten kanał ma ustawiony log channel dla {}.".format(
                                     chat.title or chat.first_name))
            except Unauthorized as excp:
                if excp.message == "Forbidden: Nie jestem członkiem kanału":
                    bot.send_message(chat.id, "Pomyślnie ustawiono log channel!")
                else:
                    LOGGER.exception("BŁĄD w ustawianiu log channela.")

            bot.send_message(chat.id, "Pomyślnie ustawiono log channel!")

        else:
            message.reply_text("Kroki do ustawienia log channelu są następujące:\n"
                               " - dodaj mnie do wybranego kanału\n"
                               " - wyślij wiadomość /setlog na kanał\n"
                               " - prześlij wiadomość /setlog na grupę\n")


    @run_async
    @user_admin
    def unsetlog(bot: Bot, update: Update):
        message = update.effective_message  # type: Optional[Message]
        chat = update.effective_chat  # type: Optional[Chat]

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(log_channel, "Kanał został odpięty od {}".format(chat.title))
            message.reply_text("Log channel został nieustawiony.")

        else:
            message.reply_text("Nie ma żadnego ustawionego log channelu!")


    def __stats__():
        return "{} ustawionych log channelów.".format(sql.num_logchannels())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return "Wszystkie logi tej grupy zostały wysłane do: {} (`{}`)".format(escape_markdown(log_channel_info.title),
                                                                            log_channel)
        return "Nie ma żadnego ustawionego log channelu dla tej grupy!"


    __help__ = """
*Tylko Administracja:*
- /logchannel: Uzyskaj informację o log channelu
- /setlog: Ustaw log channel.
- /unsetlog: Odustaw log channel.

Ustawienie log channelu jest robione poprzez:
 - dodając mnie do wybranego kanału (jako administrator!)
 - wysyłając wiadomość /setlog na kanał
 - przesyłając wiadomość /setlog na grupę
"""

    __mod_name__ = "Log Channele"

    LOG_HANDLER = CommandHandler("logchannel", logging)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func
