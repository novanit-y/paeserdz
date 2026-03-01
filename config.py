

# Токен бота (получен от @BotFather)
TOKEN = 'YOUR_BOT_TOKEN_HERE'

# ID чатов (личный и группы)
CHAT_IDS = [000000000, -1000000000000]

# Данные для входа в СГО
USER_LOGIN = 'YOUR_LOGIN'
USER_PASS = 'YOUR_PASSWORD'

# Расписание звонков
LESSONS = [
    {"num": 1, "start": "08:30", "end": "09:10"},
    {"num": 2, "start": "09:20", "end": "10:00"},
    {"num": 3, "start": "10:10", "end": "10:50"},
    {"num": 4, "start": "11:00", "end": "11:40"},
    {"num": 5, "start": "12:00", "end": "12:40"},
    {"num": 6, "start": "13:00", "end": "13:40"},
    {"num": 7, "start": "13:50", "end": "14:30"},
    {"num": 8, "start": "14:40", "end": "15:20"},
]

# Расписание уроков 
WEEK_SCHEDULE = {
    0: { 1: {"name": "Урок 1", "room": "101"}, 2: {"name": "Урок 2", "room": "102"} },
    1: { 1: {"name": "Урок 1", "room": "101"}, 2: {"name": "Урок 2", "room": "102"} },
    2: { 1: {"name": "Урок 1", "room": "101"}, 2: {"name": "Урок 2", "room": "102"} },
    3: { 1: {"name": "Урок 1", "room": "101"}, 2: {"name": "Урок 2", "room": "102"} },
    4: { 1: {"name": "Урок 1", "room": "101"}, 2: {"name": "Урок 2", "room": "102"} },
    5: { 1: {"name": "Урок 1", "room": "101"}, 2: {"name": "Урок 2", "room": "102"} }
}

# Список студентов для команды /all 
STUDENTS_DATA = [
    "@student_nick1", "@student_nick2", "tg://user?id=00000000"
]