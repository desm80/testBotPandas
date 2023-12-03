import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from datetime import datetime
from dotenv import load_dotenv
from io import BytesIO
import pandas as pd
from pathlib import Path

import constants
from src.db import create_link

load_dotenv()
router = Router()

TOKEN = os.getenv("TOKEN")
BASE_DIR = Path(__file__).parent

WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 5000
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret"
BASE_WEBHOOK_URL = "https://aiogram.dev/"


class UploadFile(StatesGroup):
    waiting_for_file = State()
    processing_file = State()


@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    try:
        await message.bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        pass
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Загрузить файл",
        callback_data=constants.UPLOAD_FILE
        )
    )
    await message.answer(
        "Нажмите на кнопку для загрузки файла",
        reply_markup=builder.as_markup()
    )
    await state.set_state(UploadFile.waiting_for_file)


@router.callback_query(F.data == constants.UPLOAD_FILE, UploadFile.waiting_for_file)
async def upload_file(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте пожалуйста файл с данными")
    await state.set_state(UploadFile.processing_file)
    await callback.answer()


@router.message(F.document, UploadFile.processing_file)
async def processing_file(message: types.Message, state: FSMContext):
    await message.answer("Обрабатываем файл")
    if not message.document.file_name.endswith(".xlsx"):
        await message.answer("Отправлен не excel файл, отправьте правильный документ")
    else:
        document = message.document
        file = await message.bot.download(document)
        try:
            directory = BASE_DIR / 'document'
            os.makedirs(directory, exist_ok=True)
            filename = f'testfile-{datetime.now().strftime("%d-%m-%Y %H-%M-%S")}.xlsx'
            filepath = os.path.join(directory, filename)
            with open(filepath, 'wb') as f:
                f.write(file.getvalue())
        except Exception as e:
            await message.answer(f"Произошла ошибка при сохранении файла: {str(e)}")
        df = pd.read_excel(file)
        rows, cols = df.shape
        for i in range(rows):
            result = []
            for j in range(cols):
                result.append(df.iloc[i, j])
            if create_link(result):
                await message.answer(
                    f"Вы отправили следующие данные\ntitle -  {result[0]}\nurl - {result[1]}\nxpath - {result[2]}"
                    f"\nОни успешно добавлены в базу данных")
            else:
                await message.answer(f"Вы предоставили некорректные данные. Исправьте их и попробуйте еще раз!")

        await state.clear()


async def main():
    bot = Bot(TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot, drop_pending_updates=True)


# async def on_startup():
#     await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)

# async def on_shutdown():
#     await bot.delete_webhook()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен по команде Ctrl+C")

    # dp = Dispatcher()
    # dp.include_router(router)
    # dp.startup.register(on_startup)
    # dp.shutdown.register(on_shutdown)
    # bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # app = web.Application()
    # webhook_requests_handler = SimpleRequestHandler(
    #     dispatcher=dp,
    #     bot=bot,
    #     secret_token=WEBHOOK_SECRET,
    # )
    # webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    # setup_application(app, dp, bot=bot)
    # web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
