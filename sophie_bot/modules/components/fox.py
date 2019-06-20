from ftplib import FTP
from time import gmtime, strftime
import ujson
import os

from telethon import custom

from sophie_bot import CONFIG, decorator, logger, bot
from sophie_bot.modules.helper_func.flood import flood_limit_dec

ftp_url = "ftp.orangefox.website"
fox_groups = [483808054, -1001287179850, -1001280218923, -1001155400138, -1001362128194]
fox_beta_groups = [483808054, -1001280218923, -1001362128194]
fox_dev_chats = [-1001155400138, 483808054]

BETA_CHANNEL = -1001429093106
STABLE_CHANNEL = 483808054

global DEVICES_STABLE
global DEVICES_BETA

DEVICES_STABLE = {}
DEVICES_BETA = {}

NEW_BETA_TEXT = """🦊 **OrangeFox R10 Beta**
`{ver}`

📱 {fullname} ({codename})
📅 Date: `{modified}`

👤 Maintainer: {maintainer}
{msg}
ℹ️ ChangeLog:
{changelog}
💬 **Beta testing group:** [join](https://t.me/joinchat/HNZTNha1iBzpX-_33EdEsg)"""

NEW_STABLE_TEXT = """🦊 **OrangeFox R10 Stable**
`{ver}`

📱 {fullname} ({codename})
📅 Date: `{modified}`

👤 Maintainer: {maintainer}
{msg}
ℹ️ ChangeLog:
{changelog}
💬 **OrangeFox chat:** [join](https://t.me/joinchat/HNZTNky4zkpWc7na_-Beow)"""


async def update_devices():
    logger.info("Update info about OrangeFox builds..")
    global DEVICES_STABLE
    global DEVICES_BETA

    f = open("update.json", "r")
    jfile = ujson.load(f)
    old_beta = jfile['beta']
    old_stable = jfile['stable']

    ftp = FTP(ftp_url, CONFIG['advanced']['ofox_ftp_user'], CONFIG['advanced']['ofox_ftp_pass'])

    data = ftp.mlsd("OrangeFox-Stable", ["type"])
    for device, facts in data:
        if not facts["type"] == "dir":
            continue

        info_file = []
        ftp.retrlines(f'RETR OrangeFox-Stable/{device}/device_info.txt', info_file.append)

        codename = info_file[0].split(': ')[1]
        fullname = info_file[1].split(': ')[1]
        maintainer = info_file[2].split(': ')[1]
        msg = ""
        print(len(info_file))
        if len(info_file) >= 4:
            msg = info_file[3].split(': ')[1]

        builds = list(ftp.mlsd("OrangeFox-Stable/" + device, ["type"]))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)
        readme = None
        done = 0
        for build, facts in builds:
            logger.debug(build)
            if not facts["type"] == "file":
                continue
            elif build == "README.md":
                readme = "README.md"
                continue

            ext = os.path.splitext(build)[1]
            if ext == '.zip' and done == 0:
                last_build = build
                modified = facts['modify']
                done = 1

        mm = list(ftp.mlsd(f"OrangeFox-Stable/{device}/{last_build[:-4]}.txt"))
        if mm:
            lchangelog = []
            ftp.retrlines(f'RETR OrangeFox-Stable/{device}/{last_build[:-4]}.txt',
                          lchangelog.append)
            changelog = ""
            for owo in lchangelog:
                if changelog:
                    changelog += '\n'
                changelog += "  " + str(owo)
            changelog_file = f"{last_build[:-4]}.txt"
        else:
            changelog = None
            changelog_file = None

        DEVICES_STABLE[device] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": last_build,
            "modified": modified,
            "readme": readme,
            "msg": msg,
            "changelog": changelog
        }

        # Check on update
        print(codename in old_stable)
        if codename not in old_stable or int(modified) > int(old_stable[device]['modified']):
            logger.info(f'Stable - new update of {codename} detected.')
            link = 'https://files.orangefox.website/OrangeFox-Stable/' + device + "/" + last_build

            await bot.send_message(
                STABLE_CHANNEL,
                NEW_STABLE_TEXT.format_map(DEVICES_STABLE[device]),
                buttons=[[custom.Button.url(
                    "⬇️ Download this build", link
                )]],
                link_preview=False
            )

    data = ftp.mlsd("OrangeFox-Beta", ["type"])
    for device, facts in data:
        if not facts["type"] == "dir":
            continue

        info_file = []
        ftp.retrlines(f'RETR OrangeFox-Beta/{device}/device_info.txt', info_file.append)

        codename = info_file[0].split(': ')[1]
        fullname = info_file[1].split(': ')[1]
        maintainer = info_file[2].split(': ')[1]
        msg = None
        print(device)
        print(len(info_file))
        if len(info_file) >= 4:
            msg = info_file[3].split(': ')[1]

        builds = list(ftp.mlsd("OrangeFox-Beta/" + device, ["type"]))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)
        readme = None
        done = 0
        for build, facts in builds:
            logger.debug(build)
            if not facts["type"] == "file":
                continue
            elif build == "README.md":
                readme = "README.md"
                continue

            ext = os.path.splitext(build)[1]
            if ext == '.zip' and done == 0:
                last_build = build
                modified = facts['modify']
                done = 1

        mm = list(ftp.mlsd(f"OrangeFox-Stable/{device}/{last_build[:-4]}.txt"))
        if mm:
            lchangelog = []
            ftp.retrlines(f'RETR OrangeFox-Stable/{device}/{last_build[:-4]}.txt',
                          lchangelog.append)
            changelog = ""
            for owo in lchangelog:
                if changelog:
                    changelog += '\n'
                changelog += "  " + str(owo)
            changelog_file = f"{last_build[:-4]}.txt"
        else:
            changelog = None
            changelog_file = None

        DEVICES_BETA[device] = {
            "codename": codename,
            "fullname": fullname,
            "maintainer": maintainer,
            "ver": last_build,
            "modified": modified,
            "readme": readme,
            "msg": msg,
            "changelog": changelog
        }

        # Check on update
        if codename not in old_beta or int(modified) > int(old_beta[device]['modified']):
            logger.info(f'BETA - new update of {codename} detected.')
            link = 'https://files.orangefox.website/OrangeFox-Beta/' + device + "/" + last_build

            await bot.send_message(
                BETA_CHANNEL,
                NEW_BETA_TEXT.format_map(DEVICES_BETA[device]),
                buttons=[[custom.Button.url(
                    "⬇️ Download this Beta", link
                )]],
                link_preview=False
            )

    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    JSON_FILE = {
        'stable': DEVICES_STABLE,
        'beta': DEVICES_BETA,
        'json_file_info': {"ver": 4, "generated_date": date}
    }
    f = open("update.json", "w+")

    ujson.dump(JSON_FILE, f, indent=1)
    f.close()
    with open('update.json', 'rb') as f:
        ftp.storbinary('STOR %s' % 'Others/update.json', f)

    ftp.quit()
    logger.info("Done!")


