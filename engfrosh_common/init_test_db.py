import asyncio

from DatabaseInterface import DatabaseInterface

DATABASE_PATH = ""


async def main():
    interface = DatabaseInterface(sqlite_filename=DATABASE_PATH)

    user_id = 16
    team_name = "Example Team"
    scav_channel_id = 222222222222222222
    user_discord_id = 111111111111111111

    group_id = await interface.add_group(team_name)
    if not group_id:
        group_id = await interface.get_group_id(group_name=team_name)
    await interface.add_scav_channel(scav_channel_id, group_id)
    await interface.add_discord_user(user_discord_id, user_id)
    await interface.add_user_to_group(user_id, group_id=group_id)
    await interface.add_team(group_id, "Best Team")

    # ** Example Usage **
    # **  Comment Out  **
    await example_checks(interface)
    # *******************


async def example_checks(interface: DatabaseInterface):

    # Change these to try out
    group_name = "Example Team"
    group_id = 1
    scav_channel_id = 222222222222222222
    discord_user_id = 111111111111111111
    user_id = 16
    coin_change = 37

    print("\nExample of Checks")
    print("====================================================")

    res = await interface.get_group_id(group_name=group_name)
    print(f"Group id for group name [{group_name}] is {res}")

    res = await interface.get_group_id(scav_channel_id=scav_channel_id)
    print(f"Group id for scav channel id [{scav_channel_id}] is {res}")

    res = await interface.get_user_id(discord_id=discord_user_id)
    print(f"User id for discord user id [{discord_user_id}] is {res}")

    res = await interface.check_user_in_group(user_id=user_id, group_id=group_id)
    print(f"User with id [{user_id}] is in group with id [{group_id}]?  {res}")

    res = await interface.check_user_in_group(group_name=group_name, discord_user_id=discord_user_id)
    print(f"User with discord id [{discord_user_id}] is in group {group_name}?  {res}")

    res = await interface.get_team_display_name(group_id)
    print(f"Team name for id [{group_id}] is {res}")

    res = await interface.get_coin_amount(group_id=group_id)
    print(f"Team with id [{group_id}] currently has {res} coins.")

    await interface.update_coin_amount(coin_change, group_id=group_id)
    res = await interface.get_coin_amount(group_id=group_id)
    print(f"Added {coin_change} to team with id [{group_id}] totalling {res}.")

    print("====================================================\n")

asyncio.get_event_loop().run_until_complete(main())
