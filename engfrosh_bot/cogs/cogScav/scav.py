# region Imports
import logging
from typing import Optional, Union
import discord
# import discord
# import datetime as dt

from discord.ext import commands
from discord.errors import NotFound

from ...EngFroshBot import EngFroshBot
# endregion


logger = logging.getLogger("Cogs.Scav")


# def load_all_settings():
#     global settings
#     with open(SETTINGS_FILE, "r") as f:
#         settings = json.load(f)
#     global quick_settings
#     quick_settings["admin_ids"] = set(settings["admin_users"])
#     quick_settings["scav_manager_ids"] = set(settings["scav_manager_users"])

#     if "bot_status_channel" in settings["channels"]:
#         settings["bot_status_channel_active"] = True
#         settings["bot_status_channel_id"] = settings["channels"]["bot_status_channel"]
#     return settings


# def load_scav_questions():
#     with open(SCAV_QUESTIONS_FILE, "r") as f:
#         return json.load(f)


# def load_user_registrations():
#     with open(USER_REGISTRATION_FILE, "r") as f:
#         global user_registrations
#         user_registrations = json.load(f)


# def save_user_registrations(indent=4):
#     with open(USER_REGISTRATION_FILE, "w") as f:
#         json.dump(user_registrations, f, indent=indent)


# async def reload_files():
#     # global settings
#     # settings = load_all_settings()
#     load_all_settings()
#     global scav_questions
#     scav_questions = load_scav_questions()
#     load_user_registrations()
#     await load_scav_teams()

# def graceful_shutdown():
#     client.logout()
#     exit()


# def save_settings(fp=None, indent=4):
#     if fp == None:
#         fp = SETTINGS_FILE
#     with open(fp, "w") as f:
#         json.dump(settings, f, indent=4)
#     logger.debug("Settings saved to %s", fp)


# def is_admin(user_id):
#     return user_id in quick_settings["admin_ids"]


# def is_scav_manager(user_id):
#     return user_id in quick_settings["scav_manager_ids"]


# async def load_scav_teams():
#     global scav_game
#     scav_game = ScavGame(SCAV_TEAM_FILENAME)
#     await scav_game.init_channels()
#     return

# endregion

# region commands


