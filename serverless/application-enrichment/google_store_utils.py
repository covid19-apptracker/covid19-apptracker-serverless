from selenium import webdriver
import time
import re
from bs4 import BeautifulSoup
from commons.logger import get_logger
from commons.data_models import Permission

logger = get_logger()


def parse_app_permissions(app_permission_element):
    permission_title = None
    permission_details = []
    permission_details_new = []

    for app_permission_section in app_permission_element.children:
        if 'class' in app_permission_section.attrs:
            class_content = app_permission_section.attrs['class'][0]
            if class_content == 'wOeix':
                # Title of the permissions
                permission_title = app_permission_section.text

            elif class_content == 'GLaCt':
                # Details of the permissions
                permission_details = parse_app_permission_details(app_permission_section.children)
                permission_details_new = parse_app_permission_details_new(app_permission_section.children)

    return permission_title, permission_details, permission_details_new


def parse_app_permission_details(app_permission_details):
    permission_details = []

    for permission_detail in app_permission_details:
        if 'class' in permission_detail.attrs and permission_detail.attrs['class'][0] == 'BCMWSd':
            permission_details.append(permission_detail.text.capitalize())

    return permission_details


def parse_app_permission_details_new(app_permission_details):
    permission_details = []

    for permission_detail in app_permission_details:
        if 'class' in permission_detail.attrs and permission_detail.attrs['class'][0] == 'BCMWSd':
            permission_details.append(Permission(permission_detail.text.capitalize()))

    return permission_details


class GoogleStoreUtils:
    chrome_driver = None

    def enrich_app_information(self, application):
        """Enrich App information from the Play Store app detail page to our model.

        Keyword arguments:
        application -- Application instance
        """
        logger.info('Access google play store app details: ' + application.id)

        app_details_url = 'https://play.google.com/store/apps/details?id=%s&hl=en_US' % application.id
        self.chrome_driver.get(app_details_url)

        self.enrich_privacy_policy(application)
        self.enrich_permissions(application)

    def enrich_privacy_policy(self, application):
        logger.info('Collecting privacy policy')

        page_source = self.chrome_driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')
        privacy_policy_element = soup.find('div', text="Privacy Policy")

        if not privacy_policy_element:
            return

        match = re.search(r'href=[\'"]?([^\'" >]+)', str(privacy_policy_element))
        if match:
            application.privacy_policy = match.group(1)

    def enrich_permissions(self, application):
        logger.info('Collecting permission')

        app_permissions = {}
        app_permissions_new = {}

        self.chrome_driver.find_element_by_link_text('View details').click()
        time.sleep(5)
        page_source = self.chrome_driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        app_permission_elements = soup.findAll('div', class_="itQHhe")

        for app_permission_element in app_permission_elements:
            permission_title, permission_details, permission_details_new = parse_app_permissions(app_permission_element)
            app_permissions[permission_title] = permission_details
            app_permissions_new[permission_title] = permission_details_new

        application.permissions = app_permissions
        application.permissions_new = app_permissions_new

    def __init__(self):
        logger.info('Configuring chrome driver for accessing Google Play Store')
        # Source: https://hackernoon.com/running-selenium-and-headless-chrome-on-aws-lambda-layers-python-3-6-bd810503c6c3
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.binary_location = '/opt/headless-chromium'

        self.chrome_driver = webdriver.Chrome('/opt/chromedriver', chrome_options=chrome_options)
        logger.info('Chrome driver configured')
