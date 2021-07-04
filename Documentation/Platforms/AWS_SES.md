# AWS SES

##Notes
### AWS Account Limitations
- By default, an AWS may be in the "Amazon SES sandbox." This limits to whom you can send an email (verified emails only).
- More info about this, as well as how to move out of the sandbox can be found here: 
  https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html

### Credentials Note 
- In order to use boto3 (AWS's python library) locally, you must add a credentials file for authentication.
- Instructions on how to create this file can be found here: 
  https://docs.aws.amazon.com/ses/latest/DeveloperGuide/create-shared-credentials-file.html
  - This file MAY be able to be moved, depending on the situation, however I have not looked into it as it seems 
    unnecessary. However, this link may help should you wish to do so:
    https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
- As always with these types of files, make sure you do not add it to your GIT/VCS, or you may have a bad time when 
  someone starts using your account without permission.
  
## Usage