class Scav(commands.Cog):
    def __init__(self, bot: EngFroshBot):
        self.bot = bot
        self.db = bot.db_int
        self.config = bot.config["module_settings"]["scav"]

    # async def reload_settings(self):

    async def scav_enabled(self):
        res = await self.db.check_scavenger_setting_enabled(name=self.config["settings_names"]["active"])
        return bool(res)

    class ScavNotEnabledError(Exception):
        """Exception raised when scav is not enabled."""

    class TeamNotFoundError(Exception):
        """Exception raised when a team for the given information is not found."""

    class TeamAlreadyFinishedError(Exception):
        """Exception raised when a team is already finished scav."""

    # @commands.Cog.listener()
    # async def on_ready(self):
        # logger.info("Successfully Logged In")
        # if settings["bot_channel_active"]:
        # for
        # print("Connected")
        # global guild
        # guild = await self.bot.fetch_guild(settings["guild_id"])
        # guild_channels = await guild.fetch_channels()
        # print(guild_channels)
        # with open(CURRENT_DIRECTORY + "/guild.tmp","w") as f:
        #     for c in guild_channels:
        #         f.write(c.name + "\n")
        # print(guild.text_channels)
        # channels["bot_status_channel"] = await self.bot.fetch_channel(settings["channels"]["bot_status_channel"])
        # channels["leaderboard_channel"] = await self.bot.fetch_channel(settings["channels"]["leaderboard_channel"])
        # await channels["bot_status_channel"].send("Hello, I am now working! It is currently {datetime}".format(
        #   datetime=dt.datetime.now().isoformat()))
        # await load_scav_teams()
        # await reload_files()
        # scav_game.save_team_info(CURRENT_DIRECTORY + "/test_teams_out.json.tmp")
        # if "profile_picture" in settings and not settings["profile_picture_set"]:
        #     with open(settings["profile_picture"], "rb") as f:
        #         await self.bot.user.edit(avatar=f.read())
        #     settings["profile_picture_set"] = True
        #     save_settings()

    async def update_scoreboard(self):
        """Update the scoreboard channel with the current standings."""

        logger.debug("Updating Scav board...")
        teams = await self.bot.db_int.get_all_scav_teams()
        teams.sort(key=lambda team: team.current_question, reverse=True)

        msg = "```\n"

        cur_place = 0
        cur_question = None
        next_place = 1

        for team in teams:
            if team.current_question == cur_question:
                place = cur_place
                next_place += 1
            else:
                place = next_place
                cur_place = next_place
                next_place += 1
                cur_question = team.current_question

            msg += f"{place}. {await self.bot.db_int.get_team_display_name(team.group)}: {team.current_question}\n"

        msg += "```"

        channels = self.config["scoreboard_channels"]

        await self.bot.send_to_all(msg, channels, purge_first=True)

    async def scav_user_allowed(self, ctx: commands.Context) -> bool:
        """
        Check if the user and channel are correct and allowed to guess / request a hint,
        and send messages stating errors if not.

        """

        # Check that the channel is a scav channel
        group_id = await self.db.get_group_id(scav_channel_id=ctx.channel.id)
        if not group_id:
            await ctx.message.reply("There is no scav team associated with this channel.")
            return False

        # Check that scav is enabled
        enabled = await self.scav_enabled()
        if not enabled:
            await ctx.message.reply("Scav is not currently enabled.")
            return False

        # Check that the user is on the team and they can guess
        on_team_task = self.db.check_user_in_group(discord_user_id=ctx.message.author.id, group_id=group_id)
        can_guess = await self.db.check_user_has_permission(discord_id=ctx.message.author.id,
                                                            permission_name="guess_scav_question")
        on_team = await on_team_task
        if not on_team or not can_guess:
            await ctx.message.reply("You are not authorized to guess here.")
            return False

        # Get team and check if they are locked out
        team = await self.db.get_scav_team(team_id=group_id)
        assert team is not None
        if team.locked_out:
            await ctx.reply(f"Your team is currently locked out for: {team.lockout_remaining}")
            return False

        if team.finished:
            await ctx.reply("You're already finished Scav!")
            return False

        return True

    @commands.command()
    async def guess(self, ctx: commands.Context, guess: str):
        """Make a guess of the answer to the current scav question."""

        if self.bot.debug:
            await ctx.message.add_reaction("🔄")

        allowed = await self.scav_user_allowed(ctx)
        if not allowed:
            return

        # Get the team id from the channel
        team_id = await self.db.get_group_id(scav_channel_id=ctx.channel.id)
        if not team_id:
            await self.bot.log("Could not get scav channel.")
            return

        # TODO add handling question response times

        # TODO add check if the question is actually enabled

        question = await self.db.get_scav_question(team_id=team_id)
        if not question:
            await self.bot.log(f"Could not get a current question for team id: {team_id}", "ERROR")
            return

        if guess.lower() != question.answer.lower():
            try:
                if self.config["incorrect_message"]:
                    await ctx.message.reply(self.config["incorrect_message"])
                else:
                    await ctx.message.add_reaction("👀")
            except NotFound:
                pass
            return

        if self.bot.debug:
            try:
                await ctx.message.add_reaction("✅")
            except NotFound:
                await self.bot.warning(f"Correct guess given, but message deleted first:\n{ctx.message}")

        await ctx.message.reply("That is correct!")

        try:
            res = await self.db.increment_question(team_id, question)
            if not res:
                await self.bot.log("Failed")
                raise Exception(f"Could not increment Team {team_id}'s scav question.")

            await self.handle_scav_question(group_id=team_id)

        except self.db.FinishedScavException:
            channels = await self.db.get_scav_channels(group_id=team_id)
            await self.bot.send_to_all("Congratulations! You have completed Scav!", channels)

        await self.update_scoreboard()

    @commands.command()
    async def question(self, ctx: commands.Context):
        """Get questions for current scavenger channel."""
        # TODO check if it is a scav channel
        if self.bot.debug:
            await ctx.message.add_reaction("🔄")

        try:
            res = await self.handle_scav_question(channel_id=ctx.message.channel.id)
            if not res:
                await self.bot.log(f"Failed to send question to <#{ctx.message.channel.id}>")
        except self.TeamNotFoundError:
            await self.bot.log(f"Could not find a scav team for channel: {ctx.channel.id}", "ERROR")
            return

        except self.TeamAlreadyFinishedError:
            await ctx.message.reply("Your team is already finished scav.")
            return

    @commands.command()
    async def scav_lock(self, ctx: commands.Context, minutes: Optional[Union[str, int]] = None):
        """Lock the current channel."""

        allowed = await self.db.check_user_has_permission(discord_id=ctx.author.id, permission_name="manage_scav")
        if not allowed:
            await ctx.reply("You are not allowed to manage scav.")
            return

        team_id = await self.db.get_group_id(scav_channel_id=ctx.channel.id)
        if not team_id:
            ctx.message.reply("Not a valid scav channel.")
            return

        await ctx.message.delete()

        DEFAULT_MINUTES = 15

        if minutes:
            minutes = int(minutes)
        else:
            minutes = DEFAULT_MINUTES

        await self.db.set_team_locked_out_time(team_id, minutes=minutes)

        channels = await self.db.get_scav_channels(group_id=team_id)

        await self.bot.send_to_all(f"Scav locked for {minutes} minutes.", channels)

    @commands.command()
    async def scav_unlock(self, ctx: commands.Context):
        """Unlock the current channel."""

        allowed = await self.db.check_user_has_permission(discord_id=ctx.author.id, permission_name="manage_scav")
        if not allowed:
            await ctx.reply("You are not allowed to manage scav.")
            return

        team_id = await self.db.get_group_id(scav_channel_id=ctx.channel.id)
        if not team_id:
            ctx.message.reply("Not a valid scav channel.")
            return

        await ctx.message.delete()

        await self.db.set_scav_team_unlocked(team_id)

        channels = await self.db.get_scav_channels(group_id=team_id)

        await self.bot.send_to_all("Scav unlocked.", channels)

    @commands.command()
    async def hint(self, ctx: commands.Context):
        """Request hint for the question."""

        if self.bot.debug:
            await ctx.message.add_reaction("🔄")

        allowed = await self.scav_user_allowed(ctx)
        if not allowed:
            return

        # Get the team id from the channel
        team_id = await self.db.get_group_id(scav_channel_id=ctx.channel.id)
        if not team_id:
            await self.bot.log("Could not get scav channel.")
            return

        # TODO add handling hint response times

        # TODO add check if the hint is actually enabled

        hint = await self.db.get_next_hint(team_id=team_id)
        if not hint:
            ctx.message.reply("No new hint available.")
            return

        if hint.file:
            file = discord.File(self.bot.config["media_root"] + "/" + hint.file, hint.display_filename)
        else:
            file = None

        await self.bot.send_to_all(f"Hint: {hint.text}", [ctx.channel.id], file=file)

    async def handle_scav_question(self,
                                   send_question: bool = True,
                                   current_hints: bool = True,
                                   new_hint: bool = False,
                                   *,
                                   group_id: Optional[int] = None,
                                   channel_id: Optional[int] = None,
                                   new_hint_lockout: Optional[int] = None) -> bool:
        """
        Handle a scav question request.

        new_hint_lockout: lockout time in seconds overides default.

        """

        # region Get Team and Check Enabled

        if not group_id and not channel_id:
            raise ValueError("Must provide an argument")

        if group_id and channel_id:
            raise ValueError("May only provide channel or team id.")

        enabled = await self.scav_enabled()
        if not enabled:
            raise self.ScavNotEnabledError

        if channel_id:
            team_id = await self.db.get_group_id(scav_channel_id=channel_id)
            if not team_id:
                raise self.TeamNotFoundError
            channels = [channel_id]

        elif group_id:
            team_id = group_id
            channels = await self.db.get_scav_channels(group_id=group_id)

        else:
            raise Exception

        team = await self.db.get_scav_team(team_id=team_id)
        assert team is not None
        if team.finished:
            raise self.TeamAlreadyFinishedError()

        # endregion

        # region Get Question

        question = await self.db.get_scav_question(team_id=team_id)
        if not question:
            await self.bot.log(f"Could not get a current question for team id: {team_id}", "ERROR")
            return False

        q_res = True
        if send_question:
            logger.debug(f"File for questions is: {question.file}")

            if question.file:
                file = discord.File(self.bot.config["media_root"] + "/" + question.file, question.display_filename)
            else:
                file = None

            q_res = await self.bot.send_to_all(question.text, channels, file=file)

        hints = []
        if current_hints:
            hints = await self.db.get_team_scav_hints(team_id=team_id)
            if not hints:
                logger.info(f"No active hints for team {team_id}")
                return q_res

        if new_hint:
            # TODO Implement New Hints
            raise NotImplementedError

        h_res = True
        if hints:
            for hint in hints:
                if hint.file:
                    file = discord.File(self.bot.config["media_root"] + "/" + hint.file, hint.display_filename)
                else:
                    file = None

                res = await self.bot.send_to_all(hint.text, channels, file=file)
                h_res = h_res and res

        return h_res and q_res

        # if settings["scav"]["allowed"]:
        #     active_scav_team = scav_game.is_scav_channel(ctx.message.channel.id)
        #     if active_scav_team is not False:
        #         if active_scav_team.is_team_member(ctx.message.author.id):
        #             if settings["scav"]["enabled"]:
        #                 lockout_time = active_scav_team.is_team_locked_out()
        #                 if lockout_time == 0:
        #                     # await message.channel.send("Checking Your Guess!")
        #                     if len(message_array) < 2:
        #                         await ctx.message.channel.send(
        #                               "You need to guess something!\nUse the format: ```! YOURGUESS```")
        #                         return
        #                     else:
        #                         await active_scav_team.check_answer(message_array[1])
        #                 else:
        #                     await ctx.message.channel.send("You are locked out for {}:{}".format(
        #                               (lockout_time / 60), lockout_time % 60))
        #                 return
        #             else:
        #                 await ctx.message.channel.send("SCAV is currently disabled")
        #                 return
        #         else:
        #             await ctx.message.channel.send("You are not allowed to guess in this channel!")
        #             return
        #     else:
        #         await ctx.message.channel.send("This is not a SCAV channel!")
        #         return
        # if settings["scav"]["enabled"]:
        #     await message.channel.send("Checking your guess...")

        # else:
        #     await message.channel.send("SCAV is not currently enabled")
        # return

    # @commands.command()
    # async def newTeam(self, ctx):
    #     message_array = ctx.message.content.lower().strip().split()

    #     if settings["scav"]["allowed"] and settings["scav"]["self_registration_allowed"]:
    #         if len(message_array) > 1:
    #             team_name = " ".join(message_array[1:])
    #         else:
    #             team_name = "Team {}".format(len(scav_game.teams))
    #         logger.debug("Creating team %s", team_name)
    #         reg_codes = await scav_game.new_scav_team(team_name=team_name)
    #         code_msg = "Here are your scav team registration codes for team {team_name}\n".format(team_name=team_name)
    #         code_msg += "```\n"
    #         for code in reg_codes:
    #             code_msg += code + "\n"
    #         code_msg += "```"
    #         code_msg += "Send one of these codes in a channel in the discord server.
    #                   Send these to your teammates and have them do the same."
    #         await ctx.message.author.send(code_msg)
    #         await ctx.message.delete()
    #         return

    # @commands.command()
    # async def enableScav(self, ctx):
    #     if is_admin(ctx.message.author.id):
    #         settings["scav"]["enabled"] = True
    #         save_settings()
    #         await ctx.send("Scav is now enabled.")
    #         return
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def disableScav(self, ctx):
    #     if is_admin(ctx.message.author.id):
    #         settings["scav"]["enabled"] = False
    #         save_settings()
    #         await ctx.send("Scav is now disabled.")
    #         return
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def lockoutTeam(self, ctx):
    #     message_array = ctx.message.content.lower().strip().split()

    #     if settings["scav"]["allowed"] and (is_admin(ctx.author.id) or is_scav_manager(ctx.author.id)):
    #         active_scav_team = scav_game.is_scav_channel(ctx.channel.id)
    #         if active_scav_team is True:
    #             await active_scav_team.unlock()
    #             if len(message_array) == 2:
    #                 minutes = int(message_array[1])
    #              # if len(message_array) == 1:
    #             else:
    #                 minutes = settings["scav"]["default_lockout_time"]
    #             await active_scav_team.lockout(minutes)
    #             # else:
    #             #     await message.channel.send("Error, not implemented custom lockout")
    #             scav_game.save_team_info()
    #         else:
    #             await ctx.channel.send("Not a SCAV channel")
    #         await ctx.message.delete()
    #         return
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def unlockTeam(self, ctx):
    #     if settings["scav"]["allowed"] and (is_admin(ctx.author.id) or is_scav_manager(ctx.author.id)):
    #         active_scav_team = scav_game.is_scav_channel(ctx.channel.id)
    #         if active_scav_team is True:
    #             await active_scav_team.unlock()
    #             scav_game.save_team_info()
    #         else:
    #             await ctx.channel.send("Not a SCAV channel")
    #         await ctx.message.delete()
    #         return
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def clue(self, ctx):
    #     if settings["scav"]["allowed"]:
    #         active_scav_team = scav_game.is_scav_channel(ctx.channel.id)
    #         if active_scav_team is not False:
    #             if settings["scav"]["enabled"]:
    #                 await active_scav_team.ask_question()
    #             else:
    #                 await ctx.send("SCAV is not enabled")
    #         else:
    #             await ctx.send("This is not a SCAV channel!")
    #         return

    # @commands.command()
    # async def hint(self, ctx):
    #     if settings["scav"]["allowed"]:
    #         active_scav_team = scav_game.is_scav_channel(ctx.channel.id)
    #         if active_scav_team is not False:
    #             if active_scav_team.is_team_member(ctx.author.id):
    #                 if settings["scav"]["enabled"]:
    #                     await active_scav_team.send_hint()
    #                 else:
    #                     await ctx.send("SCAV is not enabled")
    #             else:
    #                 await ctx.send("You are not allowed to ask for hints in this channel!")
    #                 return
    #         else:
    #             await ctx.send("This is not a SCAV channel!")
    #         return

    # @commands.command()
    # async def reload(self, ctx):
    #     if is_admin(ctx.author.id):
    #         await reload_files()
    #         await channels["bot_status_channel"].send("Files Reloaded")
    #         await ctx.delete()
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def resetTeam(self, ctx):
    #     message_array = ctx.message.content.lower().strip().split()
    #     if is_admin(ctx.author.id):
    #         team_id = int(message_array[1])
    #         if team_id in scav_game.teams:
    #             await scav_game.teams[team_id].reset_team()
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def createTeam(self, ctx):
    #     if is_admin(ctx.author.id):
    #         message_array = ctx.message.content.lower().strip().split()
    #         if len(message_array) > 1:
    #             team_name = message_array[1]
    #         else:
    #             team_name = None
    #         await scav_game.new_scav_team(team_name)
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def removeScavManager(self, ctx):
    #     if is_admin(ctx.author.id):
    #         message_array = ctx.message.content.lower().strip().split()
    #         user_id = int(message_array[1])
    #         if user_id in settings["scav_manager_users"]:
    #             settings["scav_manager_users"].remove(user_id)
    #             save_settings()
    #         if user_id in quick_settings["scav_manager_ids"]:
    #             quick_settings["scav_manager_ids"].remove(user_id)
    #         await ctx.delete()
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def welcome(self, ctx):
    #     if is_admin(ctx.author.id):
    #         await scav_game.send_introductions()
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def leaderboard(self, ctx):
    #     if is_admin(ctx.author.id):
    #         await scav_game.leaderboard()
    #     else:
    #         logger.debug("Illegal Command by %s: %s".format(ctx.author, ctx.message.content))

    # @commands.command()
    # async def scavHelp(self, ctx):
    #     if scav_game.is_scav_channel(ctx.channel.id):
    #         await ctx.send(settings["help_text"])
    #         return
    #     else:
    #         await ctx.send("Please `@Grant` for help")

    # @commands.Cog.listener()
    # async def on_message(ctx):
    #     if ctx.author == commands.user:
    #         return
    #     if ctx.guild.id != settings["guild_id"]:
    #         return
    #     message_array = ctx.message.content.lower().strip().split()
    #     # NEED GRANT TO TALK ME THROUGH THIS PART
    #     if message_array[0][0] == "$":
    #         await ctx.message.delete()
    #         if message_array[0] in user_registrations:
    #             if user_registrations[message_array[0]]["user_id"] == 0:
    #                 if user_registrations[message_array[0]]["account_type"] == "admin":
    #                     if ctx.author.id not in settings["admin_users"]:
    #                         user_registrations[message_array[0]
    #                                            ]["user_id"] = ctx.author.id
    #                         save_user_registrations()
    #                         settings["admin_users"].append(ctx.author.id)
    #                         save_settings()
    #                         quick_settings["admin_ids"].add(ctx.author.id)
    #                         role = guild.get_role(settings["admin_role"])
    #                         await ctx.author.add_roles(role)
    #                         await ctx.channel.send("Welcome Admin!")
    #                     else:
    #                         await ctx.channel.send("Already an Admin")
    #                 elif user_registrations[message_array[0]]["account_type"] == "scav_manager":
    #                     if ctx.author.id not in settings["scav_manager_users"] and
    #                                   ctx.author.id not in settings["admin_users"]:
    #                         user_registrations[message_array[0]
    #                                            ]["user_id"] = ctx.author.id
    #                         save_user_registrations()
    #                         settings["scav_manager_users"].append(
    #                             ctx.author.id)
    #                         save_settings()
    #                         quick_settings["scav_manager_ids"].add(
    #                             ctx.author.id)
    #                         role = guild.get_role(settings["scav_manager_role"])
    #                         await ctx.author.add_roles(role)
    #                         await ctx.channel.send("Welcome Scav Manager!")
    #                     else:
    #                         await ctx.channel.send("Already a Scav Manager or Higher")
    #                 elif user_registrations[message_array[0]]["account_type"] == "scav_player":
    #                     if ctx.author.id not in settings["scav_manager_users"] and ctx.author.id
    #                                    not in settings["admin_users"]:
    #                         user_registrations[message_array[0]
    #                                            ]["user_id"] = ctx.author.id
    #                         save_user_registrations()
    #                         await scav_game.teams[user_registrations[message_array[0]]["scav_team"]].add_player(
    #                             ctx.author)
    #                         # settings["scav_manager_users"].append(ctx.author.id)
    #                         # save_settings()
    #                         # quick_settings["scav_manager_ids"].add(ctx.author.id)
    #                         await ctx.channel.send("Welcome Scav Player!")
    #                     else:
    #                         await ctx.channel.send("Already a Scav Manager or Higher")
    #             else:
    #                 await ctx.channel.send("Activation code already used")
    #         else:
    #             await ctx.channel.send("Invalid activation code")
    #         return


