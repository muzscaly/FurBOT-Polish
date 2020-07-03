import re
from io import BytesIO
from typing import Optional, List

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram import Message, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, RegexHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.notes_sql as sql
from tg_bot import dispatcher, MESSAGE_DUMP, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_note_type

from tg_bot.modules.connection import connected

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# Do not async
def get(bot, update, notename, show_none=True, no_format=False):
    chat_id = update.effective_chat.id
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        send_id = user.id
    else:
        chat_id = update.effective_chat.id
        send_id = chat_id

    note = sql.get_note(chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=MESSAGE_DUMP, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text("Wygląda na to że ta wiadomość się zagubiła - Usunę ją "
                                           "z twojej listy notek.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=chat_id, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text("Wygląda na to że oryginalny wysyłający usunął swoją "
                                           "wiadomość - przepraszam! Poproś administratora bota aby zasczął "
                                           "tworzyć zrzuty wiadomości żeby uniknąć takich rzeczy. "
                                           "Usunę tą notkę z twoich zapisanych notek.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            text = note.value
            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            should_preview_disabled = True
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)
                if "telegra.ph" in text or "youtu.be" in text:
                    should_preview_disabled = False

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    bot.send_message(chat_id, text, reply_to_message_id=reply_id,
                                     parse_mode=parseMode, disable_web_page_preview=should_preview_disabled,
                                     reply_markup=keyboard)
                else:
                    ENUM_FUNC_MAP[note.msgtype](chat_id, note.file, caption=text, reply_to_message_id=reply_id,
                                                parse_mode=parseMode, disable_web_page_preview=should_preview_disabled,
                                                reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text("Wygląda na to że próbujesz wspomnieć o futrzaku którego nigdy nie widziałem wcześniej. Jeżeli serio "
                                       "go wspomnieć, prześlij mi jedną wiadomość od tego futrzaka do mnie a ja będę mógł wtedy "
                                       "go otagować!")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text("Ta notka jest niepoprawna zimportowana od innego bota - Nie mogę "
                                       "użyć jej. Jeżeli serio chcesz ją mieć, musisz ją zapisać ponownie. Przez "
                                       "ten czas usunę ją z listy twoich notek.")
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text("Nie można wysłać tej notki, ponieważ jest niepoprawnie sformatowana. Spytaj "
                                       "na @MarieSupport jeśli nie możesz zrozumieć dlaczego!")
                    LOGGER.exception("Nie można sparsować notki #%s w czacie %s", notename, str(chat_id))
                    LOGGER.warning("Wiadomość była: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("Ta notka nie istnieje")


@run_async
def cmd_get(bot: Bot, update: Update, args: List[str]):
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(bot, update, args[0], show_none=True, no_format=True)
    elif len(args) >= 1:
        get(bot, update, args[0], show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


@run_async
def hash_get(bot: Bot, update: Update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, no_hash, show_none=False)


@run_async
@user_admin
def save(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    msg = update.effective_message  # type: Optional[Message]

    note_name, text, data_type, content, buttons = get_note_type(msg)

    if data_type is None:
        msg.reply_text("Ziom, nie ma notek")
        return

    if len(text.strip()) == 0:
        text = note_name

    sql.add_note_to_db(chat_id, note_name, text, data_type, buttons=buttons, file=content)

    msg.reply_text(
        "OK, Dodano notkę '{note_name}' do *{chat_name}*.\nUżyj jej poprzez /get {note_name} lub #{note_name}".format(note_name=note_name, chat_name=chat_name), parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text("Wygląda na to że chcesz zapisać wiadomość od bota. Niestety, "
                           "boty nie mogą przesyłać wiadomości botów, więc nie mogę zapisać dokładnie tą samą wiadomość. "
                           "\nSpróbuję zapisać cały tekst który jest, ale jeśli chcesz więcej, musisz "
                           "przesłać sam wiadomość, a później ją zapisać.")
        else:
            msg.reply_text("Boty są trochę upośledzone przez Telegrama, przez utrudnianie im "
                           "komunikacji między sobą, więc nie mogę zapisać tej wiadomość "
                           "jak ja zwykle to robię. Myślałeś o przesłaniu tej wiadomości "
                           "oraz zapisać ją jako nową wiadomość? Dzięki!")
        return


@run_async
@user_admin
def clear(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    if len(args) >= 1:
        notename = args[0]

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Notka usunięta pomyślnie.")
        else:
            update.effective_message.reply_text("To nie jest notka z mojej bazy danych!")


@run_async
def list_notes(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        msg = "*NNotki w {}:*\n".format(chat_name)
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = ""
            msg = "*Lokalne notki:*\n".format(chat_name)
        else:
            chat_name = chat.title
            msg = "*Notki w {}:*\n".format(chat_name)

    note_list = sql.get_all_chat_notes(chat_id)

    for note in note_list:
        note_name = escape_markdown(" - {}\n".format(note.name))
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if msg == "*Notes in chat:*\n":
        update.effective_message.reply_text("Brak notek na tym czacie!")

    elif len(msg) != 0:
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get('extra', {}).items():
        match = FILE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(chat_id, document=output, filename="failed_imports.txt",
                                         caption="Tych plików/zdjęć nie udało się zimportować z powodu pochodzenia "
                                                 "z innego bota. To jest ograniczenie API Telegrama, i nie może"
                                                 "być ominięte. Przepraszam za niedogodność!")


def __stats__():
    return "{} notek spośród {} czatów.".format(sql.num_notes(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return "Jest obecnie `{}` notek na tym czacie.".format(len(notes))


__help__ = """
 - /get <notka>: Wysyła notkę.
 - #<notka>: To samo co /get.
 - /notes or /saved: Lista wszystkich notek na czacie.

Jeśli chcesz odzyskać zawartość notatki bez formatowania, użyj `/get <notka> noformat`. To może \
się przydać podczas aktualizacji bieżącej notatki.

*Tylko administracja:*
 - /save <notka> <wiadomość>: Zapisuje wiadomość jako notkę pod nazwą 'notka'.
Można dodać przycisk do notki poprzez użycie markdown linku przycisku. Link przygotoway z sekcją \
`buttonurl:`, przykładowo: `[URL](buttonurl:example.com)`. Wpisz /markdownhelp po więcej informacji.
 - /save <notka>: Zapisuje odpowiadaną wiadomość jako notkę pod nazwą 'notka'.
 - /clear <notka>: Usuwa notkę pod taką nazwą.
"""

__mod_name__ = "Notki"

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True)
HASH_GET_HANDLER = RegexHandler(r"^#[^\s]+", hash_get)

SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"], list_notes, admin_ok=True)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
