# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import sqlite3
from datetime import datetime, date, timedelta

import spbu
from telebot.apihelper import ApiException


def insert_skip(event_name, types, event_day, event_time,
                educators, user_id, is_choose_educator=False):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    try:
        cursor.execute("""INSERT INTO lessons 
                          (name, types, day, time, educators) 
                              VALUES (?, ?, ?, ?, ?)""",
                       (event_name, types, event_day, event_time, educators))
        sql_con.commit()
    except sqlite3.IntegrityError:
        sql_con.rollback()
    finally:
        cursor.execute("""SELECT id 
                          FROM lessons 
                          WHERE name = ? 
                            AND types = ? 
                            AND day = ? 
                            AND time = ?
                            AND educators = ?""",
                       (event_name, types, event_day, event_time, educators))
        lesson_id = cursor.fetchone()[0]
    try:
        if is_choose_educator:
            cursor.execute("""INSERT INTO user_educators VALUES (?, ?)""",
                           (user_id, lesson_id))
        else:
            cursor.execute("""INSERT INTO skips VALUES (?, ?)""",
                           (lesson_id, user_id))
        sql_con.commit()
    except sqlite3.IntegrityError:
        sql_con.rollback()
    finally:
        cursor.close()
        sql_con.close()


def get_hide_lessons_data(user_id, db_path="Bot.db", week_day=None,
                          is_educator=False):
    sql_con = sqlite3.connect(db_path)
    cursor = sql_con.cursor()
    sql_req = """SELECT
                   s.lesson_id,
                   l.name,
                   l.types,
                   l.day,
                   l.time,
                   l.educators
              """
    if is_educator:
        sql_req += """FROM user_educators AS s
                        JOIN lessons AS l
                          ON l.id = s.lesson_id
                   """
    else:
        sql_req += """FROM skips AS s
                        JOIN lessons AS l
                          ON l.id = s.lesson_id
                   """
    sql_req += """WHERE user_id = ?"""
    req_param = (user_id,)
    if week_day:
        sql_req += "  AND (day = 'all' OR day = ?)"
        req_param += (week_day, )
    cursor.execute(sql_req, req_param)
    data = cursor.fetchall()
    cursor.close()
    sql_con.close()
    return data


def get_chosen_educators(user_id, dp_path="Bot.db"):
    sql_con = sqlite3.connect(dp_path)
    cursor = sql_con.cursor()
    data = {}
    sql_req = """SELECT
                   lessons.name,
                   lessons.educators
                 FROM user_educators
                   JOIN lessons
                     ON user_educators.lesson_id = lessons.id
                 WHERE user_educators.user_id = ?"""
    for row in cursor.execute(sql_req, (user_id,)):
        if row[0] in data.keys():
            data[row[0]].add(row[1])
        else:
            data[row[0]] = {row[1]}
    return data


def delete_user(user_id, only_choice=False):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""DELETE FROM user_choice 
                      WHERE user_id = ?""", (user_id,))
    sql_con.commit()
    if not only_choice:
        cursor.execute("""DELETE FROM user_groups 
                          WHERE user_id = ?""", (user_id,))
        sql_con.commit()
        cursor.execute("""DELETE FROM skips 
                          WHERE user_id = ?""", (user_id,))
        sql_con.commit()
        cursor.execute("""DELETE FROM user_data 
                          WHERE id = ?""", (user_id,))
        sql_con.commit()
    cursor.close()
    sql_con.close()


def date_from_iso(iso):
    return datetime.strptime("%d%02d%d" % (iso[0], iso[1], iso[2]),
                             "%Y%W%w").date()


def get_current_monday_date():
    from flask_app import server_timedelta
    iso_day_date = list((date.today() + server_timedelta).isocalendar())
    if iso_day_date[2] == 7:
        iso_day_date[1] += 1
    iso_day_date[2] = 1
    monday_date = date_from_iso(iso_day_date)
    return monday_date


def get_json_week_data(user_id, next_week=False):
    if next_week:
        return get_json_week_data_api(user_id, next_week=True)
    else:
        sql_con = sqlite3.connect("Bot.db")
        cursor = sql_con.cursor()
        cursor.execute("""SELECT json_week_data
                          FROM groups_data
                            JOIN user_data
                              ON groups_data.id = user_data.group_id
                          WHERE  user_data.id= ?""", (user_id, ))
        data = cursor.fetchone()

        json_week_data = json.loads(data[0])
        cursor.close()
        sql_con.close()

    return json_week_data


def get_json_week_data_api(user_id, next_week=False, for_day=None):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT group_id
                      FROM user_data 
                      WHERE  id= ?""", (user_id,))
    group_id = cursor.fetchone()[0]
    cursor.close()
    sql_con.close()

    if for_day:
        monday_date = for_day
    elif next_week:
        monday_date = get_current_monday_date()
        monday_date += timedelta(days=7)
    else:
        monday_date = get_current_monday_date()

    json_week_data = spbu.get_group_events(group_id=group_id,
                                           from_date=monday_date)
    return json_week_data


