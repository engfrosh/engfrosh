# Usage Instructions

FroshBot needs to be the highest role.

## Running on Linux Server
### Start in background with: 
```
nohup python3 [path].py &
```

### Stop Bot
Run the following and find the process:
```
ps aux
```
```
ubuntu    113860  0.0  3.3 186776 32580 ?        Sl   03:29   0:00 python3 bot.py
```
Then run the `kill` command with the process id:
```
kill [PID]
kill 113860
```

## List of Commands and SubCommands

### SCAV Commands 

#### Guess
Either of the following can be used to guess
```
\guess [10 Letter Code]
! [10 Letter Code]
```

#### Get Question
The bot will automatically ask a question when you get one correct. 
To get the first question or to get the question again use `?` or `\question`. 

#### Get Hint
A team can request a hint with the `\hint` command sent in their channel. 
This will then lock them out for the default time specified in the `settings.json` file. 

#### Lockout Team
An admin or scav_manager can lock a team out of scav using the `\lockout` command. 
If there is no time specified it will lock them out for the default time specified in `settings.json`. 
```
\lockout
```
```
\lockout [minutes]
```

#### Unlock Team
Sending a `\unlock` command to a team's channel will unlock them for scav. 

#### Create Team
Currently only the admin role supports creating teams. 
```
\create_team
```

With specified team name:
```
\create_team [Team Name]
```

### Other Commands
#### Enable / Disable
```
\enable [setting]
```

```
\disable [setting]
```

Enables or disables a setting

###### Possible Settings
- `scav`


#### Help
`\help` will send the help text defined in `settings.json` for a scav channel.
If the channel is not a scav channel it will encourage them to message the admin. 

#### Admin Only Commands
##### Regenerate Leaderboard
The leaderboard automatically updates, but to force an update an admin can send `\leaderboard`. 

##### Create Scav Team
Admins can create new teams with `\create_team`, either with a single word team name or none, and it will use a numbered team name. 

```
\create_team
\create_team [team_name]
```

# Instruction Channels
This is the content you can send to discord channels as the instructions:

## Player Instructions

Welcome to SCAV!
If someone already gave you a registration code, just send it here. 
If you want to form a new team, send `\newteam` and the bot will create a team for you and DM you 5 invites codes for you and 4 others. 
If at any time you run into issues with discord or the bot please @Grant . 
Once you register you will get access to your scav channel.
To get a question send `?` in the channel by itself. To guess an answer send:
`! MYGUESS`

To get a hint send `\hint` however be aware you will automatically be locked out of scav for 15 minutes.

## Manager Instructions

SCAV Manager Instructions: 
To lock a team out use the following command in the team's channel, with or without the number of minutes specified, if it is not specified it will default to 15 minutes. 
```
\lockout
\lockout 10
```
To unlock a team send `\unlock` in their channel.
To enable or disable scav use the following commands:
```
\enable scav
\disable scav
```
