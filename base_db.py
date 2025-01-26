import aiosqlite

# Зададим имя базы данных
DB_NAME = 'quiz_bot.db'

# Сопрограмма создания БД
async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, user_name VARCHAR(100), question_index INTEGER, right_answer INTEGER, wrong_answer INTEGER)''')
        # Сохраняем изменения
        await db.commit()


# Сопрограмма добавления нового пользователя и сохранения состояния в БД
async def update_quiz_index(user_id, user_name, index, count_right_answer, count_wrong_answer):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, user_name, question_index, right_answer, wrong_answer) VALUES (?, ?, ?, ?, ?)', (user_id, user_name, index, count_right_answer, count_wrong_answer))
        # Сохраняем изменения
        await db.commit()


# Сопрограмма получения состояния пользователя из БД 
async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0
            

# Сопрограмма получения количества верных ответов для пользователя из БД
async def get_right_answer(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT right_answer FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


# Сопрограмма получения количества не верных ответов для пользователя из БД 
async def get_wrong_answer(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT wrong_answer FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0
            

# Сопрограмма получения количества верных и не верных ответов для всех пользователей из БД
async def get_rating_users():
    # Подключаемся к базе данных
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_name, right_answer, wrong_answer FROM quiz_state ORDER BY right_answer') as cursor:
            # Возвращаем результат
            results = await cursor.fetchall()
            text = []
            for row in results:
                text.append(list(row))
            text_str = ''
            for i in text:
                text_str = f'Имя пользователя: <i>{i[0]}</i>\nПравильные ответы: <i>{i[1]}</i>\nНеправильные ответы: <i>{i[2]}</i>\n\n'
            if results is not None:
                return text_str
            else:
                return 'Рейтинг игроков пуст!'