def get_json_day_data(user_id, day_date, json_week_data=None, next_week=False):
    if json_week_data is None:
        json_week_data = get_json_week_data(user_id, next_week)
    for day_info in json_week_data["Days"]:
        if datetime.strptime(day_info["Day"],
                             "%Y-%m-%dT%H:%M:%S").date() == day_date:
            return day_info
    return None


def is_event_in_skips(event, skips, week_day_string):
    event_educators = []
    for educator in event["EducatorIds"]:
        if educator["Item1"] != -1:
            event_educators.append(educator["Item2"].split(", ")[0])
    event_educators = set(event_educators)

    for skip_lesson in skips:
        skip_educators = set(skip_lesson[5].split("; "))
        stripped_type = " ".join(event["Subject"].split(", ")[-1].split()[:2])
        if skip_lesson[1] == ", ".join(event["Subject"].split(", ")[:-1]) and \
                (skip_lesson[2] == "all" or
                 stripped_type in skip_lesson[2].split("; ")) and \
                (skip_lesson[3] == "all" or
                 skip_lesson[3] == week_day_string) and \
                (skip_lesson[4] == "all" or
                 skip_lesson[4] == event["TimeIntervalString"]) and \
                (skip_lesson[5] == "all" or
                 event_educators.issubset(skip_educators)):
            return True
    return False


def create_schedule_answer(day_info, full_place, user_id=None, personal=True,
                           db_path="Bot.db", only_exams=False):
    from constants import emoji, subject_short_type

    if day_info is None:
        return emoji["sleep"] + " Выходной"

    answer = emoji["calendar"] + " "
    answer += day_info["DayString"].capitalize() + "\n\n"
    day_study_events = day_info["DayStudyEvents"]

    if personal:
        skips = get_hide_lessons_data(user_id, db_path,
                                      day_info["DayString"].split(", ")[0])
        chosen_educators = get_chosen_educators(user_id)
    else:
        skips = []
        chosen_educators = {}

    for event in day_study_events:
        if event["IsCancelled"] or \
                (only_exams and "пересдача" in event["Subject"]) or \
                (only_exams and "консультация" in event["Subject"]) or \
                (only_exams and "комиссия" in event["Subject"]) or \
                is_event_in_skips(event, skips,
                                  day_info["DayString"].split(", ")[0]):
            continue
        if event["IsAssigned"]:
            answer += emoji["new"] + " "
        answer += emoji["clock"] + " " + event["TimeIntervalString"]
        if event["TimeWasChanged"]:
            answer += " " + emoji["warning"]
        answer += "\n<b>"
        subject_name = ", ".join(event["Subject"].split(", ")[:-1])
        subject_type = event["Subject"].split(", ")[-1]
        stripped_subject_type = " ".join(subject_type.split()[:2])
        if stripped_subject_type in subject_short_type.keys():
            answer += subject_short_type[stripped_subject_type] + " - "
        else:
            answer += subject_type.upper() + " - "
        answer += subject_name + "</b>\n"
        have_chosen_educator = False
        if subject_name in chosen_educators.keys() and \
                any(ch_edu in [edu["Item2"].split(", ")[0] for edu in
                               event["EducatorIds"]] for ch_edu in
                    chosen_educators[subject_name]):
            have_chosen_educator = True
        for location in event["EventLocations"]:
            if location["IsEmpty"]:
                continue

            if have_chosen_educator and not chosen_educators[
                subject_name].issuperset({edu["Item2"].split(", ")[0] for edu in
                                          location["EducatorIds"]}):
                continue
            if full_place:
                location_name = location["DisplayName"].strip(", ").strip()
            else:
                location_name = location["DisplayName"].split(", ")[-1].strip()
            answer += location_name
            if location["HasEducators"]:
                educators = [educator["Item2"].split(", ")[0] for educator in
                             location["EducatorIds"] if educator["Item1"] != -1]
                if len(educators):
                    answer += " <i>({0})</i>".format("; ".join(educators))
            if event["LocationsWereChanged"] or \
                    event["EducatorsWereReassigned"]:
                answer += " " + emoji["warning"]
            answer += "\n"
        answer += "\n"

    if len(answer.strip().split("\n\n")) == 1:
        return emoji["sleep"] + " Выходной"

    return answer


