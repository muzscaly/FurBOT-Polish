import random, re
from random import randint
from telegram import Message, Update, Bot, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram import MessageEntity
from telegram.ext import Filters, MessageHandler, run_async
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.userinfo_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user

ABUSE_STRINGS = (
    "Fuck off",
    "Stfu go fuck yourself",
    "Ur mum gey",
    "Ur dad lesbo",
    "Bsdk",
    "Nigga",
    "Ur granny tranny",
    "you noob",
	"Relax your Rear,ders nothing to fear,The Rape train is finally here",
	"Stfu bc",
	"Stfu and Gtfo U nub",
	"GTFO bsdk"
    "CUnt",
    " Gay is here",
    "Ur dad gey bc "
)

EYES = [
    ['⌐■', '■'],
    [' ͠°', ' °'],
    ['⇀', '↼'],
    ['´• ', ' •`'],
    ['´', '`'],
    ['`', '´'],
    ['ó', 'ò'],
    ['ò', 'ó'],
    ['⸌', '⸍'],
    ['>', '<'],
    ['Ƹ̵̡', 'Ʒ'],
    ['ᗒ', 'ᗕ'],
    ['⟃', '⟄'],
    ['⪧', '⪦'],
    ['⪦', '⪧'],
    ['⪩', '⪨'],
    ['⪨', '⪩'],
    ['⪰', '⪯'],
    ['⫑', '⫒'],
    ['⨴', '⨵'],
    ['⩿', '⪀'],
    ['⩾', '⩽'],
    ['⩺', '⩹'],
    ['⩹', '⩺'],
    ['◥▶', '◀◤'],
    ['◍', '◎'],
    ['/͠-', '┐͡-\\'],
    ['⌣', '⌣”'],
    [' ͡⎚', ' ͡⎚'],
    ['≋'],
    ['૦ઁ'],
    ['  ͯ'],
    ['  ͌'],
    ['ළ'],
    ['◉'],
    ['☉'],
    ['・'],
    ['▰'],
    ['ᵔ'],
    [' ﾟ'],
    ['□'],
    ['☼'],
    ['*'],
    ['`'],
    ['⚆'],
    ['⊜'],
    ['>'],
    ['❍'],
    ['￣'],
    ['─'],
    ['✿'],
    ['•'],
    ['T'],
    ['^'],
    ['ⱺ'],
    ['@'],
    ['ȍ'],
    ['  '],
    ['  '],
    ['x'],
    ['-'],
    ['$'],
    ['Ȍ'],
    ['ʘ'],
    ['Ꝋ'],
    [''],
    ['⸟'],
    ['๏'],
    ['ⴲ'],
    ['◕'],
    ['◔'],
    ['✧'],
    ['■'],
    ['♥'],
    [' ͡°'],
    ['¬'],
    [' º '],
    ['⨶'],
    ['⨱'],
    ['⏓'],
    ['⏒'],
    ['⍜'],
    ['⍤'],
    ['ᚖ'],
    ['ᴗ'],
    ['ಠ'],
    ['σ'],
    ['☯']
]

MOUTHS = [
    ['v'],
    ['ᴥ'],
    ['ᗝ'],
    ['Ѡ'],
    ['ᗜ'],
    ['Ꮂ'],
    ['ᨓ'],
    ['ᨎ'],
    ['ヮ'],
    ['╭͜ʖ╮'],
    [' ͟ل͜'],
    [' ͜ʖ'],
    [' ͟ʖ'],
    [' ʖ̯'],
    ['ω'],
    [' ³'],
    [' ε '],
    ['﹏'],
    ['□'],
    ['ل͜'],
    ['‿'],
    ['╭╮'],
    ['‿‿'],
    ['▾'],
    ['‸'],
    ['Д'],
    ['∀'],
    ['!'],
    ['人'],
    ['.'],
    ['ロ'],
    ['_'],
    ['෴'],
    ['ѽ'],
    ['ഌ'],
    ['⏠'],
    ['⏏'],
    ['⍊'],
    ['⍘'],
    ['ツ'],
    ['益'],
    ['╭∩╮'],
    ['Ĺ̯'],
    ['◡'],
    [' ͜つ']
]

EARS = [
    ['q', 'p'],
    ['ʢ', 'ʡ'],
    ['⸮', '?'],
    ['ʕ', 'ʔ'],
    ['ᖗ', 'ᖘ'],
    ['ᕦ', 'ᕥ'],
    ['ᕦ(', ')ᕥ'],
    ['ᕙ(', ')ᕗ'],
    ['ᘳ', 'ᘰ'],
    ['ᕮ', 'ᕭ'],
    ['ᕳ', 'ᕲ'],
    ['(', ')'],
    ['[', ']'],
    ['¯\\_', '_/¯'],
    ['୧', '୨'],
    ['୨', '୧'],
    ['⤜(', ')⤏'],
    ['☞', '☞'],
    ['ᑫ', 'ᑷ'],
    ['ᑴ', 'ᑷ'],
    ['ヽ(', ')ﾉ'],
    ['\\(', ')/'],
    ['乁(', ')ㄏ'],
    ['└[', ']┘'],
    ['(づ', ')づ'],
    ['(ง', ')ง'],
    ['⎝', '⎠'],
    ['ლ(', 'ლ)'],
    ['ᕕ(', ')ᕗ'],
    ['(∩', ')⊃━☆ﾟ.*'],
]

