from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
from commons.logger import get_logger
from commons.aws_adapter import AwsSsmClient

logger = get_logger()
ssm = AwsSsmClient()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = ssm.get_parameter('google_spreadsheet_id')


def get_user_entered_value(value):
    return {
        "userEnteredValue": {
            "stringValue": str(value)
        }
    }


def _preprocess_headers(applications):
    headers = [key for key in applications[0].get_dict().keys() if (key != 'permissions' and key != 'permissions_new')]

    permissions = set()
    for i in range(len(applications)):
        application_permissions = applications[i].get_dict()['permissions']
        if application_permissions is None or len(application_permissions) == 0:
            continue
        for permission_key, permission_list in list(application_permissions.items()):
            [permissions.add(permission_key + ' - ' + permission) for permission in permission_list]

    permissions = list(permissions)
    permissions.sort()
    headers.extend(permissions)

    return headers


def _preprocess_applications(headers, applications):
    application_requests = []

    for i in range(len(applications)):
        application_dict = applications[i].get_dict()
        application_permissions = application_dict.get('permissions', None)
        application_has_permissions = not (application_permissions is None or len(application_permissions) == 0)

        row_values = []

        for header in headers:
            if ' - ' not in header:
                # Not a permission column
                row_values.append(get_user_entered_value(application_dict[header]))
            else:
                # Permissions column
                permission_value = False
                if application_has_permissions:
                    permissions_search = re.search('(.*) - (.*)', header)
                    permission_key = permissions_search.group(1)
                    permission_sub_key = permissions_search.group(2)
                    application_permissions = application_dict['permissions']
                    application_permission = application_permissions.get(permission_key, None)
                    if application_permission is None or len(application_permissions) == 0:
                        pass
                    else:
                        permission_value = permission_sub_key in application_permission
                row_values.append(get_user_entered_value(permission_value))

        application_requests.append({
            "updateCells": {
                "range": {
                    "startRowIndex": i + 1,
                    "endRowIndex": i + 2
                },
                "rows": [{
                    "values": row_values
                }],
                "fields": "userEnteredValue"
            }
        })

    return application_requests


class GoogleAdapter:
    service = None

    def update_spreadsheet(self, applications):
        headers = _preprocess_headers(applications)
        application_requests = _preprocess_applications(headers, applications)

        self._write_header(headers)
        self._write_data(application_requests)

    def _write_data(self, application_requests):
        body = {
            'requests': application_requests
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        logger.info('Write data: {0} cells updated.'.format(result.get('totalUpdatedCells')))

    def _write_header(self, headers):
        requests = []

        requests.append({
            "repeatCell": {
                "range": {
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 1.0,
                            "green": 1.0,
                            "blue": 1.0
                        },
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "foregroundColor": {
                                "red": 0.0,
                                "green": 0.0,
                                "blue": 0.0
                            },
                            "fontSize": 12,
                            "bold": 'true'
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        })

        requests.append({
            "updateSheetProperties": {
                "properties": {
                    "gridProperties": {
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenRowCount"
            }
        })

        header_values = [get_user_entered_value(header.capitalize()) for header in headers]

        requests.append({
            "updateCells": {
                "range": {
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "rows": [{
                    "values": header_values
                }],
                "fields": "userEnteredValue"
            }
        })

        body = {
            'requests': requests
        }

        result = self.service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        logger.info('Write header: {0} cells updated.'.format(result.get('totalUpdatedCells')))

    def __init__(self, service_account_info):
        credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        self.service = build('sheets', 'v4', credentials=credentials)