def create_master_schedule_answer(day_info):
    from constants import emoji, subject_short_type
    answer = "{0} {1}\n\n".format(emoji["calendar"], day_info["DayString"])
    for event in day_info["DayStudyEvents"]:
        answer += "{0} {1} <i>({2})</i>\n".format(
            emoji["clock"], event["TimeIntervalString"],
            "; ".join(event["Dates"]))
        answer += "<b>"
        subject_type = event["Subject"].split(", ")[-1]
        stripped_subject_type = " ".join(subject_type.split()[:2])
        if stripped_subject_type in subject_short_type.keys():
            answer += subject_short_type[stripped_subject_type] + " - "
        else:
            answer += subject_type.upper() + " - "
        answer += ", ".join(
            event["Subject"].split(", ")[:-1]) + "</b>\n"
        for location in event["EventLocations"]:
            location_name = location["DisplayName"]
            answer += location_name + " <i>({0})</i>\n".format(
                "; ".join(name["Item1"] for name in
                          event["ContingentUnitNames"]))
        answer += "\n"
    return answer


def is_user_exist(user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT count(id) 
                      FROM user_data
                      WHERE id = ?""", (user_id,))
    data = cursor.fetchone()
    cursor.close()
    sql_con.close()
    return data[0]


def is_sending_on(user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT sending 
                      FROM user_data
                      WHERE id = ?""", (user_id,))
    data = cursor.fetchone()
    cursor.close()
    sql_con.close()
    return data[0]


def set_sending(user_id, on=True):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""UPDATE user_data
                      SET sending = ?
                      WHERE id = ?""",
                   (int(on), user_id))
    sql_con.commit()
    cursor.close()
    sql_con.close()


def select_all_users():
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT id 
                      FROM user_data""")
    ids = cursor.fetchall()
    cursor.close()
    sql_con.close()
    return ids


def is_full_place(user_id, db_path="Bot.db"):
    sql_con = sqlite3.connect(db_path)
    cursor = sql_con.cursor()
    cursor.execute("""SELECT full_place 
                      FROM user_data
                      WHERE id = ?""", (user_id,))
    data = cursor.fetchone()
    cursor.close()
    sql_con.close()
    return data[0]


def set_full_place(user_id, on=True):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""UPDATE user_data
                      SET full_place = ?
                      WHERE id = ?""",
                   (int(on), user_id))
    sql_con.commit()
    cursor.close()
    sql_con.close()


def get_rate_statistics():
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT sum(rate), count(id) 
                      FROM user_data
                      WHERE rate != 0""")
    data = cursor.fetchone()
    cursor.close()
    sql_con.close()
    if data[0] is None:
        return None
    else:
        return [data[0] / data[1], data[1]]


def set_rate(user_id, count_of_stars):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""UPDATE user_data
                      SET rate = ?
                      WHERE id = ?""",
                   (int(count_of_stars), user_id))
    sql_con.commit()
    cursor.close()
    sql_con.close()


def write_log(update, work_time, was_error=False):
    if update.message is not None:
        chat_id = update.message.chat.id
        user_text = update.message.text
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
        user_text = update.callback_query.data
    else:
        chat_id = "ERROR"
        user_text = str(update)
    log = "CHAT: {0} ===== TEXT: {1} ===== TIME: {2}".format(
        chat_id, user_text, work_time)
    if was_error:
        log += "        ERROR"
    logging.info(log)


def get_templates(user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT gd.id, gd.title
                      FROM user_groups AS ug
                        JOIN groups_data AS gd
                          ON ug.group_id = gd.id
                      WHERE ug.user_id = ?;""", (user_id,))
    data = cursor.fetchall()
    cursor.close()
    sql_con.close()
    groups = {}
    for group in data:
        groups[group[1]] = group[0]
    return groups


