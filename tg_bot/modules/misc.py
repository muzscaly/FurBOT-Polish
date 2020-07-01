import html
import json
import random
from datetime import datetime
from typing import Optional, List

import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters

QUOTE_STRINGS = (
    "Fajny ten pies\n~ Specyk",
    "Jaki kurwa wąwóz\n~ Avirka",
    "CZEKOLADOWE NALEŚNIKI\n~ Artorus",
    "Lazania to po prostu tort o smaku spaghetti\n~ Kozel",
    "UwU\n~ Praktycznie każdy futrzak",
    "OwO\n~ Praktycznie każdy futrzak",
    "Sąsiad tnie stylopian\n~ Artorus",
    "No i Pan Specu no kurwa jedziemy\n~ Kozel",
    "Wydymany zestresowany gaster zabawka antystresowa\n~ Mizchi",
    "Można spalić?\n~ Pusz",
    "Niech Godek szybko zemrze a Gastera zgwałcą węże\n~ Pusz",
    "To się susiakiem pobaw\n~ Stripe",
    "Jesteś mojom przyjaciółgom,\nmoim plynem do mycia okien,\nmoim spryskiwaczem do powierzchni szklanych\n~ Koda",
    "Ja ćpię cement\n~ Fluffy Incluatio",
    "Idę się ciąć mydłem. Adios\n~ Specyk",
    "CYGAN. LEJ TEN CEMENT\n~ Davis",
    "Epic\n~ Fluffy Incluatio",
    "Mursuit is just a fursuit with (reverse) gloryhole feature\n~ Davis",
    "Jeśli wszystko inne zawiedzie, rzucaj w to Futrzakami póki nie przestanie\n~Lexis",
    "Płytki podłogowe\n~ Pastel",
    "Chuj z butami, uwaga Olive będzie skakać!\n~ Cytrynek",
    "Nie zesraj sie\n~ Stripe",
    "Reee znów się zjebałem z łóżka psia kurwa zajebana mać ~ Pusz",
    "Jeżeli się mówi \"smacznego\" jak sie zaczyna jeść, to kiedy sie znaczyna pić to mówi sie \"pijnego\"?\n~ Olive",
)


SLAP_TEMPLATES = (
    "{user1} {hits} {user2} za pomocą {item}.",
    "{user1} {hits} prosto w twarz {user2} za pomocą {item}.",
    "{user1} lekko {hits} {user2} za pomocą {item}.",
    "{user1} {throws} {item} w {user2}.",
    "{user1} podnosi {item} i {throws} tym w twarz {user2}.",
    "{user1} wystrzeliwuje {item} w stronę {user2}.",
    "{user1} zaczyna lekko klepać {user2} za pomocą {item}.",
    "{user1} zdejmuje {user2} oraz ciągle {hits} go za pomocą {item}.",
    "{user1} podnasza {item} i {hits} tym w {user2}.",
    "{user1} przywiązuje {user2} do krzesła i {throws} {item} w niego/nią.",
    "{user1} skłonił(a) się pomóc {user2} w nauce pływania w lawie."
)

ITEMS = (
    "patelnia",
    "wielki pstrąg",
    "kij bezbolowy",
    "kij do krykietu",
    "drewniana laska",
    "gwódź",
    "drukarka",
    "łopata",
    "monitor CRT",
    "podręcznik do fizyki",
    "toster",
    "potret Gastera",
    "TV",
    "pięciotonowa ciężarówka",
    "taśma klejąca",
    "książka",
    "laptop",
    "stare TV",
    "worek skał",
    "pstrąg tęczowy",
    "gumowa kura",
    "kolczasty kij",
    "gaśnica",
    "cięzki kamień",
    "kawałek ziemi",
    "ul",
    "kawałek zgniłego mięsa",
    "niedźwiedź",
    "ton cegieł",
)

THROW = (
    "rzuca",
    "cisnie",
)

HIT = (
    "uderza",
    "wali",
    "grzmota",
    "trafia",
)

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