TOSS = (
    "Heads",
    "Tails",
)

@run_async
def roll(bot: Bot, update: Update):
    update.message.reply_text(random.choice(range(1, 7)))
	
def toss(bot: Bot, update: Update):
    update.message.reply_text(random.choice(TOSS))

@run_async
def abuse(bot: Bot, update: Update):
    # reply to correct message
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(random.choice(ABUSE_STRINGS))
	
@run_async
def shrug(bot: Bot, update: Update):
    # reply to correct message
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text("¯\_(ツ)_/¯")	
	
@run_async
def bluetext(bot: Bot, update: Update):
    # reply to correct message
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text("BLUE TEXT\n MUST CLICK\n I AM A STUPID ANIMAL THAT IS ATTRACTED TO COLORS")		

@run_async
def rlg(bot: Bot, update: Update):
    # reply to correct message
    eyes = random.choice(EYES)
    mouth = random.choice(MOUTHS)
    ears = random.choice(EARS)
    repl = format(ears + eyes + mouth + eyes + ears)
    update.message.reply_text(repl)
	
def decide(bot: Bot, update: Update):
        r = randint(1, 100)
        if r <= 65:
            update.message.reply_text("Yes.")
        elif r <= 90:
            update.message.reply_text("NoU.")
        else:
            update.message.reply_text("Maybe.")
            
def table(bot: Bot, update: Update):
            r = randint(1, 100)
            if r <= 45:
                update.message.reply_text("(╯°□°）╯彡 ┻━┻")
            elif r <= 90:
                update.message.reply_text("Send money bsdk to buy new table to flip")
            else:
                update.message.reply_text("Go do some work instead of flippin tables you helpless fagit.")
		
@run_async
def hug(bot: Bot, update: Update, args: List[str]):
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
	    temp = "{user1} przytula {user2}."
	    repl = temp.format(user1=user1, user2=user2)
	    reply_text(repl, parse_mode=ParseMode.MARKDOWN)

@run_async
def tyc(bot: Bot, update: Update, args: List[str]):
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
		    user2 = "@" + escape_markdown(hugged_user.username)
		else:
		    user2 = "[{}](tg://user?id={})".format(booped_user.first_name,
							   booped_user.id)
	    temp = "{user1} tyca {user2}."
	    repl = temp.format(user1=user1, user2=user2)
	    reply_text(repl, parse_mode=ParseMode.MARKDOWN)
		
@run_async
def patpat(bot: Bot, update: Update, args: List[str]):
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
	    temp = "{user1} robi *pat pat* na {user2}."
	    repl = temp.format(user1=user1, user2=user2)
	    reply_text(repl, parse_mode=ParseMode.MARKDOWN)
		
__help__ = """
 - /shrug: get shrug XD.
 - /table: get flip/unflip :v.
 - /decide: Randomly answers yes/no/maybe
 - /toss: Tosses A coin
 - /abuse: Abuses the cunt
 - /tts <any text>: Converts text to speech
 - /bluetext: check urself :V
 - /roll: Roll a dice.
 - /rlg: Join ears,nose,mouth and create an emo ;-;
 - /zal <tekst>: zalgofy! your text
 - /hug <nazwa futrzaka>: Huga futrzaka (poprzez @, lub odpowiedź)
 - /tyc <nazwa futrzaka>: tyca futrzaka (poprzez @, lub odpowiedź)
 - /patpat <nazwa futrzaka>: pat patuje futrzaka (poprzez @, lub odpowiedź)
 Dodatek Lyrics zajmie trochę czasu.
"""

__mod_name__ = "Dodatki"

ROLL_HANDLER = DisableAbleCommandHandler("roll", roll)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss)
SHRUG_HANDLER = DisableAbleCommandHandler("shrug", shrug)
BLUETEXT_HANDLER = DisableAbleCommandHandler("bluetext", bluetext)
RLG_HANDLER = DisableAbleCommandHandler("rlg", rlg)
DECIDE_HANDLER = DisableAbleCommandHandler("decide", decide)
TABLE_HANDLER = DisableAbleCommandHandler("table", table)
HUG_HANDLER = DisableAbleCommandHandler("hug", hug)
TYC_HANDLER = DisableAbleCommandHandler("tyc", tyc)
PATPAT_HANDLER = DisableAbleCommandHandler("patpat", patpat)

dispatcher.add_handler(ROLL_HANDLER)
dispatcher.add_handler(TOSS_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(BLUETEXT_HANDLER)
dispatcher.add_handler(RLG_HANDLER)
dispatcher.add_handler(DECIDE_HANDLER)
dispatcher.add_handler(TABLE_HANDLER)
dispatcher.add_handler(HUG_HANDLER)
dispatcher.add_handler(TYC_HANDLER)
dispatcher.add_handler(PATPAT_HANDLER)
