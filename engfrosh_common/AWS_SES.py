import boto3
import logging
import os
from botocore.exceptions import ClientError

# Specify a configuration set. If you do not want to use a configuration
# set, comment the following variable, and the
# ConfigurationSetName=CONFIGURATION_SET argument below.
# CONFIGURATION_SET = "ConfigSet"


CURRENT_DIRECTORY = os.path.dirname(__file__)
LOG_LEVEL = logging.DEBUG

# region Logging Setup
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

logger = logging.getLogger(SCRIPT_NAME)

if __name__ == "__main__":
    LOG_FILE = CURRENT_DIRECTORY + "/{}.log".format(SCRIPT_NAME)
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            pass
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE)
    logger.debug("Module started.")
    logger.debug("Log file set as: %s", LOG_FILE)

logger.debug("Set current directory as: %s", CURRENT_DIRECTORY)
# endregion


def send_SES(sender_email, recipient_email, subject, body_text, body_html):
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-2"

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient_email,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=sender_email
            # ,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        return False
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}"),


# The following section can be added to another python file (once this file is imported) to added sending
# functionality to that file.

# Uncomment the following line to import the file
# import engfrosh_common.AWS_SES as SES

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
SES_Sender = "noreply@engfrosh.com"

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
SES_Recipient = "technical@engfrosh.com"

# The subject line for the email.
SES_Subject = "This is a test subject part 2"

# The email body for recipients with non-HTML email clients.
SES_BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                 "This email was sent with Amazon SES using the "
                 "AWS SDK for Python (Boto). https://aws.amazon.com/ses/"
                 )

# The HTML body of the email. Change the body as you like
SES_BODY_HTML = """<html>
<head></head>
<body>
  <h1>Amazon SES Test (SDK for Python)</h1>
  <p>This email was sent with
    <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
    <a href='https://aws.amazon.com/sdk-for-python/'>
      AWS SDK for Python (Boto)</a>.</p>
</body>
</html>
            """

if __name__ == '__main__':
    send_SES(SES_Sender, SES_Recipient, SES_Subject, SES_BODY_TEXT, SES_BODY_TEXT)
    # SES.send_SES(SES_Sender, SES_Recipient, SES_Subject, SES_BODY_TEXT, SES_BODY_HTML)
