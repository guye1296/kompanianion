import tenbis
import config
import enum
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext
)


class State(enum.IntEnum):
    PICK_RESTAURANT = 1,
    ELIMINATE_RESTAURANT = 2,


def start_pick(update: Update, context: CallbackContext) -> State:
    context.chat_data["tenbis"] = tenbis.Session(config.TENBIS_OFFICE_LOCATION)
    context.chat_data["choices"] = []

    return prompt_pick(update, context)


def show_help(update: Update, context: CallbackContext) -> State:
    update.message.reply_text(
        ""
        "/pick pick a random restaurant\n"
        "/help show this message\n"
        ""
    )
    return ConversationHandler.END


def prompt_pick(update: Update, context: CallbackContext) -> State:
    reply_keyboard = [[
        context.chat_data["tenbis"].get_random_restaurant().name for
        _ in
        range(3)
    ]]

    update.message.reply_text(
        f"Pick a restaurant, {5 - len(context.chat_data['choices'])} remaining...",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return State.PICK_RESTAURANT


def prompt_eliminate(update: Update, context: CallbackContext) -> State:
    reply_keyboard = [[choice.name for choice in context.chat_data["choices"]]]

    update.message.reply_text(
        f"Eliminate a restaurant, {len(context.chat_data['choices'])} remaining...",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return State.ELIMINATE_RESTAURANT


def prompt_winning(update: Update, context: CallbackContext) -> State:
    assert 1 == len(context.chat_data["choices"])
    update.message.reply_text(
        "Restaurant chosen!\n",
        reply_markup=ReplyKeyboardRemove()
    )

    try:
        restaurant = context.chat_data["choices"][0]
        update.message.reply_photo(photo=restaurant.photo_url, caption=str(restaurant))

    # TODO: catch exception if there is no photo
    except Exception as e:
        update.message.reply_text("Internal error")

    del context.chat_data["choices"]

    return ConversationHandler.END


def handle_pick_restaurant(update: Update, context: CallbackContext) -> State:
    text = update.message.text

    if text.endswith('!'):
        choice = tenbis.restaurant_from_str(text[:text.find('!')])
    else:
        choice = context.chat_data["tenbis"].search_restaurant(text)

    if choice is None:
        update.message.reply_text(f"Could not find restaurant {text}")
        return prompt_pick(update, context)

    context.chat_data["choices"].append(choice)

    if 5 == len(context.chat_data["choices"]):
        return prompt_eliminate(update, context)
    else:
        return prompt_pick(update, context)


def handle_eliminate_restaurant(update: Update, context: CallbackContext):
    text = update.message.text
    choice = next((c for c in context.chat_data["choices"] if text.strip() in c.name), None)

    if choice is None or choice not in context.chat_data["choices"]:
        update.message.reply_text(f"Not an existing restaurant. Choose from the ones in chat")
        return prompt_eliminate(update, context)

    context.chat_data["choices"].remove(choice)

    if 1 == len(context.chat_data["choices"]):
        return prompt_winning(update, context)
    else:
        return prompt_eliminate(update, context)


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Shutting down...")
    return ConversationHandler.END


def pick_restaurant_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('pick', start_pick)],
        states={
            State.PICK_RESTAURANT: [MessageHandler(Filters.text, handle_pick_restaurant)],
            State.ELIMINATE_RESTAURANT: [MessageHandler(Filters.text, handle_eliminate_restaurant)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )


def help_handler():
    return CommandHandler('help', show_help)

