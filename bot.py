import os
import logging
from datetime import datetime, timedelta
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import asyncio


logging.basicConfig(level=logging.INFO)

API_TOKEN = '7769527498:AAEfo583wUtMWnNl6L8F6eGdp_LN6ANjfRk'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('water_reminder.db', check_same_thread=False)
        self.create_table()

    def create_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    water_amount INTEGER,
                    frequency INTEGER,
                    last_reminder TIMESTAMP
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка создания таблицы: {e}")

    def add_user(self, user_id, water_amount, frequency):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, water_amount, frequency, last_reminder)
                VALUES (?, ?, ?, ?)
            ''', (user_id, water_amount, frequency, datetime.now()))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка добавления пользователя: {e}")

    def get_user(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения пользователя: {e}")
            return None

    def update_last_reminder(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_reminder = ? 
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Ошибка обновления последнего напоминания: {e}")

    def close(self):
        self.conn.close()


db = Database()


class WaterStates(StatesGroup):
    water_amount = State()
    frequency = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я буду напоминать тебе пить воду.\n"
                         "Сколько миллилитров воды ты хочешь выпивать за раз?")
    await WaterStates.water_amount.set()


@dp.message_handler(state=WaterStates.water_amount)
async def process_water_amount(message: types.Message, state: FSMContext):
    try:
        water = int(message.text)
        if water <= 0:
            raise ValueError
        await state.update_data(water=water)
        await message.answer("Отлично! Теперь укажи периодичность напоминаний в часах:")
        await WaterStates.frequency.set()
    except ValueError:
        await message.answer("Пожалуйста, введите целое положительное число!")


@dp.message_handler(state=WaterStates.frequency)
async def process_frequency(message: types.Message, state: FSMContext):
    try:
        frequency = int(message.text)
        if frequency <= 0:
            raise ValueError
        data = await state.get_data()
        db.add_user(message.from_user.id, data['water'], frequency)
        await message.answer(
            f"Настройки сохранены! Я буду напоминать тебе пить {data['water']} мл воды каждые {frequency} часов 🚰")
        await state.finish()
    except ValueError:
        await message.answer("Пожалуйста, введите целое положительное число!")




async def reminder_check():
    while True:
        try:
            cursor = db.conn.cursor()
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()

            for user in users:
                user_id = user[0]
                last_reminder = datetime.fromisoformat(user[3])
                frequency_hours = user[2]

                if datetime.now() - last_reminder > timedelta(hours=frequency_hours):
                    await bot.send_message(
                        user_id,
                        f"⏰ Время пить воду! Выпей {user[1]} мл воды 💧"
                    )
                    await bot.send_sticker(user_id, 'CAACAgIAAxkBAAENCqNnwq_KJJSuBnPX2UeuwL9NsRO15wACPm4AAp_OEUq2lnYyihU8RTYE')
                    db.update_last_reminder(user_id)

        except Exception as e:
            logging.error(f"Ошибка в reminder_check: {e}")

        await asyncio.sleep(60)

async def on_startup(dp):
    asyncio.create_task(reminder_check())


if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    finally:
        db.close()
