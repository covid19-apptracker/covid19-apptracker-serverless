from github import Github
from commons.data_models import Application
from commons.logger import get_logger
import json
import re

apps_filename = 'public/apps_data/apps.json'
apps_per_country_filename = 'public/apps_data/apps_per_country.json'
target_branch = 'master'

logger = get_logger()


def get_app_filename(application):
    return 'public/apps_data/apps_details/%s.json' % application.id


class GitHubAdapter:
    github_repo = None

    def get_apps(self):
        logger.info('Retrieving apps.json from GitHub')
        try:
            apps_file = self.github_repo.get_contents(apps_filename)
            return json.loads(apps_file.decoded_content.decode("UTF-8"))
        except Exception as e:
            return []

    def update_apps(self, apps):
        logger.info('Updating apps.json in GitHub')

        commit_message = "Update apps"
        commit_content = json.dumps(apps, indent=2)

        try:
            apps_file = self.github_repo.get_contents(apps_filename, ref=target_branch)
            self.github_repo.update_file(apps_file.path, commit_message, commit_content, apps_file.sha,
                                         branch=target_branch)
        except Exception as e:
            # Create file if it doesn't exist
            self.github_repo.create_file(apps_filename, commit_message, commit_content, branch=target_branch)

    def get_app_details(self, application):
        logger.info('Retrieving app details from GitHub: %s' % application.id)

        app_filename = get_app_filename(application)

        try:
            app_file = self.github_repo.get_contents(app_filename, ref=target_branch)
            app_dict = json.loads(app_file.decoded_content.decode("UTF-8"))
            application = Application()
            application.enrich_from_dictionary(app_dict)
            return application
        except Exception as e:
            # File if it doesn't exist
            return None

    def update_app_details(self, application):
        logger.info('Updating app details in GitHub: %s' % application.id)

        app_filename = get_app_filename(application)
        commit_message = "Update app %s" % application.id
        commit_content = application.get_extended_version_json()

        try:
            app_file = self.github_repo.get_contents(app_filename, ref=target_branch)
            self.github_repo.update_file(app_file.path, commit_message, commit_content, app_file.sha, branch=target_branch)
        except Exception:
            # Create file if it doesn't exist
            self.github_repo.create_file(app_filename, commit_message, commit_content, branch=target_branch)

    def get_apps_per_country(self):
        logger.info('Retrieving apps_per_country.json from GitHub')
        try:
            apps_per_country_file = self.github_repo.get_contents(apps_per_country_filename)
            return json.loads(apps_per_country_file.decoded_content.decode("UTF-8"))
        except Exception as e:
            return {}

    def update_apps_per_country(self, apps_per_country):
        logger.info('Updating apps_per_country.json in GitHub')

        commit_message = "Update apps per country"
        commit_content = json.dumps(apps_per_country, sort_keys=True, indent=2)

        try:
            apps_per_country_file = self.github_repo.get_contents(apps_per_country_filename, ref=target_branch)
            self.github_repo.update_file(apps_per_country_file.path, commit_message, commit_content, apps_per_country_file.sha,
                                         branch=target_branch)
        except Exception:
            # Create file if it doesn't exist
            self.github_repo.create_file(apps_per_country_filename, commit_message, commit_content, branch=target_branch)

    def tag_new_release(self):
        release_tag_pattern = re.compile(r'v(\d+)\.(\d+)\.(\d+)')

        last_release = self.github_repo.get_latest_release()
        tag_parts = release_tag_pattern.search(last_release.tag_name).groups()

        release_tag = 'v%s.%s.%s' % (tag_parts[0], tag_parts[1], (int(tag_parts[2]) + 1))

        self.github_repo.create_git_release(release_tag, 'Release new data %s' % release_tag, 'Release new data', target_commitish=target_branch)

    def __init__(self, token):
        g = Github(token)
        self.github_repo = g.get_repo('family-hackathon/covid19-apptracker')
