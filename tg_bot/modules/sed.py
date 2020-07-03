
import re
import sre_constants

import telegram
from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleRegexHandler

DELIMITERS = ("/", ":", "|", "_")


def separate_sed(sed_string):
    if len(sed_string) >= 3 and sed_string[1] in DELIMITERS and sed_string.count(sed_string[1]) >= 2:
        delim = sed_string[1]
        start = counter = 2
        while counter < len(sed_string):
            if sed_string[counter] == "\\":
                counter += 1

            elif sed_string[counter] == delim:
                replace = sed_string[start:counter]
                counter += 1
                start = counter
                break

            counter += 1

        else:
            return None

        while counter < len(sed_string):
            if sed_string[counter] == "\\" and counter + 1 < len(sed_string) and sed_string[counter + 1] == delim:
                sed_string = sed_string[:counter] + sed_string[counter + 1:]

            elif sed_string[counter] == delim:
                replace_with = sed_string[start:counter]
                counter += 1
                break

            counter += 1
        else:
            return replace, sed_string[start:], ""

        flags = ""
        if counter < len(sed_string):
            flags = sed_string[counter:]
        return replace, replace_with, flags.lower()


@run_async
def sed(bot: Bot, update: Update):
    sed_result = separate_sed(update.effective_message.text)
    if sed_result and update.effective_message.reply_to_message:
        if update.effective_message.reply_to_message.text:
            to_fix = update.effective_message.reply_to_message.text
        elif update.effective_message.reply_to_message.caption:
            to_fix = update.effective_message.reply_to_message.caption
        else:
            return

        repl, repl_with, flags = sed_result

        if not repl:
            update.effective_message.reply_to_message.reply_text("Próbujesz zastąpić... "
                                                                 "niczym czymś?")
            return

        try:
            check = re.match(repl, to_fix, flags=re.IGNORECASE)

            if check and check.group(0).lower() == to_fix.lower():
                update.effective_message.reply_to_message.reply_text("Hej wszystkim, {} próbuje zmusić mnie "
                                                                     "powiedzenia rzeczy, których nie chcę "
                                                                     "powiedzieć!".format(update.effective_user.first_name))
                return

            if 'i' in flags and 'g' in flags:
                text = re.sub(repl, repl_with, to_fix, flags=re.I).strip()
            elif 'i' in flags:
                text = re.sub(repl, repl_with, to_fix, count=1, flags=re.I).strip()
            elif 'g' in flags:
                text = re.sub(repl, repl_with, to_fix).strip()
            else:
                text = re.sub(repl, repl_with, to_fix, count=1).strip()
        except sre_constants.error:
            LOGGER.warning(update.effective_message.text)
            LOGGER.exception("Błąd ciągłości SRE")
            update.effective_message.reply_text("Czy ty w ogóle sedowałeś? Najwyraźniej nie.")
            return

        # empty string errors -_-
        if len(text) >= telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text("Wynik komendy sed był zbyt długi dla \
                                                 Telegrama!")
        elif text:
            update.effective_message.reply_to_message.reply_text(text)


__help__ = """
 - s/<tekst1>/<tekst2>(/<flaga>): Użyte w odpowiedzi, wykonywuje operację sed dla tej wiadomości, zastępując wszystkie \
słowa 'tekst1' słowami 'text2'. Flagi są opcjonalne i obecnie zawierają 'i' w przypadku ignorowania wielkości liter, \
„g” w przypadku globalnej lub nic. Ograniczniki obejmują `/`, `_`, `|`, oraz `:`. Obsługiwane jest grupowanie tekstu. \
Wiadomość wyjściowa nie może być większa niż {}.
*Przypomnienie:* Sed używa znaków specjalnych, aby ułatwić dopasowanie, takie jak: `+*.?\\`
Jeśli chcesz użyć tych znaków, upewnij się, że są dobrze zescapowane!
np: \\?.
""".format(telegram.MAX_MESSAGE_LENGTH)

__mod_name__ = "Sed/Regex"


SED_HANDLER = DisableAbleRegexHandler(r's([{}]).*?\1.*'.format("".join(DELIMITERS)), sed, friendly="sed")

dispatcher.add_handler(SED_HANDLER)