def setup(bot):
    bot.add_cog(Scav(bot))
# endregion

# region SCAV Classes


# class ScavTeam():
#     def __init__(self, team_info: dict, channel_id: int):
#         self.team_info = dict(team_info)
#         self.channel_id = channel_id
#         # if "team_name" not in team_info:
#         #     self.team_info["team_name"] = ""
#         # if self.team_info["current_question"] == 0:
#         #     self.team_info["question_completion_time"] = {}
#         #     scav_game.save_team_info()

#     async def init_channel(self):
#         self.channel = await client.fetch_channel(self.channel_id)

#     async def _send_message(self, content: str):
#         await self.channel.send(content)

#     def get_team_info(self):
#         return self.team_info

#     def is_team_member(self, author_id: int):
#         return author_id in self.team_info["members"]

#     def is_team_locked_out(self):
#         """Returns number of seconds if still locked out, otherwise returns 0"""
#         if not self.team_info["locked_out_until"]:
#             return False
#         locked_out_time = dt.datetime.fromisoformat(
#             self.team_info["locked_out_until"])
#         now = dt.datetime.now()
#         delta = locked_out_time - now
#         if delta > dt.timedelta(0):
#             return (delta.total_seconds())
#         else:
#             return 0

#     async def check_answer(self, guess):
#         # guess = guess.upper()
#         if self.team_info["finished"]:
#             await self.channel.send("You're already finished!")
#             return
#         if guess.lower() == scav_questions[self.team_info["current_question"]]["answer"].lower():
#             await self.correct_answer()
#             return True
#         else:
#             await self.wrong_answer()
#         return False

