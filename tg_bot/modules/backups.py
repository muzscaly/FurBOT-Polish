import json
from io import BytesIO
from typing import Optional

from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.__main__ import DATA_IMPORT
from tg_bot.modules.helper_funcs.chat_status import user_admin


@run_async
@user_admin
def import_data(bot: Bot, update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    # TODO: allow uploading doc with command, not just as reply
    # only work with a doc
    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text("Spróbuj pobrać i ponownie wysłać plik jaki był przed importowaniem - ten wydaje się "
                           "być niepewny!")
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # only import one group
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text("W tym pliku znajduje się więcej niż jedna grupa, i żadena nie ma takiego samego chat id jak ta grupa "
                           "- co wybrać, żeby zaimportować?")
            return

        # Select data source
        if str(chat.id) in data:
            data = data[str(chat.id)]['hashes']
        else:
            data = data[list(data.keys())[0]]['hashes']

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text("Wystąpił błąd podczas przywracania danych. Proces może nie być kompletny. If "
                           "Jeśli masz z tym problemy, napisz do @MarieSupport z plikiem kopii zapasowej, aby "
                           "zdebugować ten problem. Moi właściciele chętnie pomogą, a każdy zgłoszony "
                           "błąd czyni mnie lepszym! Dzięki! UwU")
            LOGGER.exception("Import dla chatid %s z nazwą %s nie powódł się.", str(chat.id), str(chat.title))
            return

        # TODO: some of that link logic
        # NOTE: consider default permissions stuff?
        msg.reply_text("Kopia zapasowa w pełni zimportowana. Witaj spowrotem! OwO")


@run_async
@user_admin
def export_data(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    msg.reply_text("")


__mod_name__ = "Kopie zapasowe"

__help__ = """
*Tylko administracja:*
 - /import: Użyj w odpowiedzi pliku kopii zapasowej od Group Butlera lub Futrzaczka jeżeli jest to możliwe, żeby wykonać bezproblemowo transfer! Notka \
 pliki oraz zdjęcia nie można zaimportować z powodu ograniczeń telegramu.
 - /export: !!! To nie jest jeszcze komenda, ale będzie nią wkrótce!
"""
IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data)

dispatcher.add_handler(IMPORT_HANDLER)
# dispatcher.add_handler(EXPORT_HANDLER)
