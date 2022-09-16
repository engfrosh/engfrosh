SELECT common_models_discorduser.discord_username || '#' || common_models_discorduser.discriminator
FROM common_models_discorduser
    INNER JOIN auth_user ON common_models_discorduser.user_id = auth_user.id
WHERE auth_user.id IN (
        SELECT auth_user_groups.user_id
        FROM auth_user_groups
            INNER JOIN auth_group ON auth_user_groups.group_id = auth_group.id
            AND auth_group.name = 'Disco Unit'
    );