def get_current_group(user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT groups_data.id, groups_data.title
                      FROM groups_data
                        JOIN user_data u ON groups_data.id = u.group_id
                      WHERE u.id = ?""", (user_id, ))
    group_data = cursor.fetchone()
    return group_data


def save_group(group_id, user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    try:
        cursor.execute("""INSERT INTO user_groups VALUES (?, ?)""",
                       (group_id, user_id))
        sql_con.commit()
    except sqlite3.IntegrityError:
        sql_con.rollback()
    finally:
        cursor.close()
        sql_con.close()


def delete_group(group_id, user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    try:
        cursor.execute("""DELETE FROM user_groups 
                          WHERE group_id = ? 
                            AND user_id = ?""",
                       (group_id, user_id))
        sql_con.commit()
    except sqlite3.IntegrityError:
        sql_con.rollback()
    finally:
        cursor.close()
        sql_con.close()


def get_statistics_for_admin():
    data = {}
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()

    cursor.execute("""SELECT count(id)
                      FROM user_data""")
    data["count_of_users"] = cursor.fetchone()[0]

    cursor.execute("""SELECT count(id)
                      FROM groups_data""")
    data["count_of_groups"] = cursor.fetchone()[0]

    cursor.execute("""SELECT count(id)
                      FROM user_data
                      WHERE sending = 1
                      GROUP BY sending""")
    r_data = cursor.fetchone()
    data["count_of_sending"] = 0 if r_data is None else r_data[0]

    cursor.close()
    sql_con.close()
    return data


def get_station_code(user_id, is_home):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    if is_home:
        cursor.execute("""SELECT home_station_code
                          FROM user_data
                          WHERE id = ?""", (user_id,))
    else:
        cursor.execute("""SELECT univer_station_code
                          FROM user_data
                          WHERE id = ?""", (user_id,))
    station_code = cursor.fetchone()[0]
    cursor.close()
    sql_con.close()
    return station_code


def change_station(user_id, station_code, is_home):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    if is_home:
        cursor.execute("""UPDATE user_data
                          SET home_station_code = ?
                          WHERE id = ?""",
                       (station_code, user_id))
    else:
        cursor.execute("""UPDATE user_data
                          SET univer_station_code = ?
                          WHERE id = ?""",
                       (station_code, user_id))
    sql_con.commit()
    cursor.close()
    sql_con.close()


def send_long_message(bot, text, user_id, split="\n\n"):
    try:
        bot.send_message(user_id, text, parse_mode="HTML")
    except ApiException as ApiExcept:
        json_err = json.loads(ApiExcept.result.text)
        if json_err["description"] == "Bad Request: message is too long":
            event_count = len(text.split(split))
            first_part = split.join(text.split(split)[:event_count // 2])
            second_part = split.join(text.split(split)[event_count // 2:])
            send_long_message(bot, first_part, user_id, split)
            send_long_message(bot, second_part, user_id, split)


def get_user_rate(user_id):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT rate
                      FROM user_data
                      WHERE id = ?""", (user_id,))
    rate = cursor.fetchone()[0]
    cursor.close()
    sql_con.close()
    return rate


def is_correct_educator_name(text):
    return text.replace(".", "").replace("-", "").replace(" ", "").isalnum()


def text_to_date(text):
    from constants import months

    text = text.replace(".", " ")
    if text.replace(" ", "").isalnum():
        words = text.split()[:3]
        for word in words:
            if not (
                    word.isdecimal() or (
                        word.isalpha() and (word.lower() in months.keys())
                    )
            ):
                return False
        try:
            day = int(words[0])
            month = datetime.today().month
            year = datetime.today().year
            if len(words) > 1:
                month = int(words[1]) if words[1].isdecimal() else months[
                    words[1]]
                if len(words) > 2:
                    year = int(words[2])
            return datetime.today().replace(day=day, month=month,
                                            year=year).date()
        except ValueError:
            return False
    return False


