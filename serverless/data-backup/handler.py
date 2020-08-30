from commons.aws_adapter import AwsDynamoDbClient

dynamodb = AwsDynamoDbClient()


def backup_data(event, context=None):
    dynamodb.create_backup()
