# -*- coding: utf-8 -*-
import hmac
from hashlib import sha256


test_token = ""
release_token = ""
yandex_key = ""
secret_key = ""

sha_string = hmac.new(bytearray(secret_key, "utf-8"),
                      bytearray(test_token, "utf-8"),
                      sha256).hexdigest()

my_id = 200466757
ks_id = 71591548

webhook_host = "eeonedown.pythonanywhere.com"
webhook_port = 443
webhook_url_base = "https://{}:{}".format(webhook_host, webhook_port)
webhook_url_path = "/{}/".format(sha_string)


emoji = {"info": u"\U00002139", "star": u"\U00002B50",
         "settings": u"\U00002699", "suburban": u"\U0001F689",
         "editor": u"\U0001F4DD", "alarm_clock": u"\U000023F0",
         "calendar": u"\U0001F4C5", "sleep": u"\U0001F634",
         "clock": u"\U0001F552", "cross_mark": u"\U0000274C",
         "check_mark": u"\U00002705", "mailbox_off": u"\U0001F4EA",
         "mailbox_on": u"\U0001F4EB", "door": u"\U0001F6AA",
         "school": u"\U0001F3EB", "disappointed": u"\U0001F61E",
         "cold_sweat": u"\U0001F613", "halo": u"\U0001F607",
         "smile": u"\U0001F604", "bullet": u"\U00002022",
         "horns": u"\U0001F608", "orange_diamond": u"\U0001F538",
         "blue_diamond": u"\U0001F539", "runner": u"\U0001F3C3",
         "arrow_up": u"\U00002B06", "warning": u"\U000026A0",
         "arrows_counterclockwise": u"\U0001F504",
         "bust_in_silhouette": u"\U0001F464", "back": u"\U0001F519",
         "mag_right": u"\U0001F50E", "arrow_backward": u"\U000025C0",
         ":arrow_forward:": u"\U000025B6"}

week_day_number = {"Пн": 1, "Вт": 2, "Ср": 3, "Чт": 4, "Пт": 5, "Сб": 6}
week_day_titles = {"Понедельник": "Пн", "Вторник": "Вт", "Среда": "Ср",
                   "Четверг": "Чт", "Пятница": "Пт", "Суббота": "Сб"}

subject_short_type = {"лекция": "Л", "практическое занятие": "ПР",
                      "семинар": "С", "урок": "У", "лабораторная работа": "ЛР",
                      "сам. работа в присутствии преподавателя": "СР"}
subject_short_type_revert = {"Л": "лекция", "ПР": "практическое занятие",
                             "С": "семинар", "У": "урок",
                             "ЛР": "лабораторная работа",
                             "СР": "сам. работа в присутствии преподавателя"}

all_stations = {"Санкт-Петербург": "c2", "Броневая": "s9603500",
                "Ленинский Проспект": "s9603435", "Лигово": "s9603837",
                "Сосновая Поляна": "s9603431", "Стрельна": "s9603542",
                "Новый Петергоф": "s9603887", "Старый Петергоф": "s9603547",
                "Университетская (Университет)": "s9603770",
                "Ораниенбаум-1": "s9603138", "Лебяжье": "s9602688",
                "Калище": "s9602687"}
all_stations_const = ["Санкт-Петербург", "Броневая", "Ленинский Проспект",
                      "Лигово", "Сосновая Поляна", "Стрельна", "Новый Петергоф",
                      "Старый Петергоф", "Университетская (Университет)",
                      "Ораниенбаум-1", "Лебяжье", "Калище"]

