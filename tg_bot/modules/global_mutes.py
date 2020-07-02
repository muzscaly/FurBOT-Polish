import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_mutes_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GMUTE
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GMUTE_ENFORCE_GROUP = 6


@run_async
def gmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("Będę go śledził moim małym oczkiem... Wojna sudo futrzaków! Dlaczego odwracacie się od siebie nawzajem?")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OHO! któś próbuje globalnie wyciszyć futrzaka od supportu! *bierze popcorn*")
        return

    if user_id == bot.id:
        message.reply_text("-_- Bardzo śmieszne... Globalnie wycisz mnie, dlaczego by nie? Niezła próba.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("To nie jest futrzak!")
        return

    if sql.is_user_gmuted(user_id):
        if not reason:
             message.reply_text("Ten futrzak jest już globalnie wyciszony. Mogę zmienić powód ale nie podałeś mi żadnego...")
            return

        success = sql.update_gmute_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if success:
            message.reply_text("Ten futrzak jest już globalnie wyciszony ale nie ma ustawionego powodu. Ale już to zostało poprawione!")
        else:
            message.reply_text("Czy możesz spróbować ponownie? Myślałem, że ta osoba była globalnie wyciszona, ale tak nie było? "
                               "Jestem bardzo zdezorientowany")

        return

    message.reply_text("*bierze taśmę klejącą* 😉")

    muter = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{} is gmuting user {} "
                 "Ponieważ:\n{}".format(mention_html(muter.id, muter.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or "No reason given"),
                 html=True)

    sql.gmute_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
        except BadRequest as excp:
            if excp.message == "Futrzak jest administratorem czatu":
                pass
            elif excp.message == "Nie znaleziono czatu":
                pass
            elif excp.message == "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Peer_id_invalid":  # Suspect this happens when a group is suspended by telegram.
                pass
            elif excp.message == "Czat grupy został zdeaktywowany":
                pass
            elif excp.message == "Trzeba być zapraszającym futrzaka, aby wyciszyć go na grupie":
                pass
            elif excp.message == "Chat_admin_required":
                pass
            elif excp.message == "Tylko twórca grupy może wyciszać administratorów grupy":
                pass
            elif excp.message == "Metoda jest dostępna tylko dla supergrup oraz kanałów":
                pass
            elif excp.message == "Nie można zdegradować twórcy czatu":
                pass
            else:
                message.reply_text("Nie mogę globalnie wyciszyć z powodu: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Nie mogę globalnie wyciszyć z powodu: {}".format(excp.message))
                sql.ungmute_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "pomyślnie globalnie wyciszono!")
    message.reply_text("Futrzak został globalnie wyciszony.")


