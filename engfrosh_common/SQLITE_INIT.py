# TODO Sync these tables up better with what Django does and proper database technique, etc

SQLITE_INIT = [
    """ CREATE TABLE IF NOT EXISTS auth_group (
            id integer PRIMARY KEY,
            name text NOT NULL UNIQUE
            );""",
    """ CREATE TABLE IF NOT EXISTS auth_user_groups (
            id integer PRIMARY KEY,
            user_id integer NOT NULL,
            group_id integer NOT NULL
            );""",
    """ CREATE TABLE IF NOT EXISTS authentication_discorduser (
            id integer PRIMARY KEY,
            discord_username text,
            discriminator integer,
            user_id NOT NULL
            );""",
    """ CREATE TABLE IF NOT EXISTS discord_bot_manager_scavchannel (
            channel_id integer PRIMARY KEY,
            group_id integer NOT NULL
            );""",
    """ CREATE TABLE IF NOT EXISTS frosh_team (
        display_name text,
        group_id integer PRIMARY KEY,
        coin_amount integer NOT NULL DEFAULT 0
        );"""
]
