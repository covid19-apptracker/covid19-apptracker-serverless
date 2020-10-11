import boto3
import json
import datetime
import os
from boto3.dynamodb.conditions import Key
from commons.data_models import Application
from commons.logger import get_logger

table_name = 'Applications'
logger = get_logger()


class AwsDynamoDbClient:
    table = None
    dynamodb_client = None

    def get_by_app_id(self, app_id):
        logger.info('Retrieving app from the database: ' + app_id)
        response = self.table.query(
            KeyConditionExpression=Key('id').eq(app_id)
        )

        if len(response['Items']) == 1:
            logger.info('App found in the database:'+ app_id)
            application = Application(app_id)
            application.enrich_from_dictionary(response['Items'][0])
            return application
        logger.info('App not found in the database: ' + app_id)
        return None

    def store_app(self, application):
        logger.info('Storing the following app in the database: ' + application.id)
        self.table.put_item(
            Item=application.get_dynamodb_item()
        )

    def get_all_apps(self):
        logger.info('Retrieving all the apps from the database')
        applications = []
        response = self.table.scan()
        if response is None or len(response['Items']) == 0:
            return applications
        for response_item in response['Items']:
            application = Application()
            application.enrich_from_dictionary(response_item)
            applications.append(application)
        return applications

    def create_backup(self):
        logger.info('Creating backup of the database')
        backup_name = table_name + '_' + datetime.date.today().strftime('%Y-%m-%d')
        self.dynamodb_client.create_backup(TableName=table_name, BackupName=backup_name)
        logger.info('Backup finished: ' + backup_name)

    def __init__(self):
        dynamodb = boto3.resource("dynamodb", region_name='us-west-1')
        self.table = dynamodb.Table('Applications')
        self.dynamodb_client = boto3.client('dynamodb')


class AwsSqsClient:
    sqs = None

    AWS_REGION = os.getenv('AWS_REGION')
    AWS_ACCOUNT = os.getenv('AWS_ACCOUNT')

    applications_queue_url = f'https://sqs.{AWS_REGION}.amazonaws.com/{AWS_ACCOUNT}/applications.fifo'

    def send_message_to_applications_queue(self, application_id):
        logger.info('Sending message to the Applications queue')
        self.sqs.send_message(
            QueueUrl=self.applications_queue_url,
            MessageBody=(
                json.dumps({'id': application_id}, indent=2)
            ),
            MessageGroupId='Applications'
        )

    def __init__(self):
        self.sqs = boto3.client('sqs')


class AwsSecretsManagerClient:
    client = None

    def get_secret(self, secret):
        response = self.client.get_secret_value(SecretId=secret)

        return response['SecretString']

    def __init__(self):
        self.client = boto3.client('secretsmanager')


class AwsSsmClient:
    client = None

    def get_parameter(self, parameter):
        response = self.client.get_parameter(Name=parameter)

        return response['Parameter']['Value']

    def __init__(self):
        self.client = boto3.client('ssm')