@run_async
def ungmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Wygląda na to, że nie odnosisz się do futrzaka.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("To nie jest futrzak!")
        return

    if not sql.is_user_gmuted(user_id):
        message.reply_text("Ten futrzak nie jest globalnie wyciszony!")
        return

    muter = update.effective_user  # type: Optional[User]

    message.reply_text("Pozwolę tobie ponownie globalnie rozmawiać, {}.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{} globalnie odciszył {}".format(mention_html(muter.id, muter.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name)),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'restricted':
                bot.restrict_chat_member(chat_id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)

        except BadRequest as excp:
            if excp.message == "Futrzak jest administratorem czatu":
                pass
            elif excp.message == "Nie znaleziono czatu":
                pass
            elif excp.message == "Brak wystarczających uprawnień do ograniczenia/odgraniczenia futrzaka tego czatu":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Metoda jest dostępna tylko dla supergrup oraz kanałów":
                pass
            elif excp.message == "Nie na czacie":
                pass
            elif excp.message == "Channel_private":
                pass
            elif excp.message == "Chat_admin_required":
                pass
            else:
                message.reply_text("Nie mogę globalnie odciszyć z powodu: {}".format(excp.message))
                bot.send_message(OWNER_ID, "Nie mogę globalnie odciszyć z powodu: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungmute_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "pomyślnie globalnie odciszono!")

    message.reply_text("Futrzak został globalnie odciszony.")


@run_async
def gmutelist(bot: Bot, update: Update):
    muted_users = sql.get_gmute_list()

    if not muted_users:
        update.effective_message.reply_text("Nie ma żadnego globalnie wyciszonego futrzaka! Jesteś milszy niż się spodziewałem...")
        return

    mutefile = 'Walić tych futrzaków.\n'
    for user in muted_users:
        mutefile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            mutefile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(mutefile)) as output:
        output.name = "gmutelist.txt"
        update.effective_message.reply_document(document=output, filename="gmutelist.txt",
                                                caption="Tutaj jest lista obecnie globalnie wyciszonych futrzaków.")


def check_and_mute(bot, update, user_id, should_message=True):
    if sql.is_user_gmuted(user_id):
        bot.restrict_chat_member(update.effective_chat.id, user_id, can_send_messages=False)
        if should_message:
            update.effective_message.reply_text("To jest zły futrzak, wyciszę go dla ciebie!")


@run_async
def enforce_gmute(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gmute.
    if sql.does_chat_gmute(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_mute(bot, update, user.id, should_message=True)
        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_mute(bot, update, mem.id, should_message=True)
        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_mute(bot, update, user.id, should_message=True)

@run_async
@user_admin
def gmutestat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("Włączyłem globalne bany dla tej grupy. To pomoże ci uchronić się "
                                                "przed spamerami, niechcianymi futrzakami, oraz największymi trollami.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("Wyłączyłem globalne wyciszenia dla tej grupy. Globalne bany nie będą więcej dotykać "
                                                "twoich futrzaków. Będziesz za to bardziej podatny na spammerów oraz "
                                                "trollów!")
    else:
        update.effective_message.reply_text("Daj mi jakiś argument żeby zmienić ustawienie! on/off, yes/no!\n\n"
                                            "Twoje obecne ustawienie: {}\n"
                                            "Jeśli True, jakiekolwiek wykonane globalne wyciszenia będą też aktywne na twojej grupie. "
                                            "Jeśli False, to one nie będą, zostawiając ciebie na prawdopodobną łaskę "
                                            "spammerów.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return "{} globalnie wyciszonych futrzaków.".format(sql.num_gmuted_users())


def __user_info__(user_id):
    is_gmuted = sql.is_user_gmuted(user_id)

    text = "Globalnie wyciszony: <b>{}</b>"
    if is_gmuted:
        text = text.format("Tak")
        user = sql.get_gmuted_user(user_id)
        if user.reason:
            text += "\nPowód: {}".format(html.escape(user.reason))
    else:
        text = text.format("Nie")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "Czat używa *globalnych wyciszeń*: `{}`.".format(sql.does_chat_gmute(chat_id))


__help__ = """
*Tylko Administracja:*
 - /gmutestat <on/off/yes/no>: Wyłącza działanie globalnych wyciszeń w twojej grupie, lub przywróci do obecnych ustawień.
Globalne wyciszane, są używane przez właścicieli botów do wyciszania niechcianych futrzaków na wszystkich grupach. To pomaga uchronić \
ciebie i twoje grupy przed spammerami jaknajszybciej jak to możliwe. Mogą zostać wyłączone na grupie poprzez \
/gmutestat
"""

__mod_name__ = "Globalne Wyciszenia"

GMUTE_HANDLER = CommandHandler("gmute", gmute, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGMUTE_HANDLER = CommandHandler("ungmute", ungmute, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GMUTE_LIST = CommandHandler("gmutelist", gmutelist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GMUTE_STATUS = CommandHandler("gmutestat", gmutestat, pass_args=True, filters=Filters.group)

GMUTE_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gmute)

dispatcher.add_handler(GMUTE_HANDLER)
dispatcher.add_handler(UNGMUTE_HANDLER)
dispatcher.add_handler(GMUTE_LIST)
dispatcher.add_handler(GMUTE_STATUS)

if STRICT_GMUTE:
    dispatcher.add_handler(GMUTE_ENFORCER, GMUTE_ENFORCE_GROUP)