#     async def wrong_answer(self):
#         await self.channel.send("Sorry, that is incorrect.")

#     async def correct_answer(self):
#         await self.channel.send("That is correct!")
#         self.team_info["question_completion_time"][self.team_info["current_question"]
#                                                    ] = dt.datetime.now().isoformat()
#         self.team_info["current_question"] += 1
#         scav_game.save_team_info()
#         if self.team_info["current_question"] >= len(scav_questions):
#             await self.channel.send("CONGRATS!! You have completed SCAV")
#             self.team_info["finished"] = True
#             self.team_info["finish_time"] = dt.datetime.now().isoformat()
#             scav_game.save_team_info()
#         else:
#             await self.ask_question()
#         await scav_game.leaderboard()
#         return

#     async def lockout(self, minutes):
#         now = dt.datetime.now()
#         delta = dt.timedelta(minutes=minutes)
#         lockout_end_time = now + delta
#         self.team_info["locked_out_until"] = lockout_end_time.isoformat()
#         scav_game.save_team_info()
#         await self.channel.send("You are locked out for {} minutes".format(minutes))
#         return

#     async def unlock(self):
#         self.team_info["locked_out_until"] = ""
#         await self.channel.send("Your team is now unlocked")
#         return

#     async def ask_question(self):
#         if self.team_info["finished"]:
#             await self.channel.send("You're already finished!")
#             return
#         if "file" in scav_questions[self.team_info["current_question"]]:
#             if "file_display_name" in scav_questions[self.team_info["current_question"]]:
#                 filename = scav_questions[self.team_info["current_question"]
#                                           ]["file_display_name"]
#             else:
#                 filename = None
#             f = discord.File(
#                 scav_questions[self.team_info["current_question"]]["file"], filename=filename)
#         else:
#             f = None
#         await self.channel.send(scav_questions[self.team_info["current_question"]]["clue"], file=f)
#         if self.team_info["current_question"] == self.team_info["last_hint"]:
#             if "hint_file" in scav_questions[self.team_info["current_question"]]:
#                 if "hint_file_display" in scav_questions[self.team_info["current_question"]]:
#                     filename = scav_questions[self.team_info["current_question"]
#                                               ]["file_display_name"]
#                 else:
#                     filename = None
#                 f = discord.File(
#                     scav_questions[self.team_info["current_question"]]["hint_file"], filename=filename)
#             else:
#                 f = None
#             await self.channel.send(scav_questions[self.team_info["current_question"]]["hint"], file=f)

