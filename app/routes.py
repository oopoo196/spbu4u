# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from json import loads
from time import time

from flask import render_template, request, abort
from telebot.apihelper import ApiException
from telebot.types import Update

from app import app
from bot import bot
from bot.constants import webhook_url_base, webhook_url_path, ids
from bot.functions import delete_user, write_log, create_schedule_answer, get_json_interval_data


@app.route("/")
@app.route("/index")
def main_page():
    from requests import get
    from bot.bots_constants import yandex_key

    url = "https://api.rasp.yandex.net/v3.0/copyright/"
    params = {"apikey": yandex_key, "format": "json"}

    data = get(url, params=params).json()["copyright"]

    return render_template("index.html", bot_name="Spbu4UBot", url=data["url"],
                           text=data["text"])


@app.route("/reset_webhook", methods=["GET", "HEAD"])
def reset_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url_base + webhook_url_path)
    return "OK", 200


@app.route(webhook_url_path, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = Update.de_json(json_string)
        was_error = False
        tic = time()
        try:
            bot.process_new_updates([update])
        except Exception as err:
            answer = "Кажется, произошла ошибка.\n" \
                     "Возможно, информация по этому поводу есть в нашем " \
                     "канале - @Spbu4u_news\nИ ты всегда можешь связаться с " \
                     "<a href='https://t.me/eeonedown'>разработчиком</a>"
            was_error = True
            if update.message is not None:
                try:
                    bot.send_message(update.message.chat.id,
                                     answer,
                                     disable_web_page_preview=True,
                                     parse_mode="HTML")
                    bot.send_message(ids["my"],
                                     str(err) + "\n\nWas sent: True")
                except ApiException as ApiExcept:
                    json_err = loads(ApiExcept.result.text)
                    if json_err["description"] == "Forbidden: bot was " \
                                                  "blocked by the user":
                        delete_user(update.message.chat.id)
                        logging.info("USER LEFT {0}".format(
                            update.message.chat.id))
                    else:
                        logging.info("ERROR: {0}".format(
                            json_err["description"]))
            else:
                pass
        finally:
            write_log(update, time() - tic, was_error)
        return "OK", 200
    else:
        abort(403)


@app.route("/test_route", methods=["POST"])
def test_route():
    json_string = request.get_data().decode("utf-8")
    print(json_string)
    update = Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/<tid>")
def schedule(tid):
    from datetime import date

    user_id = tid

    json_week = get_json_interval_data(user_id, from_date=date(2018, 5, 2),
                                       to_date=date(2018, 5, 20))

    answers = []
    for day in json_week["Days"]:
        answers.append(
            create_schedule_answer(day, full_place=False, user_id=user_id)
        )

    return render_template("schedule.html", answers=answers)
