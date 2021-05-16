import telebot
import tenbis
import flask
import config
import time
import logging


_app = flask.Flask(__name__)
_bot = telebot.TeleBot(config.API_TOKEN)
_tenbis_session = tenbis.Session(config.TENBIS_OFFICE_LOCATION)


class Session:
    """
    A session to a _bot given a chat id
    """
    def __init__(self, chat_id):
        self._chat_id = chat_id
        self._next = self._route
        self._choices = []

    def handle(self, message: telebot.types.Message):
        logging.info(f"{self._chat_id}: {message.text}")
        return self._next(message)

    def _route(self, message: telebot.types.Message):
        if message.text == '/usage':
            return self._usage(message)
        elif message.text == '/start':
            return self._usage(message)
        elif message.text == '/help':
            return self._usage(message)
        elif message.text == '/random':
            return self._random(message)
        elif message.text == '/search':
            return self._prompt_search(message)
        elif message.text == '/pick':
            return self._prompt_pick_restaurant()

    def _send_restaurant_description(self, restaurant: tenbis.Restaurant):
        try:
            _bot.send_photo(self._chat_id, photo=restaurant.photo_url, caption=str(restaurant))
        except telebot.apihelper.ApiTelegramException:
            logging.error(f"URL {restaurant.photo_url} not valid :(")
            _bot.send_message(self._chat_id, str(restaurant))

    def _prompt_search(self, message: telebot.types.Message):
        _bot.send_message(self._chat_id, "Type part of the restaurant to search for...")
        self._next = self._search

    def _search(self, message: telebot.types.Message):
        query = message.text
        result = _tenbis_session.search_restaurant(query)
        if result is None:
            _bot.send_message(self._chat_id, f"Could not find any restaurant containing:\t{query}")
        else:
            self._send_restaurant_description(result)

        self._next = self._route

    def _random(self, message: telebot.types.Message):
        choice = _tenbis_session.get_random_restaurant()
        self._send_restaurant_description(choice)

    def _prompt_pick_restaurant(self):
        markup = telebot.types.ReplyKeyboardMarkup()
        buttons = [
            telebot.types.KeyboardButton(_tenbis_session.get_random_restaurant().name) for
            _ in
            range(3)
        ]
        markup.add(*buttons)

        _bot.send_message(
            self._chat_id, f"Pick a restaurant, {5 - len(self._choices)} remaining...", reply_markup=markup
        )
        self._next = self._handle_pick

    def _prompt_eliminate_restaurant(self):
        markup = telebot.types.ReplyKeyboardMarkup()
        buttons = [
            telebot.types.KeyboardButton(choice.name) for
            choice in
            self._choices
        ]
        markup.add(*buttons)

        _bot.send_message(
            self._chat_id, f"Eliminate a restaurant, {len(self._choices)} remaining...", reply_markup=markup
        )
        self._next = self._handle_elimination

    def _handle_pick(self, message: telebot.types.Message):
        if message.text.endswith('!'):
            choice = tenbis.restaurant_from_str(message.text[:message.text.find('!')])
        else:       
            choice = _tenbis_session.search_restaurant(message.text)


        if choice is None:
            _bot.send_message(self._chat_id, f"Could not find restaurant {message.text}")
            self._prompt_pick_restaurant()
            return
        self._choices.append(choice)

        if 5 == len(self._choices):
            self._prompt_eliminate_restaurant()
        else:
            self._prompt_pick_restaurant()

    def _handle_elimination(self, message: telebot.types.Message):
        choice = next((c for c in self._choices if message.text.strip() in c.name), None)
        
        if choice is None or choice not in self._choices:
            _bot.send_message(self._chat_id, f"Not an existing restaurant. Choose from the ones in chat")
            self._prompt_eliminate_restaurant()
            return

            
        self._choices.remove(choice)

        if 1 == len(self._choices):
            self._prompt_winning_restaurant()
        else:
            self._prompt_eliminate_restaurant()

    def _prompt_winning_restaurant(self):
        assert 1 == len(self._choices)
        _bot.send_message(self._chat_id, "Restaurant chosen!\n")
        self._send_restaurant_description(self._choices[0])
        self._choices.clear()
        self._next = self._route

    def _usage(self, message: telebot.types.Message):
        _bot.reply_to(message, "Usage:\n"
                              "/random : select a random restaurant\n"
                              "/search : search a restaurant\n"
                              "/pick : pick a restaurant gladiator style!\n"
                              "/help | /usage : show this message\n"
                     )


# TODO: terminate session after inactivity
_sessions = {}


@_bot.message_handler()
def route_message(message: telebot.types.Message):
    # add to existing list of user sessions
    try:
        session = _sessions[message.chat.id]
    except KeyError:
        logging.info(f"Creating session {message.chat.id}")
        session = Session(message.chat.id)
        _sessions[message.chat.id] = session

    return session.handle(message)


# Empty webserver index, return nothing, just http 200
@_app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@_app.route(config.WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        _bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def run():
    _bot.remove_webhook()
    time.sleep(0.1)

    _bot.set_webhook(
        url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH,
    )

    _app.run(
        host=config.WEBHOOK_LISTEN,
        port=config.WEBHOOK_PORT,
    )
