import datetime
import json
import urllib.parse

import play_scraper
from commons.aws_adapter import AwsDynamoDbClient
from commons.data_models import Application
from commons.logger import get_logger

import enrich_country
import enrich_permissions

permissions_enricher = enrich_permissions.PermissionsEnricher()
dynamodb = AwsDynamoDbClient()
logger = get_logger()


def enrich_application(event, context=None):
    app_id = json.loads(event['Records'][0]['body'])['id']

    logger.info('Processing application %s' % app_id)

    application = dynamodb.get_by_app_id(app_id)

    if application is not None:
        # Existing application
        logger.info('Application %s was already in the system, checking for updates' % application.id)

        updated_application = get_data_from_play_store(application.id)

        if updated_application is None:
            # App is not available anymore
            logger.info('Application %s is not available on the store anymore, updating information' % application.id)
            application.available = False
            dynamodb.store_app(application)
        else:
            # Check if data has changed
            updated_application.country = application.country
            updated_application.first_time_seen = application.first_time_seen
            if application == updated_application:
                logger.info('Application %s has not changed since last check' % application.id)
            else:
                logger.info('Application %s has changed since last check, updating information' % application.id)
                dynamodb.store_app(updated_application)
    else:
        # New application
        application = get_data_from_play_store(app_id)
        application.first_time_seen = datetime.date.today().strftime('%Y-%m-%d')
        if application is not None:
            dynamodb.store_app(application)


def get_data_from_play_store(application_id):
    application = None

    try:
        play_store_app_data = play_scraper.details(application_id)
        application = map_app_from_play_store(play_store_app_data)
    except Exception as err:
        logger.error("Error getting data from the play store: {0}".format(err))

    return application


def map_app_from_play_store(play_store_app_data):
    """Map information of the App from the Play Store to our model.
    Returns an Application object

    Keyword arguments:
    play_store_app_data -- Play Store app data
    """

    application = Application(play_store_app_data['app_id'])

    application.title = play_store_app_data['title']
    application.icon_url = play_store_app_data['icon']
    application.developer_id = urllib.parse.unquote(play_store_app_data['developer_id'].replace('+', ' '))
    application.downloads = play_store_app_data['installs']
    application.description = play_store_app_data['description'].replace('\n', ' ')
    application.app_store_url = play_store_app_data['url']
    application.developer_url = play_store_app_data['developer_url']

    application.updated_date = parse_date(play_store_app_data['updated'])

    application.country = enrich_country.enrich_app_country(
        application.id,
        application.description,
        application.developer_url
    )

    application.permissions = permissions_enricher.get_app_permissions(
        application.id
    )

    return application


def parse_date(original_date):
    return datetime.datetime.strptime(original_date, '%B %d, %Y').strftime('%Y-%m-%d')