def add_new_user(user_id, group_id, group_title=None):
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    if group_title is None:
        group_title = spbu.get_group_events(group_id)[
                          "StudentGroupDisplayName"][7:]
    try:
        cursor.execute("""INSERT INTO groups_data 
                          (id, title)
                          VALUES (?, ?)""",
                       (group_id, group_title))
    except sqlite3.IntegrityError:
        sql_con.rollback()
    finally:
        json_week = json.dumps(spbu.get_group_events(group_id))
        cursor.execute("""UPDATE groups_data
                          SET json_week_data = ?
                          WHERE id = ?""",
                       (json_week, group_id))
        sql_con.commit()
    try:
        cursor.execute("""INSERT INTO user_data (id, group_id)
                          VALUES (?, ?)""",
                       (user_id, group_id))
    except sqlite3.IntegrityError:
        sql_con.rollback()
        cursor.execute("""UPDATE user_data 
                          SET group_id = ?
                          WHERE id = ?""",
                       (group_id, user_id))
    finally:
        sql_con.commit()
        cursor.execute("""DELETE FROM user_choice WHERE user_id = ?""",
                       (user_id,))
        sql_con.commit()
        cursor.close()
        sql_con.close()


def get_semester_dates():
    today = datetime.today()
    if today.month in range(2, 8):
        start_year = today.year
        end_year = today.year
        start_month = 2
        end_month = 8
    else:
        start_year = today.year - 1 if today.month < 2 else today.year
        end_year = today.year + 1 if today.month > 7 else today.year
        start_month = 8
        end_month = 2

    return [date(year=start_year, month=start_month, day=1),
            date(year=end_year, month=end_month, day=1)]


def get_json_attestation(user_id):
    sem_dates = get_semester_dates()
    group_id = get_current_group(user_id)[0]
    req = spbu.get_group_events(group_id=group_id,
                                from_date=sem_dates[0],
                                to_date=sem_dates[1],
                                lessons_type="Attestation")
    return req


def get_available_months(user_id):
    from constants import months_date

    json_att = get_json_attestation(user_id)
    available_months = {}
    for day_data in json_att["Days"]:
        data = datetime.strptime(day_data["Day"], "%Y-%m-%dT%H:%M:%S")
        available_months[data.month] = "{0} {1}".format(months_date[data.month],
                                                        data.year)
    return available_months


def get_blocks(user_id, day_date):
    from constants import emoji, subject_short_type

    json_day = get_json_day_data(user_id, day_date)
    day_string = json_day["DayString"].capitalize()

    day_study_events = json_day["DayStudyEvents"]
    block_answers = []
    item_block_num = 0
    for num, event in enumerate(day_study_events):
        if event["IsCancelled"]:
            continue
        answer = "\n<b>{ibn}. "
        subject_type = event["Subject"].split(", ")[-1]
        stripped_subject_type = " ".join(subject_type.split()[:2])
        if stripped_subject_type in subject_short_type.keys():
            answer += subject_short_type[stripped_subject_type] + " - "
        else:
            answer += subject_type.upper() + " - "
        answer += ", ".join(event["Subject"].split(", ")[:-1]) + "</b>"
        if is_event_in_skips(event, get_hide_lessons_data(
                user_id, week_day=json_day["DayString"].split(", ")[0]),
                             json_day["DayString"].split(", ")[0]):
            answer += " {0}".format(emoji["cross_mark"])
        answer += "\n"
        for location in event["EventLocations"]:
            if location["IsEmpty"]:
                continue
            location_name = location["DisplayName"].strip(", ")
            answer += location_name
            if location["HasEducators"]:
                educators = [educator["Item2"].split(", ")[0] for educator in
                             location["EducatorIds"] if educator["Item1"] != -1]
                if len(educators):
                    answer += " <i>({0})</i>".format("; ".join(educators))
            answer += "\n"
        if num != 0 and event["TimeIntervalString"] == \
                day_study_events[num - 1]["TimeIntervalString"]:
            item_block_num += 1
            block_answers[-1] += answer.format(ibn=item_block_num + 1)
        else:
            item_block_num = 0 if num != 0 else item_block_num
            answer = "{0} {1}\n".format(emoji["clock"],
                                        event["TimeIntervalString"]) + answer
            block_answers.append(answer.format(ibn=item_block_num + 1))
    return day_string, [block + "\nВыбери занятие:" for block in block_answers]


