import argparse
import logging
import heroku3
import requests


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='install telegram bot')
    parser.add_argument(
        'heroku-api-key',
        type=str,
        help='Heroku API key. '
             'Run `heroku authorizations:create` in order to get your API key'
    )
    parser.add_argument('horoku-app-name', type=str, help='Heroku App name')
    parser.add_argument('telegram-api-token', type=str, help='Telegram bot API token')
    parser.add_argument('tenbis-location', type=str, help='10 bis office location')

    return parser.parse_args()


def configure_application(app, api_token, office_location):
    # set configuration
    config = app.config()
    config["WEBHOOK_HOST"] = app.web_url
    config["TENBIS_OFFICE_LOCATION"] = office_location
    config["TELEGRAM_API_TOKEN"] = api_token


def create_certs(app):
    pass


def deploy_heroku_bot(heroku_key, app_name, api_token, office_location):
    connection = heroku3.from_key(heroku_key)
    try:
        app = connection.app(app_name)
    except requests.HTTPError:
        logging.info(f"Creating app {app_name}")
        app = connection.create_app(app_name)

    configure_application(app, api_token, office_location)
    create_certs(app)


if __name__ == '__main__':
    arguments = parse_arguments()
    logging.info("Deploying bot on heroku")

    deploy_heroku_bot(
        arguments.heroku_api_key,
        arguments.heroku_app_name,
        arguments.telegram_api_token,
        arguments.tenbis_location
    )

