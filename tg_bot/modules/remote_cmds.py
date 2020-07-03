import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "Futrzak jest administratorem chatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Peer_id_invalid",
    "Czat grupy został zdeaktywowany",
    "Trzeba być zapraszającym futrzaka, aby zbanować go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może zbanować administratorów grupy",
    "Channel_private",
    "Nie na czacie"
}

RUNBAN_ERRORS = {
    "Futrzak jest administratorem chatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Peer_id_invalid",
    "Czat grupy został zdeaktywowany",
    "Trzeba być zapraszającym futrzaka, aby odbanować go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może odbanowywać administratorów grupy",
    "Channel_private",
    "Nie na czacie"
}

RKICK_ERRORS = {
    "Futrzak jest administratorem chatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Peer_id_invalid",
    "Czat grupy został zdeaktywowany",
    "Trzeba być zapraszającym futrzaka, aby wyrzucić go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może wyrzucać administratorów grupy",
    "Channel_private",
    "Nie na czacie"
}

RMUTE_ERRORS = {
    "Futrzak jest administratorem chatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Peer_id_invalid",
    "Czat grupy został zdeaktywowany",
    "Trzeba być zapraszającym futrzaka, aby wyciszyć go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może wyciszać administratorów grupy",
    "Channel_private",
    "Nie na czacie"
}

RUNMUTE_ERRORS = {
    "Futrzak jest administratorem chatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Peer_id_invalid",
    "Czat grupy został zdeaktywowany",
    "Trzeba być zapraszającym futrzaka, aby odciszyć go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może odciszać administratorów grupy",
    "Channel_private",
    "Nie na czacie"
}

@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return
    elif not chat_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Przepraszam, ale to jest prywatny czat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Nie mogę tutaj ograniczać futrzaków! Sprawdź czy mam prawa administratora i czy mogę banować.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
        return

    if user_id == bot.id:
        message.reply_text("Nie zamierzam BANOWAĆ siebie, oszalałeś?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Zbanowano na tym czacie!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Zbanowano!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas banowania futrzaka %s na chacie %s (%s) z powodu %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę zbanować tego futrzaka.")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return
    elif not chat_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Przepraszam, ale to jest prywatny czat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Nie mogę tutaj odograniczać futrzaków! Sprawdź czy mam prawa administratora i czy mogę odbanowywać.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("Dlaczego próbujesz zdalnie futrzaka który jest już na chacie?")
        return

    if user_id == bot.id:
        message.reply_text("Nie będę ODBANOWYWAŁ siebie, jestem tutaj administratorem!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Yup, ten futrzak może wrócić!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Odbanowany!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas odbanowania futrzaka %s na chacie %s (%s) z powodu %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę odbanować tego futrzaka.")

@run_async
@bot_admin
def rkick(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return
    elif not chat_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Przepraszam, ale to jest prywatny czat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Nie mogę tutaj odograniczać futrzaków! Sprawdź czy mam prawa administratora i czy mogę wyrzucać.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Naprawdę chciałbym móc wyrzucać administratorów...")
        return

    if user_id == bot.id:
        message.reply_text("Tjaaa... Nie zrobię tego")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Wyrzucono z czatu!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Wyrzucono!', quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas wyrzucania futrzaka %s na chacie %s (%s) z powodu %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę wyrzucić tego futrzaka.")

@run_async
@bot_admin
def rmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return
    elif not chat_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Przepraszam, ale to jest prywatny czat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Nie mogę tutaj odograniczać futrzaków! Sprawdź czy mam prawa administratora i czy mogę wyciszać.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Naprawdę chciałbym móc wyciszać administratorów...")
        return

    if user_id == bot.id:
        message.reply_text("Nie zamierzam WYCISZAĆ siebie, oszalałeś?")
        return

    try:
        bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
        message.reply_text("Wyciszony na czacie!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Muted!', quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas wyciszania futrzaka %s (%s) przez %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę wyciszyć tego futrzaka.")

@run_async
@bot_admin
def runmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu/futrzaka.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return
    elif not chat_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do czatu.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Przepraszam, ale to jest prywatny czat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Nie mogę tutaj odograniczać futrzaków! Sprawdź czy mam prawa administratora i czy mogę odciszać.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
       if member.can_send_messages and member.can_send_media_messages \
          and member.can_send_other_messages and member.can_add_web_page_previews:
        message.reply_text("Ten futrzak ma już prawo do mówienia na tym czacie.")
        return

    if user_id == bot.id:
        message.reply_text("Nie będę ODCISZAŁ siebie, jestem tutaj administratorem!")
        return

    try:
        bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
        message.reply_text("Yup, ten futrzak może mówić na tym czacie!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Odciszony!', quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas odciszania futrzaka %s (%s) przez %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę odciszyć tego futrzaka.")

__help__ = ""

__mod_name__ = "Zdalne komendy"

RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)
RKICK_HANDLER = CommandHandler("rkick", rkick, pass_args=True, filters=CustomFilters.sudo_filter)
RMUTE_HANDLER = CommandHandler("rmute", rmute, pass_args=True, filters=CustomFilters.sudo_filter)
RUNMUTE_HANDLER = CommandHandler("runmute", runmute, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
