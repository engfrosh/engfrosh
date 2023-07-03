# This function runs in an AWS lambda hooked up the SNS connected to the SES inbound email traffic
# It converts to addresses on emails to web requests to the scav site

import json
import logging
import urllib3
from urllib.parse import quote

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    message = event["Records"][0]["Sns"]["Message"]
    if isinstance(message, str):
        logger.info(message)
        message = json.loads(message)
    logger.info(message)
    logger.info(type(message))
    logger.info(type(message["mail"]))
    mail = message["mail"]
    dest = mail.get("destination")
    logger.info(dest)
    http = urllib3.PoolManager()
    for d in dest:
        logger.info(d)
        if not d == "waiver@int.engfrosh.com" and not d == "logistics@engfrosh.com":
            logger.info("https://server.engfrosh.com/api/waiver?email="+quote(d, safe=''))
            http.request("GET", "https://server.engfrosh.com/api/waiver?email="+quote(d, safe=''))
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
