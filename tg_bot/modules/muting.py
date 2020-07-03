import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@user_admin
@loggable
def mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Musisz mi podać nazwę futrzaka lub odpowiedzieć na jego wiadomość żeby go wyciszyć.")
        return ""

    if user_id == bot.id:
        message.reply_text("Nie wyciszę samego siebie!")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Wydaje mi się że nie mogę wyciszyć administracji!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
            message.reply_text("👍🏻 wyciszony! 🤐")
            return "<b>{}:</b>" \
                   "\n#WYCISZENIE" \
                   "\n<b>Administrator:</b> {}" \
                   "\n<b>Futrzak:</b> {}".format(html.escape(chat.title),
                                                 mention_html(user.id, user.first_name),
                                                 mention_html(member.user.id, member.user.first_name))

        else:
            message.reply_text("Ten futrzak jest już wyciszony!")
    else:
        message.reply_text("Tego futrzaka nie ma na czacie!")

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def unmute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Musisz mi podać nazwę futrzaka lub odpowiedzieć na jego wiadomość żeby go odciszyć.")
        return ""

    member = chat.get_member(int(user_id))

    if member.status != 'kicked' and member.status != 'left':
        if member.can_send_messages and member.can_send_media_messages \
                and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text("Ten futrzak ma już prawo do mówienia.")
        else:
            bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
            message.reply_text("Odciszony!")
            return "<b>{}:</b>" \
                   "\n#ODCISZENIE" \
                   "\n<b>Administrator:</b> {}" \
                   "\n<b>Futrzak:</b> {}".format(html.escape(chat.title),
                                                 mention_html(user.id, user.first_name),
                                                 mention_html(member.user.id, member.user.first_name))
    else:
        message.reply_text("Tego futrzaka i tak nie ma na czacie. Odciszenie go nie spowoduje że zacznie mówić "
                           "jak wcześniej!")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return ""
        else:
            raise

    if is_user_admin(chat, user_id, member):
        message.reply_text("Naprawdę chciałbym móc wyciszać administratorów...")
        return ""

    if user_id == bot.id:
        message.reply_text("Nie zamierzam WYCISZAĆ siebie, oszalałeś?")
        return ""

    if not reason:
        message.reply_text("Nie podałeś długości wyciszenia dla tego futrzaka!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TYMCZASOWO WYCISZONY" \
          "\n<b>Administrator:</b> {}" \
          "\n<b>Futrzak:</b> {}" \
          "\n<b>Długość:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                        mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Powód:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=False)
            message.reply_text("Zamknij się! 😠 Wyciszony na {}!".format(time_val))
            return log
        else:
            message.reply_text("Ten futrzak jest już wyciszony.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Zamknij się! 😠 Wyciszony na {}!".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas wyciszania futrzaka %s (%s) przez %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę wyciszyć tego futrzaka.")

    return ""


__help__ = """
*Tylko Administracja:*
 - /mute <nazwa futrzaka>: Ucisza futrzaka. (poprzez @, lub odpowiedź)
 - /tmute <nazwa futrzaka> x(m/g/d): Wycisza futrzaka przez podaną ilość czasu. (poprzez @, lub odpowiedź). m = minuty, g = godziny, d = dni.
 - /unmute <nazwa futrzaka>: Odczisza futrzaka. (poprzez @, lub odpowiedź)
"""

__mod_name__ = "Mute"

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True, filters=Filters.group)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True, filters=Filters.group)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, pass_args=True, filters=Filters.group)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