@run_async
def rquote(bot: Bot, update: Update):
    update.effective_message.reply_text(random.choice(QUOTE_STRINGS))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    """ Wysyła adres IP bota, aby móc wejść na ssh w razie potrzeby.
        TYLKO WŁAŚCICIEL.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "Pierwotny wysyłający, {}, ma ID `{}`.\nPrzesyłający, {}, ma ID `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id),
                parse_mode=ParseMode.MARKDOWN)
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_text("ID {} to `{}`.".format(escape_markdown(user.first_name), user.id),
                                                parse_mode=ParseMode.MARKDOWN)
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text("Twoje ID to `{}`.".format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text("ID grupy to `{}`.".format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN)


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        msg.reply_text("Nie mogę wyciągnąć informacji od tego futrzaka.")
        return

    else:
        return

    text = "<b>Informacje o futrzaku</b>:" \
           "\nID: <code>{}</code>" \
           "\nImię: {}".format(user.id, html.escape(user.first_name))

    if user.last_name:
        text += "\nNazwisko: {}".format(html.escape(user.last_name))

    if user.username:
        text += "\nPseudomin: @{}".format(html.escape(user.username))

    text += "\nPermamentny link futrzaka: {}".format(mention_html(user.id, "link"))

    if user.id == OWNER_ID:
        text += "\n\nTen futrzak jest moim opiekunem - Nigdy nie zrobiłbym nic przeciwko mu!"
    else:
        if user.id in SUDO_USERS:
            text += "\nTen futrzak jest jednym z moich sudo futrzaków! " \
                    "Prawie tak potężny jak mój opiekun - więc uważaj."
        else:
            if user.id in SUPPORT_USERS:
                text += "\nTen futrzak jest jednym z moich futrzaków wsparcia! " \
                        "Nie jest sudo futrzakiem, ale dalej może ciebie globalnie zbanować."

            if user.id in WHITELIST_USERS:
                text += "\nTen futrzak jest na białej liście! " \
                        "To znaczy że nie mogę go zbanować\wyrzucić."

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def get_time(bot: Bot, update: Update, args: List[str]):
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text("Dla mnie zawsze jest czas na Yiff!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(GMAPS_TIME, params=dict(location="{},{}".format(lat, long), timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp + offset).strftime("%H:%M:%S w %A %d %B")
                update.message.reply_text("Jest {} w {}".format(time_there, location))


@run_async
def echo(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@run_async
def gdpr(bot: Bot, update: Update):
    update.effective_message.reply_text("Usuwanie możliwych do zidentyfikowania danych...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text("Twoje dane osobowe zostały usunięte\n\nPamiętaj że to nie odbanuje "
                                        "ciebie z czatów z powodu że to już dane Telegrama, nie moje. "
                                        "Spam, ostrzeżenia oraz globalny ban są również zachowane z powodu "
                                        "[tego](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
                                        "które wyraźnie stwierdza, że prawo do usunięcia nie ma zastosowania "
                                        "\"jako wykonanie zadania realizowanego w interesie publicznym\", jak to "
                                        "ma miejsce w przypadku wyżej wymienionych danych.",
                                        parse_mode=ParseMode.MARKDOWN)


MARKDOWN_HELP = """
Markdown to bardzo potężne narzędzie do formatowania tekstu obsługiwane przez Telegram. {} ma kilka ulepszeń, aby upewnić się, \
że zapisane wiadomości są poprawnie parsowane i umożliwić tworzenie przycisków.

- <code>_kursywa_</code>: napisanie tekstu między '_' utworzy tekst z kursywą
- <code>*pogrubienie*</code>: napisanie tekstu między '*' utworzy pogrubiony tekst
- <code>`kod`</code>: napisanie tekstu między '`' utworzy tekst na stałej szerokości, znany jako 'kod'
- <code>[tekst](URL)</code>: utworzy link - wiadomość będzie pokazana jako tylko <code>tekst</code>, \
oraz jego naciśnięcie otworzy stronę <code>URL</code>.
NP: <code>[test](example.com)</code>

- <code>[tekst](buttonurl:URL)</code>: to jest specjalne ulepszenie które pozwala futrzakom utworzyć \
przyciski. <code>tekst</code> biędzie pokazany jako nazwa przycisku a <code>URL</code> \
będzie linkiem kryjącym się pod przyciskiem.
NP: <code>[To jest przycisk](buttonurl:example.com)</code>

