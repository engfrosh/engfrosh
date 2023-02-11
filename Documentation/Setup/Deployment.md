# Deployment procedure

## [1](#ec2-setup) - Deploy an AWS EC2 server
## [2](#server-configuration) - Configure the server
## [3](#testing) - Testing information
## [4](#discord-commands) - Discord Commands
# EC2 Setup

### Note this is subject to change as we look into AWS docker options

Type:
    - Head's day and other small events should use a t3a.nano or similar type
    - Full deployment for the week should use a t3a.micro or above
OS: Ubuntu 22.04
    - Tested, others may work
EBS storage:
    - gp3,
    - size 10-20,
    - Encryption, default key is fine
    - leave the other defaults

- Add a security group with SSH, HTTP, and HTTPS
    - Note, if you are recreating a server, you will probably need to clear the entry in ~/.ssh/known_hosts
- Add or create a new key pair


## Once Launched
- Create an elastic IP and assign it
- add IP to DNS as a subdomain

# Server Configuration

### Note: The EBS volume will fill up with frequent docker rebuilds so ensure you have a script running `docker system prune` that is run by cron frequently

## Setup the database

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
cd ~/engfrosh-docker/mariadb/
sudo ./rebuild.sh
```

When prompted for a database password choose a good password for the `root` account

Next initialize the database with the following command

```sh
sudo ./setup.sh
```

The DB is now configured

#### Note: If you ever need to manually access the DB run `docker exec -it mariadb mysql -u root -p` and enter the root password to enter a SQL shell

## Setup the EngFrosh site

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

Follow the prompts to setup the initial admin user

#### Note: that it is safe to ignore the errors from nginx before `setup_ssl.sh` is called as it will be unable to find the SSL certificates

After SSL is setup you need to run

```sh
sudo docker restart engfrosh
```

See [site configuration](#site-config) for information on how to use the site

## Setup the Discord bot

### Run Build On Discord Bot Container

```sh
cd ~/engfrosh-docker/discord-bot/
```

Now copy `environment.example` to `environment` as well as `example_configs.py` to `configs.py` and fill in all variables

See the discord credentials section below for info about creating an application

```sh
sudo ./rebuild.sh
```

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
- Copy the token to the `environment` file in the engfrosh_docker for both the site and discord bot folder.
- Uncheck public bot

- Go back to OAuth and check bot, then administrator (for now) and then use the link to add the bot to your server.

- For your discord server, make it a community server if desired.

- make sure it is up and running properly

#### Add AWS Credentials

- Create an IAM role if one has not already been created, it should only have the ability to send SES messages

### Updating Site

_When you make changes to the git repo, you at some point want to put these on the testing
or production server. The following instructions are how to update an already running site._

- SSH into the server
- Rebuild the desired service
    - Changes to the credentials/environment files as well as changes in the git repo are updated on rebuild
    - To rebuild a container `cd` to the correct directory for the desired application (eg `engfrosh-docker/engfrosh-site`, etc) and run `sudo ./rebuild.sh`

# Site Config

Most things can be done through the UI at [https://mars.engfrosh.com/manage](https://mars.engfrosh.com/manage)

If anything is really broken or is unable to be modified through the site, see the management commands below

## Configuration Files (Discord Bot)

The `config/<mode>.yaml` and `config/base.yaml` files in the git repo are used for configuring some static options. They need to be reloaded with a full rebuild of the bot.

This is where you enter options like message ids for robert and channels/roles for automated messages or admin permissions

## Management Commands:

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

## Logging

To access the logs for any service run `sudo docker logs <engfrosh,discord-bot,mariadb>`

The discord bot will output information about almost anything the bot does with log level `INFO`. This will show up in the docker logs using the command above which can be useful for debugging

The site access and error log can be accessed by running `sudo docker exec -it engfrosh less /var/log/nginx/access.log` or `error.log`. Although this will NOT give any information about the Django application and the docker logs must be used to view stack traces or any other debug info

## Site Usage

### User Setup

Go to the admin UI with the link above and log in with the admin user using the `Login as staff` button.

Teams are created through the `Manage Teams` page. To create a team click `Add Team` and the site will prompt you for the name.
Clicking the + icon below `Discord Role?` will cause the site to create a role in the linked Discord server for this team and create a `DiscordRole` database entry linking them

User management is done through the `Add Users` page. Users can be added by uploading a CSV file (example file is in the root folder of this repo) or manually

All planning members should have the staff flag set so they can access some elements of the admin panel. To do this navigate to the admin panel, click the `Users` tab, click on the user then select the `Staff status` checkbox and hit save.

When users are ready to be emailed, go to the `Magic Links` page and click the `Email 50` button in the top left to send out a magic link to the first 50 users on the list.
This magic link will allow a user to log in once and then link their Discord account for future logins. This magic link will also automatically make the user join the Discord server.

If you need to manually make someone join the server, the `Add Users To Guild` button will allow you to force users to join the server.

### Permission/Group Setup

Groups will have to be manually changed to have the correct permissions. These permissions are synced between the site and bot so it is important to get them right.

Go to the `Groups` tab on the admin panel, click on the desired group and use the arrows to move permissions to the chosen permissions side, then hit save.

`Facil` and `Head` groups will need the `Can guess for scavenger` permission

Create a `Spirit` group that will need the `Can manage scav` permission and depending on how much time there is to train Spirit on how to use the site they can be given access to view and edit teams, puzzles, etc

### Scavenger Setup

Click the `Initialize Database` button.

Go to `Server Admin` and make sure under `Boolean Settings` that `SCAVENGER_ENABLED` is set to `False` (or a red X). If it is not then click the name and you are able to change it and save.

Under `Scavenger Puzzle Streams` (in the admin panel) you must create a stream through the `add scavenger puzzle stream` button.
You can give it any name you'd like and set it to enabled so you can start adding puzzles to it.

Under `Scavenger Puzzles` (in the admin panel) you can add puzzles through the `add scavenger puzzle` button.

The fields for each puzzle are:

Name: The name of the puzzle THAT IS SHOWN TO THE USERS. This is required
Answer: The correct answer to the puzzle
Require photo upload: If this is false then scavenger puzzle responses will be automatically approved, mostly used for Head's Day
Enabled: Controls if the puzzle is active, it will be skipped if it is disabled. WARNING: If disabling puzzles while scav is in progress ensure no teams are currently on the puzzle or they will get stuck (see fixing scav below)
Order: Controls the order of the puzzles, in ascending order. Note: This field allows decimals to make it easy to move puzzles around
Stream: Which set of puzzles this belongs to (you can have multiple different "streams" of puzzles that teams can be on). Just set this to the stream created before
QR Code: DO NOT TOUCH THIS. It will be automatically generated
Text: The text to display for the puzzle, this is optional
Puzzle file: The puzzle to display for this puzzle. Can be an image or any other kind of file
Puzzle file display filename: If the puzzle is not an image you can change what the file name is displayed as (otherwise it is random)
Puzzle file download: Makes the puzzle file downloadable
Puzzle file is image: Displays the puzzle file as an image

When Spirit is ready to open scav, go back to the `Boolean Settings` menu and flip `SCAVENGER_ENABLED` to `True`

#### NOTE: If you setup the scavenger puzzles after creating the teams they will all be broken

This isn't a big problem just the team puzzle activities will need to be created. This can be done manually or with the `Initialize Scavenger` button.

### Fixing Scav

#### Teams are stuck in lockout

If teams are stuck in lockout it is probably an issue with timezones of the site vs DB vs discord bot. To fix this either use the `scav_unlock` command in Discord or click `Teams` under the admin panel, select the team that is locked out, then delete everything in the `Scavenger locked out until` field and hit save. Spirit should also be able to use this command so tell them to manually unlock scav until it is fixed.

#### Teams are stuck on a disabled puzzle

If teams are stuck on a puzzle that has been disabled go to `Team Puzzle Activities` in the admin panel and locate the activity for the stuck team that is marked as not completed. Edit it and manually set the puzzle to be the next puzzle in the stream then hit save.

# Testing

Always test the site before rebuilding the site and putting it into production. If there are major issues the build will usually fail which will leave the current site running but try to be sure it will work before that. It is best practice to run the docker build in your dev environment first as a test.

All testing must be done manually as it is very difficult to unit test what is basically just a UI. It is a good idea to create a test plan and follow it for all testing.

When testing ensure you include as many edge cases as possible, some good ones to start on are:
- Scav puzzles with verification disabled

# Discord Commands

The Discord bot is able to directly interact with the site's DB and can do a lot of management of the system.

The current list of commands is:
## add_overwrite

Permission: `admin`

This command adds a permission overwrite to a discord channel. It's usage is `/add_overwrite <channel id> <@ role> <name eg read_messages, etc> <value eg True/False>`.
All the permissions are able to be found at [the Nextcord permission docs](https://docs.nextcord.dev/en/stable/api.html#permissions)

## add_pronoun

Permission: `admin`

This adds a pronoun to a user and changes their nickname to reflect it. It's usage is `/add_pronoun <@ user> <emote from pronoun message>`.

## change_nick

Permission: `admin`

This adds a nickname override to a user and forces the bot to not modify it in ANY WAY. If nicknames are changed through Discord manually they will be reset by the bot if the user selects pronouns or any other action is performed modifying their name. It's usage is `/change_nick <@ user> <nick>`

## channels

Permission: `admin`

This command shows a list of every channel on the server and their channel id. It's usage is `/channels`

## clear_nick

Permission: `admin`

This command resets a user's nickname to THE BOT's default nickname for the user `First Last (Pronouns)`. The usage for this is `/clear_nick <@ user>`

## create_channel

Permission: `common_models.create_channel`

This command creates a private channel in a given category and sets permissions on it. It's usage is `/create_channel <category id> <name> <allowed roles, space seperated>`

## create_group

Permission: `common_models.create_channel`

This command creates a group channel between two roles. It's usage is `/create_group <roles space seperated>`.
It will put the channel in the first group's category and it will be named `group1-group2-...`

## create_invite

Permission: `common_models.create_invite`
WARNING: This permission can be used to generate invite links with admin access

This command creates a custom invite to the server that will assign roles and a nickname to a user. In the future it will also automatically link accounts on the site as well. It's usage is `/create_invite <@ role> [optional nickname]`

## create_role

Permission: `common_models.create_role`

This command creates a role, it's category, and it's own channel. It's usage is `/create_role <name>`

## create_user

Permission: `admin`

This command creates a user on the site's backend. It's usage is `/create_user <@ user> <first name> <last name>`

## deleteoverwrite

Permission: `admin`

This command deletes an overwrite from a channel. It is very useful if you accidentally lock yourself out of a channel. It's usage is `/deleteoverwrite <channel id> <@ role>`

## echo

Permission: `admin`

This command makes the bot echo text. Its not super useful and is mostly just a fun thing. It's usage is `/echo <text>`

## guess

Permission: `common_models.guess_scavenger_puzzle`

This command allows a user to attempt to complete a scavenger puzzle. It's usage is `/guess <answer> [optional verification photo]`

## hint

Permission: `None`

This command allows a user to request a hint for scav. It's usage is `/hint`

## import_users

Permission: `admin`

This command allows you to add a bunch of users from a CSV file to the discord server and assign roles and nicknames without going through the site. It will also send emails with discord links to all of them but will not import them into the site's backend. It's usage is `/import_users <csv file>`

The columns of this CSV file must be `Nickname | Role Name | E-Mail`

## overwrites

Permission: `admin`

This command lists all of the current overwrites on a channel. It's usage is `/overwrites <channel id>`

## pronoun_create

Permission: `admin`

This command creates a pronoun and binds it to an emoji so it can be added to the pronoun selection message. It's usage is `/pronoun_create <name> <emoji>`

Note: This will not regenerate the pronoun selection message and that has to be done with the `send_pronoun_message` command

## purge

Permission: `common_models.purge_channels`

This command deletes all the messages in a channel. It's usage is `/purge [optional channel id]`

## question

Permission: `None`

This command shows the current scav question your team is on. It's usage is `/question`

## remove_pronoun

Permission: `admin`

This command removes a pronoun from a user. It's usage is `/remove_pronoun <@ user> <emoji from pronoun message>`

## rename

Permission: `admin`

This command renames a channel. It's usage is `/rename <channel id> <new name>`

## rename_all

Permission: `admin`

This command resets every user's nickname to THE BOT's DEFAULT name. This is by default `First Last (Pronouns)` although this will not effect users with nickname overrides set. It's usage is `/rename_all`

## robert_add

Permission: `None`

This command adds to the robert queue. It's usage is `/robert_add <1-3>`

## robert_message

Permission: `admin`

This command creates the message that the bot will edit to show the robert queue. It's usage is `/robert_message`.

Note: This message will have to be marked as the robert message through the bot's config

## robert_next

Permission: `None`

This command pops the top point of the robert queue and displays it. It's usage is `/robert_next`

## scav_lock

Permission: `common_models.manage_scav`

This command locks a team out of scav. It's usage is `/scav_lock <@ team> [minutes, default is 15]`

## scav_unlock

Permission: `common_models.manage_scav`

This command unlocks a team's scav. It's usage is `/scav_unlock <@ team>`

## send_pronoun_message

Permission: `admin`

This command creates a message in the current channel that can be reacted to in order to be assigned pronouns. It's usage is `/send_pronoun_message`

## set_coin

Permission: `common_models.change_team_coin`

This command allows Spirit to set a team's skash count. It's usage is `/set_coin <team name> <amount>`

## shutdown

Permission: `superadmin`

This command allows a superadmin to shut the bot off. It's usage is `/shutdown`

## Euchre Stuff

The Euchre stuff should not be enabled on the server for the week but may be enabled on the planning server. It's commands are:

### euchre_start 

Permission: `None`

This command starts a game of Euchre. It's usage is `/euchre_start <@ player1> <@ player2> <@ player3> < @player4>`

### euchre_accept

Permission: `None`

This command accepts a card as trump. It's usage is `/euchre_accept [card only if you are the dealer]`

### euchre_reject

Permission: `None`

This command rejects a card as trump and moves on to the next player's turn. It's usage is `/euchre_reject`

### euchre_hand

Permission: `None`

This command shows your current hand. It's usage is `/euchre_hand`

### euchre_status

Permission: `None`

This command shows the current status of the game and how many points and tricks have been won. It's usage is `/euchre_status`

### euchre_play

Permission: `None`

This command plays a card during a Euchre trick. It's usage is `/euchre_play <card>`

### euchre_end

Permission: `None`

This command ends a game of Euchre. It's usage is `/euchre_end`
