#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A telegram bot lets you search wikipedia

@author Guy Sheffer (GuySoft) <guysoft at gmail dot com>
"""
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler, RegexHandler
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)
from telegram import InlineKeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import ParseMode
from emoji import emojize
import logging
import traceback
from configparser import ConfigParser
from collections import OrderedDict
import os
import json
import wikipedia
import sys
import time
from urllib.request import urlopen, URLError

DIR = os.path.dirname(__file__)


def ini_to_dict(path):
    """ Read an ini path in to a dict

    :param path: Path to file
    :return: an OrderedDict of that path ini data
    """
    config = ConfigParser()
    config.read(path)
    return_value=OrderedDict()
    for section in reversed(config.sections()):
        return_value[section]=OrderedDict()
        section_tuples = config.items(section)
        for itemTurple in reversed(section_tuples):
            return_value[section][itemTurple[0]] = itemTurple[1]
    return return_value


class TelegramCallbackError(Exception):
    def __init__(self, message=""):
        self.message = message


class CronJobsError(Exception):
    def __init__(self, message = ""):
        self.message = message


def build_callback(data):
    return_value = json.dumps(data)
    if len(return_value) > 64:
        raise TelegramCallbackError("Callback data is larger tan 64 bytes")
    return return_value


def get_job_id(job):
    try:
        return job.comment.split(" ")[1]
    except IndexError:
        print(str(traceback.format_exc()))
        return None


def handle_cancel(update):
    query = update.message.text
    if query == "Close" or query == "/cancel":
        reply = "Perhaps another time"
        update.message.reply_text(reply)
        return reply
    return None


def get_articles(search):
    try:
        wikipedia.summary(search)
    except wikipedia.exceptions.DisambiguationError as e:
        return e.options
    except wikipedia.exceptions.PageError:
        return []
    except ValueError:
        return []
    return [search]


class Bot:
    def __init__(self, token):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(start_handler)

        self.ARTICLE_RESULTS, self.ARTICLES_ANSWER = range(2)

        # Add conversation handler with the states ALARM_TYPE, DAILY, WEEKDAY, HOUR
        set_article_handler = ConversationHandler(
            entry_points=[RegexHandler('[^!(\/help)](.*)$', self.get_article_results, pass_chat_data=True)],
            states={

                self.ARTICLES_ANSWER: [RegexHandler('^(.*)$', self.get_article, pass_chat_data=True)]
            },
            fallbacks=[]
        )
        self.dispatcher.add_handler(set_article_handler)

        help_handler = CommandHandler('help', self.help)
        self.dispatcher.add_handler(help_handler)

        self.dispatcher.add_error_handler(self.error_callback)

        # self.dispatcher.add_handler(echo_handler)

        return

    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="I'm a Wikipedia bot, send me an article you want to"
                                                              " search for, please type /help for info")
        return

    def get_article_results(self, bot, update, chat_data):
        keyboard = []
        suggestion = None

        search = update.message.text.strip()
        results = get_articles(search)

        chat_data["results"] = results

        # We found just what we were looking for!
        if len(results) == 1:
            return self.get_article(bot, update, chat_data)

        # We found nothing, try looking for suggestions
        if len(results) == 0:
            suggestion = wikipedia.suggest(search)
            results = get_articles(suggestion)
            chat_data["results"] = results

            # Ok, no article, no suggestion
            if len(results) == 0:
                reply = "No article found"
                update.message.reply_text(reply)
                return ConversationHandler.END

        for result in results:
            keyboard.append([InlineKeyboardButton(result)])

        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        reply = ""

        if suggestion is not None:
            reply += 'Did you mean "' + suggestion + '"?\n'

        reply += 'Please select one of the results, or /cancel to cancel:'

        update.message.reply_text(reply, reply_markup=reply_markup)
        return self.ARTICLES_ANSWER
        return ConversationHandler.END

    def get_article(self, bot, update, chat_data):
        article = update.message.text

        reply = handle_cancel(update)
        if reply is None:

            if article in chat_data["results"]:
                page = wikipedia.page(article)
                bot.send_message(chat_id=update.message.chat_id, text=page.summary,
                                 parse_mode=ParseMode.HTML)

            else:
                update.message.reply_text("Article not in list")
        else:
            return ConversationHandler.END
        return ConversationHandler.END
    
    def cancel(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Perhaps another timefff")
        return ConversationHandler.END

    def error_callback(self, bot, update, error):
        try:
            raise error
        except Unauthorized as e:
            # remove update.message.chat_id from conversation list
            pass
        except BadRequest:
            # handle malformed requests - read more below!
            pass
        except TimedOut:
            # handle slow connection problems
            pass
        except NetworkError:
            # handle other connection problems
            pass
        except ChatMigrated as e:
            # the chat_id of a group has changed, use e.new_chat_id instead
            pass
        except TelegramError:
            # handle all other telegram related errors
            pass
        return

    def help(self, bot, update):
        icon = emojize(":information_source: ", use_aliases=True)
        text = icon + " The following commands are available:\n"

        commands = [["Any text", "Search for an article"],
                    ["/help", "Get this message"]
                    ]

        for command in commands:
            text += command[0] + " " + command[1] + "\n"

        bot.send_message(chat_id=update.message.chat_id, text=text)

    def run(self):
        self.updater.start_polling()
        return


def check_connectivity(reference):
    try:
        urlopen(reference, timeout=1)
        return True
    except URLError:
        return False


def wait_for_internet():
    while not check_connectivity("https://api.telegram.org"):
        print("Waiting for internet")
        time.sleep(1)


if __name__ == "__main__":
    config_file_path = os.path.join(DIR, "config.ini")
    settings = ini_to_dict(config_file_path)
    if not config_file_path:
        print("Error, no config file")
        sys.exit(1)
    if ("main" not in settings) or ("token" not in settings["main"]):
        print("Error, no token in config file")

    wait_for_internet()

    a = Bot(settings["main"]["token"])
    a.run()
    print("Bot Started")
