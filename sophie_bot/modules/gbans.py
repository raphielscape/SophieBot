from time import gmtime, strftime

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

from sophie_bot import SUDO, decorator, logger, mongodb, bot
from sophie_bot.modules.connections import connection
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import (get_user, get_user_and_text,
                                      user_admin_dec, user_link)


@decorator.command("antispam", arg=True)
@user_admin_dec
@connection(admin=True, only_in_groups=True)
async def switch_antispam(event, status, chat_id, chat_title):
    args = event.pattern_match.group(1)
    enable = ['yes', 'on', 'enable']
    disable = ['no', 'disable']
    bool = args.lower()
    old = mongodb.antispam_setting.find_one({'chat_id': chat_id})
    if bool:
        if bool in disable:
            new = {'chat_id': chat_id, 'disabled': True}
            if old:
                mongodb.antispam_setting.update_one(
                    {'_id': old['_id']}, {"$set": new}, upsert=False)
            else:
                mongodb.antispam_setting.insert_one(new)
            await event.reply("Antispam disabled for {chat_name}".format(chat_title))
        elif bool in enable:
            mongodb.clean_service.delete_one({'_id': old['_id']})
            await event.reply("Antispam enabled for {chat_name}".format(chat_title))
        else:
            await event.reply("Heck, i don't undestand what you wanna from me.")
            return
    else:
        if old and old['disabled'] is True:
            txt = 'disabled'
        else:
            txt = 'enabled'
        await event.reply("Antispam for **{}** is **{}**".format(chat_title, txt))
        return


@decorator.command("gban", arg=True, from_users=SUDO)
async def gban_1(event):
    await blacklist_user(event)


@decorator.command("fban", arg=True, from_users=172811422)
async def gban_2(event):
    await blacklist_user(event)


async def blacklist_user(event):
    print('owo')
    user_a, reason = await get_user_and_text(event)
    user = await bot.get_entity(user_a['user_id'])
    if not reason:
        await event.reply("You can't blacklist user without a reason blyat!")
        return
    try:
        banned_rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
        )

        await event.client(
            EditBannedRequest(
                event.chat_id,
                user,
                banned_rights
            )
        )

    except Exception as err:
        await event.reply(str(err))
        logger.error(err)
        return
    old = mongodb.blacklisted_users.find_one({'user': user_a['user_id']})
    if old:
        new = {
            'user': user_a['user_id'],
            'date': old['date'],
            'by': old['by'],
            'reason': reason
        }
        mongodb.blacklisted_users.update_one({'_id': old['_id']}, {"$set": new}, upsert=False)
        await event.reply("This user already blacklisted! I'll update the reason.")
        return
    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    new = {
        'user': user_a['user_id'],
        'date': date,
        'reason': reason,
        'by': event.from_id
    }
    user_id = user_a['user_id']
    logger.info(f'user {user_id} gbanned by {event.from_id}')
    mongodb.blacklisted_users.insert_one(new)
    await event.reply("Sudo {} blacklisted {}.\nDate: `{}`\nReason: `{}`".format(
        await user_link(event.from_id), await user_link(user_a['user_id']), date, reason))


@decorator.command("ungban", arg=True, from_users=SUDO)
async def un_blacklist_user(event):
    chat_id = event.chat_id
    user = await get_user(event)
    try:
        unbanned_rights = ChatBannedRights(
            until_date=None,
            view_messages=False,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False,
        )

        precheck = mongodb.gbanned_groups.find({'user': user})
        if precheck:
            chats = mongodb.gbanned_groups.find({'user': user})
        else:
            chats = chat_id
        for chat in chats:
            await event.client(
                EditBannedRequest(
                    chat['chat'],
                    user,
                    unbanned_rights
                )
            )

    except Exception as err:
        await event.reply(err)
        logger.error(err)
    old = mongodb.blacklisted_users.find_one({'user': user['user_id']})
    if not old:
        await event.reply("This user isn't blacklisted!")
        return
    user_id = user['user_id']
    logger.info(f'user {user_id} ungbanned by {event.from_id}')
    mongodb.blacklisted_users.delete_one({'_id': old['_id']})
    await event.reply("Sudo {} unblacklisted {}.".format(
        await user_link(event.from_id), await user_link(user_id)))


@decorator.insurgent()
async def gban_trigger(event):
    user_id = event.from_id

    K = mongodb.blacklisted_users.find_one({'user': user_id})
    if K:
        banned_rights = ChatBannedRights(
            until_date=None,
            view_messages=True,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
        )

        try:
            ban = await event.client(
                EditBannedRequest(
                    event.chat_id,
                    user_id,
                    banned_rights
                )
            )

            if ban:
                mongodb.gbanned_groups.insert_one({'user': user_id, 'chat': event.chat_id})
                await event.reply(get_string("gbans", "user_is_blacklisted", event.chat_id).format(
                                  await user_link(user_id), K['reason']))

        except Exception as err:
            logger.info(f'Error on gbanning {user_id} in {event.chat_id} \n {err}')
            pass


@decorator.ChatAction()
async def gban_helper_2(event):
    if event.user_joined is True or event.user_added is True:
        if hasattr(event.action_message.action, 'users'):
            from_id = event.action_message.action.users[0]
        else:
            from_id = event.action_message.from_id

        K = mongodb.blacklisted_users.find_one({'user': from_id})
        if K:
            banned_rights = ChatBannedRights(
                until_date=None,
                view_messages=True,
                send_messages=True,
                send_media=True,
                send_stickers=True,
                send_gifs=True,
                send_games=True,
                send_inline=True,
                embed_links=True,
            )

            try:
                ban = await event.client(
                    EditBannedRequest(
                        event.chat_id,
                        from_id,
                        banned_rights
                    )
                )

                if ban:
                    mongodb.gbanned_groups.insert_one({'user': from_id, 'chat': event.chat_id})
                    await event.reply(get_string("gbans", "user_is_blacklisted", event.chat_id).format(
                                      await user_link(from_id), K['reason']))

            except Exception as err:
                logger.info(f'Error on gbanning {from_id} in {event.chat_id} \n {err}')
                pass
