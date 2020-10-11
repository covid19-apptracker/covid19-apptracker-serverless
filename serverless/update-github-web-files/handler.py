import json
from datetime import datetime

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
    new_applications = []
    updated_applications = []
    applications = dynamodb.get_all_apps()

    applications.sort(key=lambda x: x.id)

    for application in applications:
        logger.info('Processing app: %s' % application.id)

        if application.country == 'UK':
            application.country = 'GB'

        application_from_github = github_adapter.get_app_details(application)

        sort_permissions(application)
        if application_from_github is not None:
            sort_permissions(application_from_github)
        else:
            new_applications.append(application)

        if application_from_github != application:
            updated_applications.append((application_from_github, application))
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

    logger.info('Sending digest email')
    send_app_updates_email(new_applications, updated_applications)


def sort_permissions(application):
    if application.permissions is None or not application.permissions:
        return

    for permission, permission_list in application.permissions.items():
        permission_list.sort(key=lambda x: x.name)


def send_app_updates_email(new_applications, updated_applications):
    if len(new_applications) == 0 and len(updated_applications) == 0:
        logger.info('Skipping digest email, no updates')
        return

    subject = f"Covid19AppTracker updates digest"

    body = f'Digest {datetime.now().strftime("%m/%d/%Y")}' \
           f'\n' \
           f'\n' \
           f'New applications:\n' \
           f'\n'

    for application in new_applications:
        logger.info(f'Adding new app to digest {application.id}')
        body = body + f'{application.get_extended_version_json()}\n\n'

    body = body + f'\n\nUpdated applications:\n\n'

    for application_update in updated_applications:
        application_from_github = application_update[0]
        application = application_update[1]

        if set(application_from_github.permissions) != set(application.permissions):
            logger.info(f'Adding app permissions update to digest {application.id}')
            body = body + f'Application ID: {application.id}\n'
            body = body + f'Previous Dangerous count permissions: {application.dangerous_permissions_count}\n'
            body = body + f'New Dangerous count permissions: {application_from_github.dangerous_permissions_count}\n'
            body = body + f'Previous permissions:\n{json.dumps(application_from_github.permissions, indent=2)}\n'
            body = body + f'New permissions:\n{json.dumps(application.permissions, indent=2)}\n'

    email_client.send_email(subject, body)
