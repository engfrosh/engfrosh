# Deploying to AWS

### Deploy an AWS EC2 Server

# Note this is subject to change as we look into AWS docker options

- Ubuntu 22.04
    - Tested, others may work
- Tested on t2.micro (free), actual production deployment may require more powerful
    - the cheapest is t3a.nano which should be fine for staging
- EBS storage,
    - gp3,
    - size 10 (for now),
    - Encryption, default key is fine
    - leave the other defaults
- Add a security group with SSH, HTTP, and HTTPS
    - Note, if you are recreating a server, you will probably need to clear the entry in ~/.ssh/known_hosts
- Add or create a new key pair


### Once Launched
- Create an elastic IP and assign it
- add IP to DNS as a subdomain


### Installing Docker (Ubuntu)

```sh
sudo apt-get install docker.io
sudo systemctl enable docker
sudo systemctl start docker
```

### Clone the engfrosh-docker repo

```
$ git clone https://github.com/engfrosh/engfrosh-docker.git
```

After running `rebuild.sh` each of these containers will be started and configured to start on boot

### Run Build On Database Container

```sh
cd ~/engfrosh-docker/postgresql/
sudo ./rebuild.sh
```

When prompted for a database password choose a good password for the `postgres` account

Next initialize the database with the following command

```sh
sudo ./setup.sh
```

The DB is now configured

### Run Build On Site Container

```sh
cd ~/engfrosh-docker/engfrosh-site/
```

Now copy `environment.example` to `environment` and fill in all variables
Also copy `credentials.example` to `credentials` and fill in all variables

```sh
sudo ./rebuild.sh
sudo ./setup_ssl.sh
sudo docker exec -it engfrosh python3 /home/ubuntu/engfrosh/engfrosh_site/manage.py createsuperuser
```

Note that it is safe to ignore the errors from nginx before `setup_ssl.sh` is called as it will be unable to find the SSL certificates

After SSL is setup you need to run

```sh
sudo docker restart engfrosh
```

### Run Build On Discord Bot Container

```sh
cd ~/engfrosh-docker/discord-bot/
```

Now copy `environment.example` to `environment` as well as `example_configs.py` to `configs.py` and fill in all variables

```sh
sudo ./rebuild.sh
```

### Run 

#### Management Commands:

To stop the EngFrosh site, type:

```
sudo docker stop engfrosh
```
To start the site when stopped, type:
```
sudo docker start engfrosh
```
To stop and then start the site, type:
```
sudo docker restart engfrosh
```

## Discord Bot (Not Dockerized)
Add a `credentials.json` to the engfrosh_bot folder based on the template.

Make sure to change the bot config to the production one.

### Creating Discord Credentials

Create a new discord application [here](https://discord.com/developers/applications)

Under OAuth2 add the redirects:
```
https://mars.engfrosh.com/accounts/login/discord/callback/
https://mars.engfrosh.com/accounts/register/discord/callback/
```
<!-- For development user the callbacks:
```
http://localhost:8000/accounts/register/discord/callback/
http://localhost:8000/accounts/login/discord/callback/
```
 -->

Copy your client id and client secret to the credentials.py in the engfrosh_site folder.

Got to bot and add it as a bot.
- Copy the token to the `credentials.json` file in the engfrosh_bot folder.
- update the database credentials as well in that file
- Uncheck public bot

- Go back to OAuth and check bot, then administrator (for now) and then use the link to add the bot to your server.

- For your discord server, make it a community server is desired.


- Give the needed permissions to the discord bot on the database.
- Add the needed database entries such as the enable scavenger setting.

- make sure it is up and running properly

Add it as a service.
Add to `/etc/systemd/system/engfrosh_bot.service`
```
[Unit]
Description=EngFrosh Discord Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/engfrosh
ExecStart=python3 -m engfrosh_bot

[Install]
WantedBy=multi-user.target
```

Then run
```
systemctl start engfrosh_bot
```
and check that the bot is indeed running
```
systemctl enable engfrosh_bot
```
so that it runs at start up.

You may also want to change the service file permissions so non root can control them.

#### Add AWS Credentials

- Create an IAM role if one has not already been created, it should only have the ability to send SES messages

### Updating Site

_When you make changes to the git repo, you at some point want to put these on the testing
or production server. The following instructions are how to update an already running site._

- SSH into the server
- Rebuild the desired service
    - Changes to the credentials/environment files as well as changes in the git repo are updated on rebuild
    - To rebuild a container `cd` to the correct directory for the desired application (eg `engfrosh-docker/engfrosh-site`, etc) and run `sudo ./rebuild.sh`
