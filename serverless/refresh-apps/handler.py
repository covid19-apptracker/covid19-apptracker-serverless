from commons.aws_adapter import AwsDynamoDbClient
from commons.aws_adapter import AwsSqsClient
from commons.logger import get_logger

dynamodb = AwsDynamoDbClient()
queue = AwsSqsClient()
logger = get_logger()


def refresh_apps(event, context=None):
    applications = dynamodb.get_all_apps()

    applications.sort(key=lambda x: x.id)

    for application in applications:
        logger.info('Processing app: %s' % application.id)
        queue.send_message_to_applications_queue(application.id)
