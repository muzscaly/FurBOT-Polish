import html
from typing import Optional, List

from telegram import Message, Update, Bot, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.userinfo_sql as sql
from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user


@run_async
def about_me(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(username + "Informacje o tym futrzaku są obecnie niedostępne!")
    else:
        update.effective_message.reply_text("Nie dodałeś jeszcze żadnych informacji o sobie!")


@run_async
def set_about_me(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    text = message.text
    info = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            message.reply_text("Twoje informacje zostały pomyślnie zapisane")
        else:
            message.reply_text(
                "O tobie powinien ograniczać się do {} liter".format(MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
def about_bio(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text("{} Nie dodano jeszcze żadnych szczegółów na temat tego futrzaka!".format(username))
    else:
        update.effective_message.reply_text("Twoje informacje o tobie zostały dodane!")


@run_async
def set_about_bio(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    sender = update.effective_user  # type: Optional[User]
    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id == message.from_user.id:
            message.reply_text("Czy chcesz zmienić swój własny...?? OK...")
            return
        elif user_id == bot.id and sender.id not in SUDO_USERS:
            message.reply_text("Tylko SUDO FUTRZAKI mogą zmieniać moje informacje.")
            return

        text = message.text
        bio = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("{} Informacje o tym futrzaku zostały pomyślnie zebrane!".format(repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "O tobie powinien ograniczać się do {} liter! Liczba właśnie wpisanych znaków {}.".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Jego informacje można dodać tylko, jeśli czyjaś WIADOMOŚĆ jest jako ODPOWIEDŹ")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return "<b>O futrzaku:</b>\n{me}\n<b>Co inne futrzaki mówią:</b>\n{bio}".format(me=me, bio=bio)
    elif bio:
        return "<b>Co inne futrzaki mówią:</b>\n{bio}\n".format(me=me, bio=bio)
    elif me:
        return "<b>O futrzaku:</b>\n{me}""".format(me=me, bio=bio)
    else:
        return ""


__help__ = """
 - /setbio <tekst>: W odpowiedzi, zapisze biografię innego futrzaka.
 - /bio: Wysyła biografię o tobie lub innego futrzaka. Nie możesz tego ustawić samodzielnie.
 - /setme <tekst>: Ustawia twoje informacje.
 - /me: Wysyła informacje o tobie lub innego futrzaka.
"""

__mod_name__ = "Biografie i Informacje"

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio, pass_args=True)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me, pass_args=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)
