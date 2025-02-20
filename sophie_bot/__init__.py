# Copyright © 2018, 2019 MrYacha
# This file is part of SophieBot.
#
# SophieBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

import logging
import coloredlogs
import asyncio
import redis
import ujson
import sys

from flask import Flask

from aiogram.contrib.fsm_storage.redis import RedisStorage

from pymongo import MongoClient
from telethon import TelegramClient
from aiogram import Bot, Dispatcher, types

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s: %(message)s",
    level=logging.INFO)

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)


f = open('data/bot_conf.json', "r")

CONFIG = ujson.load(f)

logger.info("----------------------")
logger.info("|      SophieBot     |")
logger.info("----------------------")
logger.info("Powered by Telethon and AIOGram and bleck megic")

if not (platform := sys.platform == 'linux' or 'linux2'):
    logger.error("SophieBot support only Linux systems, your OS is " + platform)
    exit(1)

DEBUG_MODE = CONFIG["advanced"]["debug_mode"]
if DEBUG_MODE is True:
    logger.setLevel(logging.DEBUG)
    logger.warn("! Enabled debug mode, please don't use it on production to repect data privacy.")


OWNER_ID = int(CONFIG["basic"]["owner_id"])

SUDO = list(CONFIG["advanced"]["sudo"])
SUDO.append(OWNER_ID)

WL = list(CONFIG["advanced"]["whitelisted"])
WHITELISTED = SUDO + WL + [OWNER_ID] + [483808054]

API_ID = CONFIG["basic"]["app_id"]
API_HASH = CONFIG["basic"]["app_hash"]
MONGO_CONN = CONFIG["basic"]["mongo_conn"]
MONGO_PORT = CONFIG["basic"]["mongo_port"]
REDIS_COMM = CONFIG["basic"]["redis_conn"]
REDIS_PORT = CONFIG["basic"]["redis_port"]
TOKEN = CONFIG["basic"]["bot_token"]
NAME = TOKEN.split(':')[0] + CONFIG["advanced"]["bot_name_additional"]

# Init MongoDB
mongodb = MongoClient(MONGO_CONN).sophie

# Init Redis
redis = redis.StrictRedis(
    host=REDIS_COMM, port=REDIS_PORT, db='1', decode_responses=True)

tbot = TelegramClient(NAME, API_ID, API_HASH)

# Telethon
tbot.start(bot_token=TOKEN)

# AIOGram
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = RedisStorage()
dp = Dispatcher(bot, storage=storage)

# Flask
flask = Flask(__name__)

bot_info = asyncio.get_event_loop().run_until_complete(bot.get_me())
BOT_USERNAME = bot_info.username  # bot_info.username
BOT_ID = bot_info.id