#     async def introduction(self):
#         await self.channel.send(settings["help_text"])

#     async def send_hint(self):
#         if self.team_info["finished"]:
#             await self.channel.send("You're already finished!")
#             return
#         if "hint_file" in scav_questions[self.team_info["current_question"]]:
#             if "hint_file_display" in scav_questions[self.team_info["current_question"]]:
#                 filename = scav_questions[self.team_info["current_question"]
#                                           ]["file_display_name"]
#             else:
#                 filename = None
#             f = discord.File(
#                 scav_questions[self.team_info["current_question"]]["hint_file"], filename=filename)
#         else:
#             f = None
#         if "hint" in scav_questions[self.team_info["current_question"]]:
#             if self.team_info["last_hint"] == self.team_info["current_question"]:
#                 await self.ask_question()
#                 return
#             else:
#                 self.team_info["last_hint"] = self.team_info["current_question"]
#                 scav_game.save_team_info()
#                 await self.lockout(settings["scav"]["default_lockout_time"])
#                 await self.channel.send(scav_questions[self.team_info["current_question"]]["hint"], file=f)
#         else:
#             await self.channel.send("Sorry, no hint available")
#         # logger.debug("Team %i asked question %i: %s".format())

#     async def reset_team(self):
#         self.team_info["finished"] = False
#         self.team_info["finish_time"] = ""
#         self.team_info["question_completion_time"] = {}
#         self.team_info["current_question"] = 0
#         self.team_info["locked_out_until"] = ""
#         self.team_info["last_hint"] = -1
#         scav_game.save_team_info()
#         await self.channel.send("Your team has been reset")

