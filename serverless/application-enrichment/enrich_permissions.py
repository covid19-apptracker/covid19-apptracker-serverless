from selenium import webdriver
import time
from bs4 import BeautifulSoup
from commons.logger import get_logger

logger = get_logger()


def parse_app_permissions(app_permission_element):
    permission_title = None
    permission_details = []

    for app_permission_section in app_permission_element.children:
        if 'class' in app_permission_section.attrs:
            class_content = app_permission_section.attrs['class'][0]
            if class_content == 'wOeix':
                # Title of the permissions
                permission_title = app_permission_section.text
            elif class_content == 'GLaCt':
                # Details of the permissions
                permission_details = parse_app_permission_details(app_permission_section.children)

    return permission_title, permission_details


def parse_app_permission_details(app_permission_details):
    permission_details = []

    for permission_detail in app_permission_details:
        if 'class' in permission_detail.attrs and permission_detail.attrs['class'][0] == 'BCMWSd':
            permission_details.append(permission_detail.text.capitalize())

    return permission_details


class PermissionsEnricher:
    chrome_driver = None

    def get_app_permissions(self, app_id):
        """Scrape App permissions from the Play Store app detail page to our model.
        Returns a dictionary with the permissions

        Keyword arguments:
        app_id -- Play Store app id
        :rtype: dict
        """
        logger.info('Collecting permissions from the following app:', app_id)

        app_permissions = {}
        app_details_url = 'https://play.google.com/store/apps/details?id=%s&hl=en_US' % app_id

        self.chrome_driver.get(app_details_url)
        self.chrome_driver.find_element_by_link_text('View details').click()

        time.sleep(5)

        page_source = self.chrome_driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        app_permission_elements = soup.findAll('div', class_="itQHhe")
        for app_permission_element in app_permission_elements:
            permission_title, permission_details = parse_app_permissions(app_permission_element)
            app_permissions[permission_title] = permission_details

        return app_permissions

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