def get_current_block(message_text, user_id, is_prev=False):
    from flask_app import server_timedelta
    from constants import week_day_number, week_day_titles
    current_block = int(message_text.split(" ")[0]) - 1
    day_string = message_text.split(")")[0].split("(")[-1]

    iso_day_date = list((datetime.today() + server_timedelta).isocalendar())
    if iso_day_date[2] == 7:
        iso_day_date[1] += 1
    iso_day_date[2] = week_day_number[week_day_titles[day_string]]
    day_date = date_from_iso(iso_day_date)

    blocks = get_blocks(user_id, day_date)[1]
    if is_prev:
        block_index = (current_block - 1) % len(blocks)
    else:
        block_index = (current_block + 1) % len(blocks)

    block = blocks[block_index]
    answer = "<b>{0} из {1}</b> <i>({2})</i>\n\n{3}".format(
        (block_index % len(blocks) + 1), len(blocks), day_string, block)
    events = [event.split("\n")[0] for event in block.split("\n\n")[1:-1]]
    return answer, events


def get_lessons_with_educators(user_id, day_date):
    from constants import emoji

    json_day = get_json_day_data(user_id, day_date)
    answer = ""
    day_study_events = json_day["DayStudyEvents"]
    count = 0
    for event in day_study_events:
        event_text = ""
        if event["IsCancelled"] or len([loc for loc in event["EventLocations"]
                                        if loc["HasEducators"]]) < 2:
            continue
        subject_name = ", ".join(event["Subject"].split(", ")[:-1])
        event_text += "{0}</b>".format(subject_name)
        if is_event_in_skips(event, get_hide_lessons_data(
                user_id, week_day=json_day["DayString"].split(", ")[0]),
                             json_day["DayString"].split(", ")[0]):
            event_text += " {0}".format(emoji["cross_mark"])
        event_text += "\n"

        chosen_educators = get_chosen_educators(user_id)
        have_chosen_educator = False
        if subject_name in chosen_educators.keys() and \
                any(ch_edu in [edu["Item2"].split(", ")[0] for edu in
                               event["EducatorIds"]] for ch_edu in
                    chosen_educators[subject_name]):
            have_chosen_educator = True
        for location in event["EventLocations"]:
            event_text += location["DisplayName"].strip(", ")
            educators = {educator["Item2"].split(", ")[0] for educator in
                         location["EducatorIds"] if educator["Item1"] != -1}
            if len(educators):
                event_text += " <i>({0})</i>".format("; ".join(educators))
            if have_chosen_educator and educators.issubset(chosen_educators[
                                                               subject_name]):
                event_text += " {0}".format(emoji["heavy_check_mark"])
            event_text += "\n"
        if event_text not in answer:
            count += 1
            answer += "<b>{0}. {1}\n".format(count, event_text)
    if answer == "":
        data = {"is_empty": True, "answer": "Подходящих занятий нет",
                "date": json_day["DayString"].capitalize()}
    else:
        data = {"is_empty": False, "answer": answer.strip("\n\n"),
                "date": json_day["DayString"].capitalize()}
    return data


def create_session_answer(json_attestation, month, user_id, full_place,
                          personal, only_exams):
    answer = ""
    for day_data in json_attestation["Days"]:
        event_date = datetime.strptime(day_data["Day"], "%Y-%m-%dT%H:%M:%S")
        if month == str(event_date.month):
            cur_answer = create_schedule_answer(
                day_data, full_place, user_id=user_id, personal=personal,
                only_exams=only_exams)
            if "Выходной" not in cur_answer:
                answer += cur_answer.replace("\n\n", "\n") + "\n"
    return answer


def get_key_by_value(dct, val):
    return [it[0] for it in dct.items() if it[1] == val][0]


def get_random_group_id():
    sql_con = sqlite3.connect("Bot.db")
    cursor = sql_con.cursor()
    cursor.execute("""SELECT group_id
                      FROM user_data
                      LIMIT 1""")
    group_id = cursor.fetchone()[0]
    sql_con.commit()
    cursor.close()
    sql_con.close()
    return group_id
