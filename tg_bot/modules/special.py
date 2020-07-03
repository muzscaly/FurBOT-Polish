from io import BytesIO
from time import sleep
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import is_user_ban_protected, bot_admin

import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4


@run_async
def quickscope(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
    try:
        bot.kick_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("Próba zbanowania " + to_kick + " w " + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def quickunban(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
    try:
        bot.unban_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("Próba odbanowania " + to_kick + " w " + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def banall(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[0])
        all_mems = sql.get_chat_members(chat_id)
    else:
        chat_id = str(update.effective_chat.id)
        all_mems = sql.get_chat_members(chat_id)
    for mems in all_mems:
        try:
            bot.kick_chat_member(chat_id, mems.user)
            update.effective_message.reply_text("Próba zbanowania " + str(mems.user))
            sleep(0.1)
        except BadRequest as excp:
            update.effective_message.reply_text(excp.message + " " + str(mems.user))
            continue


@run_async
def snipe(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("Podaj mi czat do którego mam wysłać wiadomość!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Nie można wysłać wiadomości do %s", str(chat_id))
            update.effective_message.reply_text("Nie mogę wysłać wiadomości. Może nie należę do tej grupy?")


@run_async
@bot_admin
def getlink(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        update.effective_message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")
    chat = bot.getChat(chat_id)
    bot_member = chat.get_member(bot.id)
    if bot_member.can_invite_users:
        invitelink = bot.get_chat(chat_id).invite_link
        update.effective_message.reply_text(invitelink)
    else:
        update.effective_message.reply_text("Nie mam dostępu do linku zapraszającego!")


@bot_admin
def leavechat(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
        bot.leaveChat(chat_id)
    else:
        update.effective_message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")

__help__ = """
**Tylko opiekun:**
- /getlink <chatid>: Uzyskiwuje link zaproszenia na podany czat.
- /banall: Banuje wszystkich furzaków czatu.
- /leavechat <chatid> : Opuszcza podany czat.
**Tylko sudo futrzaki oraz opiekun:**
- /quickscope <userid> <chatid>: Banuje futrzaka na podanym czacie.
- /quickunban <userid> <chatid>: Odbanywuje futrzaka na podanym czacie.
- /snipe <chatid> <tekst>: Wysyła wiadomość w moim imieniu na podany czat.
- /rban <userid> <chatid>: Zdalnie banuje futrzaka na podanym czacie.
- /runban <userid> <chatid>: Zdalnie odbanywuje futrzaka na podanym czacie.
- /stats: Wyświetla moje statystyki.
- /chatlist: Wysyła plik z listą czatów na których jestem.
- /gbanlist: Wysyła plik z listą globalnie zbanowanych futrzaków.
- /gmutelist: Wysyła plik z listą globalnie wyciszonych futrzaków.
- /restrict <chatid>: Blokuje dodanie mnie na podany czat.
- /unrestrict <chatid>: Odblokiwuje dodanie mnie na podany czat.
**Tylko futrzaki supportu:**
- /Gban : Globalnie banuje futrzaka.
- /Ungban : Globalnie odbanywuje futrzaka.
- /Gmute : Globalnie wycisza futrzaka.
- /Ungmute : Globalnie odcisza futrzaka.
NOTKA: sudo futrzaki oraz opiekun też mogą używać tych komend.
**Zwykli futrzaki:**
- /listsudo Gives a list of sudo users
- /listsupport gives a list of support users
"""
__mod_name__ = "Komendy specjalne"

SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args=True, filters=CustomFilters.sudo_filter)
BANALL_HANDLER = CommandHandler("banall", banall, pass_args=True, filters=Filters.user(OWNER_ID))
QUICKSCOPE_HANDLER = CommandHandler("quickscope", quickscope, pass_args=True, filters=CustomFilters.sudo_filter)
QUICKUNBAN_HANDLER = CommandHandler("quickunban", quickunban, pass_args=True, filters=CustomFilters.sudo_filter)
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler("leavechat", leavechat, pass_args=True, filters=Filters.user(OWNER_ID))

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANALL_HANDLER)
dispatcher.add_handler(QUICKSCOPE_HANDLER)
dispatcher.add_handler(QUICKUNBAN_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
