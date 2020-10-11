import play_store_search
from commons.aws_adapter import AwsDynamoDbClient
from commons.aws_adapter import AwsSqsClient
from commons.aws_adapter import AwsSsmClient
from commons.logger import get_logger
import constants

dynamodb = AwsDynamoDbClient()
queue = AwsSqsClient()
ssm = AwsSsmClient()
logger = get_logger()


def search_google_play_store(event, context=None):
    search_terms = ssm.get_parameter('google_search_term')

    for search_term in search_terms.split(','):
        logger.info('Google Search Term: ' + search_term)
        app_ids = play_store_search.get_apps_ids(search_term)

        logger.info('Applications found in the Play Store: ' + str(len(app_ids)))

        for app_id in app_ids:
            if app_id in constants.ignore_apps:
                logger.info('Ignoring the following app: ' + app_id)
                continue

            if dynamodb.get_by_app_id(app_id) is None:
                logger.info('New application found: ' + app_id)
                # New Application found send message to queue to enrich application data
                queue.send_message_to_applications_queue(app_id)