full_info_answer = \
    'ИНФОРМАЦИЯ\n\n' \
    '<b>Раздел "Расписание"</b>\n\n' \
    '{} Информация о расписании берется с <b>официального сайта расписания ' \
    'СПбГУ</b> - https://timetable.spbu.ru\n' \
    '{} Информация о паре формируется следующим образом:\n' \
    '    Время\n' \
    '    Тип - Название пары\n' \
    '    Адрес1 (преподаватели);\n' \
    '    Адрес2 (преподаватели);\n' \
    '    и т.д.\n' \
    '{} В любой день расписание смотрится по <b>текущей</b> неделе до ' \
    'ВОСКРЕСЕНЬЯ. В воскресенье расписание будет показано для следующей ' \
    'недели.\n' \
    '{} Если занятие <i>отменено</i>, бот его не пришлет.\n' \
    '{} {} позволит посмотреть расписание на любой день недели или на ' \
    'неделю полностью. После выбора дня бот пришлет расписание для ' \
    '<b>текущей</b> недели, а также предложит посмотреть расписание для ' \
    'следующей.\n' \
    '{} В этом же разделе можно <i>подписаться на рассылку</i> расписания ' \
    '- {}. Рассылка производится каждый день в 21:00. О выходных днях бот ' \
    'не уведомляет.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    '{} Можно вызвать командой /settings.\n' \
    '{} Во время <i>смены группы</i> можно воспользоваться командой ' \
    '<b>Назад</b> (или /home) для возврата в <i>Главное меню</i>.\n' \
    '{} Если ты решишь прекратить пользоваться ботом, пожалуйста, ' \
    '<b>заверши работу</b> с ним (для этого необходимо написать /exit или ' \
    'выбрать <b>“Завершить работу”</b> в меню настроек. Просто удалить ' \
    'диалог недостаточно). Боту очень тяжело всех помнить, и ты, решив ' \
    'больше не использовать его, таким образом облегчишь ему работу.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    '{} Можешь <b>оценить</b> бота по четырехбалльной шкале (как в универе. ' \
    'От "неуд" до "отлично") или посмотреть <i>средний балл</i> оценок ' \
    'других пользователей.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    '{} Для того, чтобы <i>скрыть занятие</i>, необходимо:\n' \
    '   1. Выбрать день, когда есть это занятие;\n' \
    '   2. Выбрать нужное занятие;\n' \
    '   3. Определиться со временем, когда скрывать занятие.\n' \
    '{} Занятие можно <i>скрыть</i>:\n' \
    '   1. В определенное время в определенный день недели (например, есть ' \
    'две пары английского в субботу, первая и вторая. Этим вариантом можно ' \
    'скрыть, допустим, только первую);\n' \
    '   2. В любое время в определенный день недели (то есть весь английский' \
    ' в этот день);\n' \
    '   3. В любой день (весь свой английский абсолютно {}).\n' \
    'P.S. Любые совпадения случайны, английский выбран как предмет, который ' \
    'есть почти у всех.\n' \
    '{} Вернуть можно как определенное занятие, так и все отмененные.\n' \
    '{} Для того, чтобы не запутаться в отмененных занятиях, перед каждым ' \
    'названием добавлен <i>id</i>.\n' \
    '{} В настройках адреса:\n' \
    '   Полный - отображаться будет адрес целиком, как на сайте ' \
    '(Университетский просп., д. 35, корп. Д, 204Д)\n' \
    '   Аудитория - отображаться будет только аудитория (204Д)\n\n' \
    '<b>Раздел "{}"</b>\n' \
    '{} Данные предоставлены сервисом <a href="http://rasp.yandex.ru/">' \
    'Яндекс.Расписания</a>.\n' \
    '{} В меню доступно два направления: из Университета и в Университет.\n' \
    '{} После выбора направления будет показана информация по <b>3 ' \
    'ближайшим</b> электричкам, а именно: Через сколько отправление, ' \
    'Время отправления и Время прибытия\n' \
    '{} После этого есть возможность просмотра <i>всех оставшихся</i> на ' \
    'сегодня электричек.\n' \
    '{} Если по выбранному маршруту на сегодня электричек <i>нет</i>, то ' \
    'бот пришлет расписание <i>первых 5</i> электричек на завтра.\n' \
    '{} Можно выбрать свой маршрут (пока только в направлении Ораниенбаума ' \
    'и обратно).'.format(emoji["bullet"], emoji["bullet"], emoji["bullet"],
                         emoji["bullet"], emoji["bullet"], emoji["calendar"],
                         emoji["bullet"], emoji["alarm_clock"],
                         emoji["settings"], emoji["bullet"], emoji["bullet"],
                         emoji["bullet"], emoji["star"], emoji["bullet"],
                         emoji["editor"], emoji["bullet"], emoji["bullet"],
                         emoji["horns"], emoji["bullet"], emoji["bullet"],
                         emoji["bullet"], emoji["suburban"], emoji["bullet"],
                         emoji["bullet"], emoji["bullet"], emoji["bullet"],
                         emoji["bullet"], emoji["bullet"])

briefly_info_answer = \
    'КРАТКАЯ ИНФОРМАЦИЯ\n\n' \
    '<b>Раздел "Расписание"</b>\n' \
    'Здесь ты можешь <i>узнать расписание</i> на любой день, а также ' \
    '<i>подписаться на рассылку</i>.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    'Здесь ты можешь <i>сменить группу</i> или <i>завершить работу</i> с ' \
    'ботом.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    'Здесь ты можешь <i>оценить бота</i> и посмотреть <i>средний балл</i> ' \
    'оценок пользователей.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    'Здесь ты можешь <i>скрыть</i> или <i>вернуть</i> занятие в расписании, ' \
    'а также настроить <i>отображение адреса</i>.\n\n' \
    '<b>Раздел "{}"</b>\n' \
    'Здесь ты можешь посмотреть <i>электрички</i> от или до Университета. ' \
    'Также есть возможность проложить <i>свой маршрут</i>.'.format(
        emoji["settings"], emoji["star"], emoji["editor"], emoji["suburban"])