Jeżeli chcesz wiele przycisków na tym samym wierszu, dodaj :same. Jak tutaj:
<code>[pierwszy](buttonurl://example.com)
[drugi](buttonurl://google.com:same)</code>
To utworzy 2 przyciski na wiersz zamiast jednego.

Miej na uwadze że wiadomość z przyciskiem <b>MUSI</b> posiadać jakiś tekst niż sam przycisk!
""".format(dispatcher.bot.first_name)


@run_async
def markdown_help(bot: Bot, update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text("Spróbuj przesłać następującą wiadomość do mnie, i zobaczysz!")
    update.effective_message.reply_text("/save test To jest test markdown. _kursywa_, *pogrubienie*, `kod`, "
                                        "[URL](example.com) [przycisk](buttonurl:github.com) "
                                        "[przycisk2](buttonurl://google.com:same)")


@run_async
def stats(bot: Bot, update: Update):
    update.effective_message.reply_text("Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS]))

@run_async
def stickerid(bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text("ID naklejki:\n```" + 
                                            escape_markdown(msg.reply_to_message.sticker.file_id) + "```",
                                            parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Użyj tej komendy jako odpowiedź do naklejki żeby uzyskać jej ID",
                                            parse_mode=ParseMode.MARKDOWN)
@run_async
def getsticker(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        bot.sendChatAction(chat_id, "typing")
        update.effective_message.reply_text("Korzystaj z tej funkcji mądrze!",
                                            parse_mode=ParseMode.MARKDOWN)
        bot.sendChatAction(chat_id, "upload_document")
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.sendDocument(chat_id, document=open('sticker.png', 'rb'))
#       bot.sendChatAction(chat_id, "upload_photo")
#       bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))
        
    else:
        bot.sendChatAction(chat_id, "typing")
        update.effective_message.reply_text("Użyj tej komendy jako odpowiedź do naklejki żeby uzyskać obraz tej naklejki",
                                            parse_mode=ParseMode.MARKDOWN)

@run_async
def hug(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        hugged_user = bot.get_chat(user_id)
        user1 = curr_user
        if hugged_user.username:
            user2 = "@" + escape_markdown(hugged_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(hugged_user.first_name,
                                                   hugged_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = "{user1} przytula {user2}!\n{user2} został(a) przytulony/a NaN razy!"

    repl = temp.format(user1=user1, user2=user2)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)

@run_async
def boop(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        booped_user = bot.get_chat(user_id)
        user1 = curr_user
        if booped_user.username:
            user2 = "@" + escape_markdown(booped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(booped_user.first_name,
                                                   booped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = "{user1} tycnął {user2}!\n{user2} został(a) tycnięty/a NaN razy!"

    repl = temp.format(user1=user1, user2=user2)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)

@run_async
def warm(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        warmed_user = bot.get_chat(user_id)
        user1 = curr_user
        if warmed_user.username:
            user2 = "@" + escape_markdown(warmed_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(warmed_user.first_name,
                                                   warmed_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = "{user1} ogrzał {user2}!\n{user2} został(a) ogrzany/a NaN razy!"

    repl = temp.format(user1=user1, user2=user2)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)
		
@run_async
def pat(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        patted_user = bot.get_chat(user_id)
        user1 = curr_user
        if patted_user.username:
            user2 = "@" + escape_markdown(patted_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(patted_user.first_name,
                                                   patted_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = "{user1} poklepał {user2}!\n{user2} został(a) poklepany/a NaN razy!"

    repl = temp.format(user1=user1, user2=user2)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)

# /ip is for private use
__help__ = """
 - /id: Wypisuje obecny groupid. Jeżeli użyte w odpowiedzi do wiadomości, wypisuje userid.
 - /rquote: Odpisuje losową wiadomością z listy cytatów.
 - /slap: Uderza futrzaka lub uderza wysyłającego jeżeli nie zostało użyte w odpowiedzi
 - /hug: Huga futrzaka lub przytula wysyłającego jeżeli nie zostało użyte w odpowiedzi.
 - /boop: Tyca futrzaka lub tyca wysyłającego jeżeli nie zostało użyte w odpowiedzi.
 - /warm: Ociepla futrzaka lub ociepla wysyłającego jeżeli nie zostało użyte w odpowiedzi.
 - /pat: Poklepywuje futrzaka lub poklepywuje wysyłającego jeżeli nie zostało użyte w odpowiedzi.
 - /time <miejsce>: Podaje lokalny czas w podanym miejscu.
 - /info: Uzyskaj informacje o futrzaku.
 - /gdpr: usuwa twoje informacje z mojej bazy danych. Użycie tylko na PW.
 - /markdownhelp: szybki tutorial działania markdown w Telegramie. Użycie tylko na PW.
 - /stickerid: Użycie przy odpowiedzi na naklejkę zwraca jej ID.
 - /getsticker: Użycie przy odpowiedzi na naklejkę zwraca obraz PNG naklejki.
"""

__mod_name__ = "Inne"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))

TIME_HANDLER = CommandHandler("time", get_time, pass_args=True)

RQUOTE_HANDLER = DisableAbleCommandHandler("rquote", rquote)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)
HUG_HANDLER = DisableAbleCommandHandler("hug", hug, pass_args=True)
BOOP_HANDLER = DisableAbleCommandHandler("boop", boop, pass_args=True)
WARM_HANDLER = DisableAbleCommandHandler("warm", warm, pass_args=True)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)


dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(RQUOTE_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(HUG_HANDLER)
dispatcher.add_handler(BOOP_HANDLER)
dispatcher.add_handler(WARM_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
