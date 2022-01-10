#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import re
import sys
import time
import logging
import datetime

from threading import Lock
from random import randrange
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

groups = []

task_num = 0
MINUTES_PER_DAY = 24 * 60
HELP_MESSAGE = '''
command: /remind "$message" $frequency
message: message to remind
frequency: how many time bot should work per day
'''

class Group:

    def __init__(self, message, frequency, group_id):
        self.tasks = []
        self.group_id = group_id
        self.tasks.append(Task(message, frequency, group_id))

    def add_task(self, message, frequency, group_id):
        self.tasks.append(Task(message, frequency, group_id))

class Task:

    def __init__(self, message, frequency, group_id):
        global task_num
        task_num += 1
        self.lock = Lock()
        self.message = message
        self.frequency = frequency
        self.group_id = group_id
        self.set_new_reminder()

    def set_new_reminder(self):
        timings = 0
        now = datetime.datetime.now()
        current_minute = now.minute + now.hour * 60
        self.lock.acquire()
        for i in range(int(self.frequency)):
            timing = randrange(MINUTES_PER_DAY)
            if(timing + current_minute < MINUTES_PER_DAY):
                job_queue.run_once(self.notify, timing * 60)
                print("{}:{}".format(int((timing+current_minute)/60), (timing+current_minute)%60), file=sys.stderr)
                timings += 1
        self.frequency_today = timings
        self.frequency_executed = 0
        self.lock.release()

    def set_today_reminder(self):
        self.lock.acquire()
        for i in range(self.frequency):
            timing = randrange(MINUTES_PER_DAY)
            print("{}:{}".format(int((timing)/60), (timing)%60), file=sys.stderr)
            job_queue.run_once(self.notify, timing * 60)
        self.frequency_today = self.frequency
        self.frequency_executed = 0

    def notify(self, context):
        self.lock.acquire()
        self.frequency_executed += 1
        bot.send_message(self.group_id, self.message)
        self.lock.release()

#def set_reminder(task):

def set_daily_reminders(context):
    for task in tasks:
        task.set_today_reminder()

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(HELP_MESSAGE)

def set_reminder_command(update: Update, context: CallbackContext) -> None:
    """Set reminders."""
    text = update.message.text
    match = re.search("^/remind \"(.+)\" (\d+)$", text)
    if not match:
        update.message.reply_text(HELP_MESSAGE)
    else:
        message = match.group(1)
        frequency = match.group(2)
        group_id = update.message.chat.id
        for group in groups:
            if group_id == group.group_id:
                group.add_task(message, frequency, group_id)
                bot.send_message(group_id, "Task set!")
                return
        groups.append(Group(message, frequency, group_id))
        bot.send_message(group_id, "Task set!")

    '''
    '''
def list_command(update: Update, context: CallbackContext) -> None:
    """List reminders."""
    group_id = update.message.chat.id
    for group in groups:
        if group_id == group.group_id:
            message = ""
            for i, task in enumerate(group.tasks):
                message += "{}. 每日關心{}({}/{})\n".format(i + 1, task.message, task.frequency_executed, task.frequency_today)
            bot.send_message(task.group_id, message)
            return
    bot.send_message(group_id, "No reminder!")


def main() -> None:
    """Start the bot."""
    global bot
    global job_queue

    # Create the Updater and pass it your bot's token.
    updater = Updater("YOUR_TOKEN")
    bot = updater.bot
    job_queue = updater.job_queue
    job_queue.run_daily(set_daily_reminders, datetime.time(0, 0, 0))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("remind", set_reminder_command))
    dispatcher.add_handler(CommandHandler("list", list_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