#     async def add_player(self, author):
#         self.team_info["members"].append(author.id)
#         scav_game.save_team_info()
#         # member = guild.get_member(author.id)
#         # member = await client.fetch_user(author.id)
#         role = guild.get_role(self.team_info["role"])
#         await author.add_roles(role)

#     def create_registration_code(self, name="", nickname=""):
#         code = "$" + "".join(random.choice(string.ascii_lowercase +
#                                            string.digits) for i in range(8))
#         global user_registrations
#         user_registrations[code] = {
#             "name": "",
#             "nickname": "",
#             "account_type": "scav_player",
#             "user_id": 0,
#             "scav_team": self.channel_id,
#             "team_name": self.team_info["team_name"]
#         }
#         save_user_registrations()
#         return code


# class ScavGame():
#     def __init__(self, all_team_info_fp: str):
#         logger.debug("Team info to load is a filepath, attempting to load...")
#         with open(all_team_info_fp, "r") as f:
#             all_team_info = json.load(f)
#         # if type(all_team_info) is not dict:
#         #     raise NotImplementedError(
#         #         "Passed all_team_info is not dict or filepath")
#         self.teams = {}
#         for key, value in all_team_info.items():
#             key = int(key)
#             self.teams[key] = ScavTeam(value, key)
#             logger.debug("Scav team with id %i loaded", key)
#         logger.info("All Scav teams loaded")
#         return