# Main
f = open("update.json", "r")
jfile = ujson.load(f)
DEVICES_STABLE = jfile['stable']
DEVICES_BETA = jfile['beta']

print(DEVICES_STABLE)
print(DEVICES_BETA)


@decorator.command("update")
async def do_update_devices(event):
    if event.chat_id not in fox_dev_chats:
        return
    msg = await event.reply("Updating...")
    await update_devices()
    await msg.edit('Done!')


@decorator.command("list")
@flood_limit_dec("list")
async def list_stable(event):
    if event.chat_id in fox_beta_groups:
        text = "**Beta testing devices:**\n"
        for device in DEVICES_BETA:
            text += "* {} (`{}`)\n".format(
                DEVICES_BETA[device]['fullname'], DEVICES_BETA[device]["codename"])
    elif event.chat_id in fox_groups:
        text = "**Supported devices:**\n"
        for device in DEVICES_STABLE:
            text += "* {} (`{}`)\n".format(
                DEVICES_STABLE[device]['fullname'], DEVICES_STABLE[device]["codename"])
    text += "\nTo get device write `/codename`"
    await event.reply(text)


@decorator.StrictCommand("^[/#](.*)")
async def check(event):
    device_arg = event.pattern_match.group(1).lower()
    if device_arg not in DEVICES_STABLE and device_arg not in DEVICES_BETA:
        return

    if event.chat_id in fox_beta_groups and device_arg in DEVICES_BETA:
        beta_device = DEVICES_BETA[device_arg]
        text = "📱 **" + beta_device['fullname'] + "** (`{}`)".format(beta_device['codename'])
        build = beta_device['ver']
        text += "\n📁 Last beta: `" + build + "`"
        text += "\n📅 Date: `" + beta_device['modified'] + "`"
        maintainer = beta_device['maintainer']
        text += "\n👨‍🔬 Maintainer: " + maintainer
        link_beta = "https://files.orangefox.website/OrangeFox-Beta/" + device_arg
        buttons = []
        if beta_device['msg']:
            text += "\n🗒️ Notes:\n" + beta_device['msg']
        if beta_device['readme']:
            buttons.append([custom.Button.url(
                f"📄 Readme file ({beta_device['readme']})", link_beta)])
        buttons.append([custom.Button.url("⬇️ Download beta", link_beta + "/" + build),
                       custom.Button.url("🗄️ All builds", link_beta)])
    elif event.chat_id in fox_groups and device_arg in DEVICES_STABLE:
        device = DEVICES_STABLE[device_arg]
        text = "📱 **" + device['fullname'] + "** (`{}`)".format(device['codename'])
        build = device['ver']
        text += "\n📁 Last build: `" + build + "`"
        text += "\n📅 Date: `" + device['modified'] + "`"
        maintainer = device['maintainer']
        text += "\n👨‍🔬 Maintainer: " + maintainer
        link_stable = "https://files.orangefox.website/OrangeFox-Stable/" + device_arg
        buttons = [[custom.Button.url("Download last", link_stable + "/" + build)]]
        link_mirror = "https://sourceforge.net/projects/orangefox/files/"
        buttons = []
        if device['msg']:
            text += "\n🗒️ Notes:\n" + device['msg']
        buttons.append([custom.Button.url("⬇️ Download last", link_stable + "/" + build)])
        if device['readme']:
            buttons.append([custom.Button.url(f"📄 Readme file ({device['readme']})", link_beta)])
        buttons.append([custom.Button.url("🗄️ All builds", link_stable),
                       custom.Button.url("☁️ Cloud", link_mirror + device_arg)])

    if not text:
        return
    await event.reply(text, buttons=buttons)
