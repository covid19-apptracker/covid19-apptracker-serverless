import json

from gh_adapter import GitHubAdapter
from google_adapter import GoogleAdapter
from commons.aws_adapter import AwsDynamoDbClient
from commons.aws_adapter import AwsSecretsManagerClient
from commons.aws_adapter import AwsSesClient
from commons.logger import get_logger

dynamodb = AwsDynamoDbClient()
secretsmanager = AwsSecretsManagerClient()
email_client = AwsSesClient()
github_adapter = GitHubAdapter(secretsmanager.get_secret('github_token'))
googleAdapter = GoogleAdapter(json.loads(secretsmanager.get_secret('google_api')))
logger = get_logger()


def update_github_files(event, context=None):
    tag_new_release = False
    applications = dynamodb.get_all_apps()

    applications.sort(key=lambda x: x.id)

    for application in applications:
        logger.info('Processing app: %s' % application.id)

        if application.country == 'UK':
            application.country = 'GB'

        application_from_github = github_adapter.get_app_details(application)

        sort_permissions(application)
        if application_from_github is not None:
            send_new_app_email(application)
            sort_permissions(application_from_github)

        if application_from_github != application:
            send_update_app_email(application_from_github, application)
            github_adapter.update_app_details(application)
            tag_new_release = True

    logger.info('Updating apps.json')

    apps = github_adapter.get_apps()
    updated_apps = [application.get_short_version_dict() for application in applications]
    updated_apps.sort(key=lambda x: x['id'])

    if apps != updated_apps:
        github_adapter.update_apps(updated_apps)
        tag_new_release = True

    logger.info('Updating apps_per_country.json')

    apps_per_country = github_adapter.get_apps_per_country()
    updated_apps_per_country = {}

    for application in applications:
        updated_apps_per_country[application.country] = updated_apps_per_country.get(application.country, 0) + 1

    if apps_per_country != updated_apps_per_country:
        github_adapter.update_apps_per_country(updated_apps_per_country)
        tag_new_release = True

    logger.info('Tagging a new release')

    if tag_new_release:
        github_adapter.tag_new_release()

    logger.info('Updating Google Spreadsheet')
    googleAdapter.update_spreadsheet(applications)


def sort_permissions(application):
    if application.permissions is None or not application.permissions:
        return

    for permission, permission_list in application.permissions.items():
        permission_list.sort()


def send_update_app_email(application_from_github, application):
    subject = f"Application updated {application.id}"
    body = application.get_extended_version_json()
    email_client.send_email(subject, body)


def send_new_app_email(application):
    subject = f"New application found {application.id}"
    body = application.get_extended_version_json()
    email_client.send_email(subject, body)