#     async def init_channels(self):
#         for team in self.teams.values():
#             await team.init_channel()

#     def save_team_info(self, filename: str = None, indent=4):
#         if filename is None:
#             filename = SCAV_TEAM_FILENAME
#         export_dict = {}
#         for key, value in self.teams.items():
#             export_dict[str(key)] = value.get_team_info()
#         with open(filename, "w") as f:
#             json.dump(export_dict, f, indent=indent)

#     def is_scav_channel(self, channel_id: int):
#         if channel_id in self.teams:
#             return self.teams[channel_id]
#         else:
#             return False

#     async def new_scav_team(self, team_name=None):
#         global guild
#         logger.debug("Create new team")
#         if team_name == None:
#             team_name = "Team {}".format(len(self.teams))
#         logger.debug("Team name: %s", team_name)
#         # role = await guild.create_role(name=team_name, colour=discord.Colour.gold)
#         new_role = await guild.create_role(name=team_name)
#         scav_manager_role = guild.get_role(settings["scav_manager_role"])
#         overwrites = {
#             guild.default_role: discord.PermissionOverwrite(read_messages=False),
#             new_role: discord.PermissionOverwrite(read_messages=True),
#             scav_manager_role: discord.PermissionOverwrite(read_messages=True)
#         }
#         # channel = await guild.create_text_channel(team_name, category=settings["scav"]["category"],
#                   overwrites=overwrites)
#         channel = await guild.create_text_channel(team_name, overwrites=overwrites)
#         team_details = BLANK_TEAM_CSV
#         team_details["role"] = new_role.id
#         team_details["team_name"] = team_name
#         self.teams[channel.id] = (ScavTeam(team_details, channel.id))
#         await self.teams[channel.id].init_channel()
#         self.save_team_info()
#         await channels["bot_status_channel"].send("{} Created".format(team_name))
#         reg_codes = []
#         for i in range(settings["scav"]["default_team_size"]):
#             reg_codes.append(self.teams[channel.id].create_registration_code())
#         await self.leaderboard()

#         guild = await client.fetch_guild(settings["guild_id"])
#         return reg_codes

#     async def leaderboard(self):
#         await channels["leaderboard_channel"].purge()
#         finished_teams = []
#         inprogress_teams = []
#         for key, team in self.teams.items():
#             if team.team_info["finished"]:
#                 finished_teams.append(team)
#             else:
#                 inprogress_teams.append(team)
#         finished_teams = sorted(
#             finished_teams, key=lambda team: team.team_info["finish_time"])
#         inprogress_teams = sorted(
#             inprogress_teams, key=lambda team: team.team_info["current_question"], reverse=True)
#         leaderboard_str = "Standings\n============\n"
#         position = 1
#         for team in finished_teams:
#             leaderboard_str += "{position}: {team}\n".format(
#                 position=position, team=team.team_info["team_name"])
#             position += 1
#         for team in inprogress_teams:
#             leaderboard_str += "\*{position}: {team}\n".format(
#                 position=position, team=team.team_info["team_name"],)
#             position += 1
#         await channels["leaderboard_channel"].send(leaderboard_str)

#     async def send_introductions(self):
#         for team in self.teams.values():
#             await team.introduction()

# # endregion
