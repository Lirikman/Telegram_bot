from questions import quiz_data
from base_db import create_table, update_quiz_index, get_quiz_index, get_right_answer, get_wrong_answer, get_rating_users
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram import F

# Включим логирование
logging.basicConfig(level=logging.INFO)

API_TOKEN = 'YOUR_TOKEN'

# Создаём объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

def generate_options_keyboard(answer_options, right_answer):
  # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()

    # В цикле создаем 4 Inline кнопки, а точнее Callback-кнопки
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            # Текст на кнопках соответствует вариантам ответов
            text=option,
            # Присваиваем данные для колбэк запроса.
            # Если ответ верный сформируется колбэк-запрос с данными 'right_answer'
            # Если ответ неверный сформируется колбэк-запрос с данными 'wrong_answer'
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("Верно!")

    # Получение текущего количества верных и не верных ответов для данного пользователя
    current_right_answer = await get_right_answer(callback.from_user.id)
    current_wrong_answer = await get_wrong_answer(callback.from_user.id)

    # Обновление номера текущего вопроса и количества правильных ответов в БД
    current_right_answer += 1
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, callback.from_user.username, current_question_index, current_right_answer, current_wrong_answer)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_option = quiz_data[current_question_index]['correct_option']

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Получение текущего количества верных и не верных ответов для данного пользователя
    current_right_answer = await get_right_answer(callback.from_user.id)
    current_wrong_answer = await get_wrong_answer(callback.from_user.id)

    # Обновление номера текущего вопроса и количества неправильных ответов в базе данных
    current_wrong_answer += 1
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, callback.from_user.username, current_question_index, current_right_answer, current_wrong_answer)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик две кнопки
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))
    # Прикрепляем кнопки к сообщению
    await message.answer('Добро пожаловать в литературный квиз!', reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команды /rating
@dp.message(F.text=="Статистика")
@dp.message(Command("rating"))
async def cmd_rating(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Статистика"))
    # Прикрепляем кнопки к сообщению
    result = await get_rating_users()
    await message.answer(f'<b>Рейтинг игроков!</b>\n{result}',
                         parse_mode=ParseMode.HTML
                         )


# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    # Запускаем новый квиз
    await new_quiz(message)


# Сопрограмма запуска нового квиза
async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # получаем имя пользователя
    user_name = message.from_user.username
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    # сбрасываем текущие значения счётчиков верных и не верных ответов на 0
    current_right_answer = 0
    current_wrong_answer = 0
    await update_quiz_index(user_id, user_name, current_question_index, current_right_answer, current_wrong_answer)
    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)


# Сопрограмма получения нового вопроса
async def get_question(message, user_id):
    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


# Запуск главной сопрограммы
async def main():
    # Запуск создания таблиц базы данных
    await create_table()
    # Запуск процесса поллинга новыйх апдейтов
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
