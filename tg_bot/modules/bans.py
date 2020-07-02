import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "Futrzak jest administratorem chatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Peer_id_invalid",
    "Czat grupy został zdeaktywowany",
    "Trzeba być zapraszającym futrzaka, aby wyrzucić go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może wyrzucić administratorów grupy",
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
    "Trzeba być zapraszającym futrzaka, aby wyrzucić go z grupy",
    "Chat_admin_required",
    "Tylko twórca grupy może wyrzucić administratorów grupy",
    "Channel_private",
    "Nie jest na czacie"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
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

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Naprawdę chciałbym móc banować administratorów...")
        return ""

    if user_id == bot.id:
        message.reply_text("Nie zamierzam BANOWAĆ siebie, oszalałeś?")
        return ""

    log = "<b>{}:</b>" \
          "\n#ZBANOWANY" \
          "\n<b>Administrator:</b> {}" \
          "\n<b>Futrzak:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Powód:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} Zbanowany!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Zbanowano!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas banowania futrzaka %s na chacie %s (%s) z powodu %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę zbanować tego futrzaka.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
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

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Naprawdę chciałbym móc banować administratorów...")
        return ""

    if user_id == bot.id:
        message.reply_text("Nie zamierzam BANOWAĆ siebie, oszalałeś?")
        return ""

    if not reason:
        message.reply_text("Nie określiłeś czasu bonu tego futrzaka!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TYMCZASOWO ZBANOWANY" \
          "\n<b>Administrator:</b> {}" \
          "\n<b>Futrzak:</b> {}" \
          "\n<b>Okres:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Powód:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Zbanowano! Futrzak będzie zbanowany przez {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "User not found":
            # Do not reply
            message.reply_text("Zbanowano! Futrzak będzie zbanowany przez {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("BŁĄD podczas banowania futrzaka %s na chacie %s (%s) z powodu %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Cholera, nie mogę zbanować tego futrzaka.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Naprawdę chciałbym móc wyrzucać administratorów...")
        return ""

    if user_id == bot.id:
        message.reply_text("Tjaaa... Nie zrobię tego")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Wyrzucono!")
        log = "<b>{}:</b>" \
              "\n#WYRZUCONY" \
              "\n<b>Administrator:</b> {}" \
              "\n<b>Futrzak:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Powód:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Cholera, nie mogę wyrzucić tego futrzaka.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Chciałbym móc... Sle jesteś administratorem.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Nie ma problemu.")
    else:
        update.effective_message.reply_text("Huh? Nie mogę :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nie mogę znaleźć tego futrzaka")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Jakbym mógł odbanować siebie kiedy mnie tu by nie było...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Dlaczego próbujesz odbanować kogoś kto jest już na chacie?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Yup, ten futrzak może wrócić!")

    log = "<b>{}:</b>" \
          "\n#ODBANOWANY" \
          "\n<b>Administrator:</b> {}" \
          "\n<b>Futrzak:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Powód:</b> {}".format(reason)

    return log


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
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem")
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
        message.reply_text("Naprawdę chciałbym móc banować administratorów...")
        return

    if user_id == bot.id:
        message.reply_text("Nie zamierzam BANOWAĆ siebie, oszalałeś?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Zbanowano!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Zbanowany!', quote=False)
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
            message.reply_text("Czat nie znaleziony! Sprawdź czy podałeś poprawny chat ID oraz czy w nim jestem")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Przepraszam, ale to jest prywatny czat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Nie mogę tutaj odograniczać futrzaków! Sprawdź czy mam prawa administratora i czy mogę odbanować.")
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
        message.reply_text("Dlaczego próbujesz zdalnie odbanować kogoś kto jest już na chacie?")
        return ""

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


__help__ = """
 - /kickme: Wykopuje futrzaka który wpisał tą komendę

*Tylko Administracja:*
 - /ban <nazwa futrzaka>: Banuje futrzaka. (poprzez @, lub odpowiedź)
 - /tban <nazwa futrzaka> (m/g/d): Banuje futrzaka przez podaną ilość czasu. (poprzez @, lub odpowiedź). m = minuty, g = godziny, d = dni.
 - /unban <nazwa futrzaka>: Odbanuje futrzaka. (poprzez @, lub odpowiedź)
 - /kick <nazwa futrzaka>: Wykopuje futrzaka, (poprzez @, lub odpowiedź)
"""

__mod_name__ = "Bany"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
