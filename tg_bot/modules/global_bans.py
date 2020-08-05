import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "Futrzak jest administratorem czatu",
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

UNGBAN_ERRORS = {
    "Futrzak jest administratorem czatu",
    "Nie znaleziono czatu",
    "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu",
    "User_not_participant",
    "Metoda jest dostępna tylko dla supergrup oraz kanałów",
    "Nie na czacie",
    "Channel_private",
    "Chat_admin_required",
}


@run_async
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("I spy, with my little eye... a sudo user war! Why are you guys turning on each other?")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH someone's trying to gban a support user! *grabs popcorn*")
        return

    if user_id == bot.id:
        message.reply_text("-_- So funny, lets gban myself why don't I? Nice try.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text("This user is already gbanned; I'd change the reason, but you haven't given me one...")
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text("This user is already gbanned, for the following reason:\n"
                               "<code>{}</code>\n"
                               "I've gone and updated it with your new reason!".format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML)
        else:
            message.reply_text("This user is already gbanned, but had no reason set; I've gone and updated it!")

        return

    message.reply_text("⚡️ *Snaps the Banhammer* ⚡️")

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>Global Ban</b>" \
                 "\n#GBAN" \
                 "\n<b>Status:</b> <code>Enforcing</code>" \
                 "\n<b>Sudo Admin:</b> {}" \
                 "\n<b>User:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>" \
                 "\n<b>Reason:</b> {}".format(mention_html(banner.id, banner.first_name),
                                              mention_html(user_chat.id, user_chat.first_name), 
                                                           user_chat.id, reason or "No reason given"), 
                html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text("Could not gban due to: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Could not gban due to: {}".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, 
                  "{} has been successfully gbanned!".format(mention_html(user_chat.id, user_chat.first_name)),
                html=True)
    message.reply_text("Person has been gbanned.")


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("To nie jest futrzak!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Ten futrzak nie jest globalnie zbanowany!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("Przepraszam ciebie {}. Dostałeś globalne ułaskawienie.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>Globalne odbanowanie</b>" \
                 "\n#GLOBALNE ODBANOWANIE" \
                 "\n<b>Status:</b> <code>Odwłołany</code>" \
                 "\n<b>Sudo administrator:</b> {}" \
                 "\n<b>Futrzak:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),
                                                       mention_html(user_chat.id, user_chat.first_name), 
                                                                    user_chat.id),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text("Nie mogę globalnie odbanować z powodu: {}".format(excp.message))
                bot.send_message(OWNER_ID, "Nie mogę globalnie odbanować z powodu: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, 
                  "{} został ułaskawiony z globalnego bana!".format(mention_html(user_chat.id, 
                                                                                 user_chat.first_name)),
                  html=True)

    message.reply_text("Ten futrzak został globalnie odbanowany i ułaskawiony!")


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("Nie ma żadnego globalnie zbanowanego futrzaka! Jesteś milszy niż się spodziewałem...")
        return

    banfile = 'Walić tych futrzaków.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Powód: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="Tutaj jest lista obecnie globalnie zbanowanych futrzaków.")


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text("To jest zły futrzak, jego nie powinno być tutaj!")


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Włączyłem globalne bany dla tej grupy. To pomoże ci uchronić się "
                                                "przed spamerami, niechcianymi futrzakami, oraz największymi trollami.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Wyłączyłem globalne bany dla tej grupy. Globalne bany nie będą więcej dotykać "
                                                "twoich futrzaków. Będziesz za to bardziej podatny na spammerów oraz "
                                                "trollów!")
    else:
        update.effective_message.reply_text("Daj mi jakiś argument żeby zmienić ustawienie! on/off, yes/no!\n\n"
                                            "Twoje obecne ustawienie: {}\n"
                                            "Jeśli True, jakiekolwiek wykonane globalne bany będą też aktywne na twojej grupie. "
                                            "Jeśli False, to one nie będą, zostawiając ciebie na prawdopodobną łaskę "
                                            "spammerów.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return "{} globalnie zbanowanych futrzaków.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "Globalnie zbanowany: <b>{}</b>"
    if is_gbanned:
        text = text.format("Tak")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nPowód: {}".format(html.escape(user.reason))
    else:
        text = text.format("Nie")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Czat używa *globalnych banów*: `{}`.".format(sql.does_chat_gban(chat_id))


__help__ = """
*Tylko Administracja:*
 - /gbanstat <on/off/yes/no>: Wyłącza działanie globalnych banów w twojej grupie, lub przywróci do obecnych ustawień.

Globalne bany, są używane przez właścicieli botów do uchrony przed niechcianymi futrzakami na wszystkich grupach. To pomaga uchronić \
ciebie i twoje grupy przed spammerami jaknajszybciej jak to możliwe. Mogą zostać wyłączone na grupie poprzez \
/gbanstat
"""

__mod_name__ = "Globalne Bany"

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GBAN_STATUS = CommandHandler("gbanstat", gbanstat, pass_args=True, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
