import argparse
import logging
import heroku3
import requests


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='install telegram bot')
    parser.add_argument(
        '--heroku-api-key',
        type=str,
        help='Heroku API key. '
             'Run `heroku authorizations:create` in order to get your API key'
    )
    parser.add_argument('--heroku-app-name', type=str, help='Heroku App name')
    parser.add_argument('--telegram-api-token', type=str, help='Telegram bot API token')
    parser.add_argument('--tenbis-location', type=str, help='10 bis office location')
    parser.add_argument('--webhook-port', type=int, choices=[80, 88, 443, 8443])

    return parser.parse_args()


def configure_application(app, api_token, office_location, port):
    # set configuration
    app.update_config({
        "WEBHOOK_HOST": app.domains()[0].hostname,
        "WEBHOOK_PORT": port,
        "TENBIS_OFFICE_LOCATION": office_location,
        "TELEGRAM_API_TOKEN": api_token
    })


def deploy_heroku_bot(heroku_key, app_name, api_token, office_location, port):
    connection = heroku3.from_key(heroku_key)
    try:
        app = connection.app(app_name)
    except requests.HTTPError as e:
        logging.info(f"Creating app {app_name}")
        app = connection.create_app(app_name)

    configure_application(app, api_token, office_location, port)
    app.restart()


if __name__ == '__main__':
    arguments = parse_arguments()
    logging.info("Deploying bot on heroku")

    deploy_heroku_bot(
        arguments.heroku_api_key,
        arguments.heroku_app_name,
        arguments.telegram_api_token,
        arguments.tenbis_location,
        arguments.webhook_port
    )

