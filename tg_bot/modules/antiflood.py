import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.kick_member(user.id)
        msg.reply_text("Przestań przeskadzać innym futrzakom. Nie jesteś dłużej potrzebny na tej grupie...")

        return "<b>{}:</b>" \
               "\n#ZBANOWANY" \
               "\n<b>Futrzak:</b> {}" \
               "\nSpam na grupie.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("Nie możesz korzystać z tej usługi, dopóki nie dasz mi uprawnień.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFORMACJA" \
               "\nBrak uprawnień do wyrzucania, więc automatycznie wyłączona anty-spam.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("Nie będę już wydalać futrzaków, którzy spamują.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("Nie będę już wydalać futrzaków, którzy spamują.")
                return "<b>{}:</b>" \
                       "\n#ANTY-SPAM" \
                       "\n<b>Administrator:</b> {}" \
                       "\nAnty-spam wyłączony.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 3:
                message.reply_text("Anty-spam musi być ustawiony na 0 (wyłączony), lub o liczbę większą niż 3!")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("Kontrola spamu {} została dodana do wliczania ".format(amount))
                return "<b>{}:</b>" \
                       "\n#ANTY-SPAM" \
                       "\n<b>Administracja:</b> {}" \
                       "\nAnty-spam został ustawiony na <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("Nie rozumię co mówisz. Użyj liczby lub Tak/Nie")

    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("Od teraz nie kontroluję wiadomości!")
    else:
        update.effective_message.reply_text(
            " {} Zostawię niespodziankę futrzakowi który wysyła więcej wiadomości na raz.".format(limit))


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Obecnie *Nie ma* wymuszonej kontroli spamu."
    else:
        return " The message control is set to `{}`.".format(limit)


__help__ = """
 - /flood: Żeby sprawdzić obecny stan kontroli spamu..

*Tylko administracja:*
 - /setflood <int/'no'/'off'>: Włącza lub wyłącza kontrolę spamu
"""

__mod_name__ = "Anty-Spam"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
