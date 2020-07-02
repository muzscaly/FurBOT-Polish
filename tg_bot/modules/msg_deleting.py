import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, can_delete
from tg_bot.modules.log_channel import loggable


@run_async
@user_admin
@loggable
def purge(bot: Bot, update: Update, args: List[str]) -> str:
    msg = update.effective_message  # type: Optional[Message]
    if msg.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            message_id = msg.reply_to_message.message_id
            if args and args[0].isdigit():
                delete_to = message_id + int(args[0])
            else:
                delete_to = msg.message_id - 1
            for m_id in range(delete_to, message_id - 1, -1):  # Reverse iteration over message ids
                try:
                    bot.deleteMessage(chat.id, m_id)
                except BadRequest as err:
                    if err.message == "Message can't be deleted":
                        bot.send_message(chat.id, "Nie można usunąć wszystkich wiadomości. Wiadomości mogą być zbyt stare, Mogę "
                                                  "nie mieć uprawnień do usuwania, lub czat nie jest supergrupą.")

                    elif err.message != "Message to delete not found":
                        LOGGER.exception("Błąd podczas czyszczenia wiadomości czatu.")

            try:
                msg.delete()
            except BadRequest as err:
                if err.message == "Message can't be deleted":
                    bot.send_message(chat.id, "Nie można usunąć wszystkich wiadomości. Wiadomości mogą być zbyt stare, Mogę "
                                              "nie mieć uprawnień do usuwania, lub czat nie jest supergrupą.")

                elif err.message != "Message to delete not found":
                    LOGGER.exception("Błąd podczas czyszczenia wiadomości czatu.")

            return "<b>{}:</b>" \
                   "\n#CZYSZCZENIE" \
                   "\n<b>Administrator:</b> {}" \
                   "\nWyczyszczono <code>{}</code> wiadomości.".format(html.escape(chat.title),
                                                                       mention_html(user.id, user.first_name),
                                                                       delete_to - message_id)

    else:
        msg.reply_text("Wybierz początek czyszczenia wiadomości w dół poprzez odpowiedzenie na najstarszą wiadomość.")

    return ""


@run_async
@user_admin
@loggable
def del_message(bot: Bot, update: Update) -> str:
    if update.effective_message.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            update.effective_message.reply_to_message.delete()
            update.effective_message.delete()
            return "<b>{}:</b>" \
                   "\n#USUWANIE" \
                   "\n<b>Administrator:</b> {}" \
                   "\nWiadomość usunięta.".format(html.escape(chat.title),
                                                  mention_html(user.id, user.first_name))
    else:
        update.effective_message.reply_text("Co ty chcesz usunąć?")

    return ""


__help__ = """
*Tylko Administracja:*
 - /del: Usuwa wiadomość na którą odpowiedziałeś
 - /purge: Usuwa wszystkie wiadomości w dół od tej na którą odpowiedziałeś.
 - /purge <liczba>: Usuwa wiadomość na którą odpowiedziałeś oraz X następnych.
"""

__mod_name__ = "Czyszczenie"

DELETE_HANDLER = CommandHandler("del", del_message, filters=Filters.group)
PURGE_HANDLER = CommandHandler("purge", purge, filters=Filters.group, pass_args=True)

dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PURGE_HANDLER)
