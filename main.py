import asyncio
import logging
import os
import re
from datetime import datetime, time

# Сторонние библиотеки (только нужные)
from playwright.async_api import async_playwright
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject 
from aiogram.types import FSInputFile, LinkPreviewOptions
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- 1. НАСТРОЙКА ЛОГОВ ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# --- 2. ПОДКЛЮЧЕНИЕ НАСТРОЕК ---
try:
    import config
    logging.info("--- КОНФИГ ЗАГРУЖЕН УСПЕШНО ---")
except Exception as e:
    logging.error(f"ОШИБКА В CONFIG.PY: {e}")
    exit()

# Константы путей
DIARY_URL = 'https://sgo1.edu71.ru/app/school/studentdiary/'
USER_DATA_DIR = "./user_data"
DOWNLOAD_PATH = "./downloads"
HW_STATE_FILE = "homework_state.txt" 
current_screenshot = "diary_current.png"

if not os.path.exists(DOWNLOAD_PATH): os.makedirs(DOWNLOAD_PATH)

bot = Bot(token=config.TOKEN)
dp = Dispatcher()

# --- 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_time_status():
    """Оригинальная функция расчета времени"""
    now = datetime.now()
    day = now.weekday()
    if day == 6: return "🎉 Сегодня воскресенье! Уроков нет."
    today_lessons = config.WEEK_SCHEDULE.get(day, {})
    curr = now.time()
    for i, l_t in enumerate(config.LESSONS):
        l_start = time(*map(int, l_t['start'].split(':')))
        l_end = time(*map(int, l_t['end'].split(':')))
        if l_start <= curr <= l_end:
            c_s = today_lessons.get(l_t['num'], {"name": "Неизвестно", "room": "?"})
            rem = (datetime.combine(now.date(), l_end) - now).seconds // 60
            res = f"📖 Урок {l_t['num']}: {c_s['name']}\n🔔 До конца: {rem} мин."
            n_s = today_lessons.get(l_t['num'] + 1)
            if n_s: res += f"\n\n➡️ Далее: {n_s['name']} (каб. {n_s['room']})"
            return res
        if i < len(config.LESSONS) - 1:
            nxt_t = config.LESSONS[i+1]
            n_start = time(*map(int, nxt_t['start'].split(':')))
            if l_end < curr < n_start:
                n_s = today_lessons.get(nxt_t['num'], {"name": "Неизвестно", "room": "?"})
                rem = (datetime.combine(now.date(), n_start) - now).seconds // 60
                return f"☕ Перемена.\n⏳ Через {rem} мин. урок {nxt_t['num']}: {n_s['name']} (каб. {n_s['room']})"
    return "🎉 Уроки на сегодня закончились!"

async def get_to_correct_week(page, target_date):
    for _ in range(10):
        try:
            header = await page.locator("div, h2, span").filter(has_text="202").inner_text()
            found = re.findall(r"(\d{1,2}\.\d{1,2}\.\d{2,4})", header)
            if len(found) >= 2:
                s_w = datetime.strptime(found[0], "%d.%m.%y" if len(found[0].split('.')[-1])==2 else "%d.%m.%Y").date()
                e_w = datetime.strptime(found[1], "%d.%m.%y" if len(found[1].split('.')[-1])==2 else "%d.%m.%Y").date()
                if s_w <= target_date <= e_w: return True
                if target_date < s_w: await page.locator("button i.fa-chevron-left").first.click()
                else: await page.locator("button i.fa-chevron-right").first.click()
                await asyncio.sleep(4)
            else: break
        except: break
    return False

# --- 4. ЯДРО БРАУЗЕРА (PLAYWRIGHT) ---

async def take_action(target_date=None, target_subject=None):
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                USER_DATA_DIR, headless=True, viewport={'width':1920,'height':1200}
            )
            page = context.pages[0]
            await page.goto(DIARY_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            try:
                prof = page.locator("text=Акопян Артём").first
                if await prof.is_visible(timeout=3000): await prof.click(); await asyncio.sleep(3)
                pass_f = page.locator('input[type="password"]').first
                if await pass_f.is_visible(timeout=3000):
                    await page.locator('input[type="text"], input[placeholder*="огин"]').first.fill(config.USER_LOGIN)
                    await pass_f.fill(config.USER_PASS); await page.keyboard.press("Enter"); await asyncio.sleep(10)
            except: pass

            await page.wait_for_selector("text=Дневник", timeout=20000)
            await page.locator("a, button").filter(has_text="Дневник").first.click(); await asyncio.sleep(2)
            await page.locator("a, button").filter(has_text="Дневник").last.click(); await asyncio.sleep(8)

            hw_cells = await page.locator("tr td:nth-child(4)").all_inner_texts()
            current_hw_text = "".join(hw_cells).strip()

            if target_date and target_subject:
                if not await get_to_correct_week(page, target_date): 
                    await context.close(); return "date_not_found", None, ""
                
                months_ru =["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
                date_str_ru = f"{target_date.day} {months_ru[target_date.month - 1]}"
                day_box = page.locator("div, .day").filter(has_text=date_str_ru).first
                row = day_box.locator("tr, .lesson-row").filter(has_text=re.compile(target_subject, re.I)).first
                clip = row.locator(".fa-paperclip, a[href*='attachment']").first
                
                if await clip.is_visible(timeout=5000):
                    await clip.click(); await asyncio.sleep(4)
                    files =[]
                    links = await page.locator('.v-dialog a, a[href*="download"]').all()
                    for l in links:
                        try:
                            async with page.expect_download(timeout=10000) as d_info: await l.click()
                            d = await d_info.value
                            f_p = os.path.join(DOWNLOAD_PATH, d.suggested_filename)
                            await d.save_as(f_p); files.append(f_p)
                        except: continue
                    await context.close(); return "files", files, ""
                else:
                    await context.close(); return "no_files", None, ""

            await page.screenshot(path=current_screenshot, full_page=True)
            await context.close()
            return "screenshot", current_screenshot, current_hw_text
            
        except Exception as e:
            logging.error(f"Ошибка браузера: {e}")
            return "error", None, ""

# --- 5. ЛОГИКА ОТПРАВКИ ---

async def send_logic(force_send=False, chat_id=None):
    res_type, path, current_hw_text = await take_action()
    
    if res_type == "screenshot":
        last_hw_text = ""
        if os.path.exists(HW_STATE_FILE):
            with open(HW_STATE_FILE, "r", encoding="utf-8") as f:
                last_hw_text = f.read()

        is_changed = current_hw_text != last_hw_text

        if force_send or is_changed:
            targets = [chat_id] if chat_id else config.CHAT_IDS
            for cid in targets:
                try: await bot.send_photo(chat_id=cid, photo=FSInputFile(path), caption="ДЗ")
                except: pass
            
            if not chat_id: 
                with open(HW_STATE_FILE, "w", encoding="utf-8") as f:
                    f.write(current_hw_text)
                logging.info("База ДЗ обновлена.")
        else:
            logging.info("Изменений в ДЗ нет. Пропускаю.")

# --- 6. КОМАНДЫ БОТА ---

last_dz_time = None 

@dp.message(Command("dz"))
async def cmd_dz(m: types.Message):
    if m.chat.id not in config.CHAT_IDS:
        return await m.answer("❌ У вас нет доступа к этому боту.")

    global last_dz_time
    now = datetime.now()
    if last_dz_time:
        diff = (now - last_dz_time).total_seconds()
        if diff < 600:
            left_seconds = int(600 - diff)
            mins = left_seconds // 60
            secs = left_seconds % 60
            return await m.answer(f"⏳ Не так часто! Команду можно использовать раз в 10 минут.\nОсталось ждать: {mins} мин {secs} сек.")
            
    last_dz_time = now
    await m.answer("⌛ Делаю свежий скриншот...")
    await send_logic(force_send=True, chat_id=m.chat.id)

@dp.message(Command("time"))
async def cmd_time(m: types.Message):
    await m.answer(get_time_status())

@dp.message(Command("all"))
async def cmd_all(message: types.Message, command: CommandObject):
    if message.chat.id not in config.CHAT_IDS:
        return
        
    ann = command.args if command.args else "@all"
    await message.answer(ann)
    chunks = [config.STUDENTS_DATA[i:i + 7] for i in range(0, len(config.STUDENTS_DATA), 7)]
    for chunk in chunks:
        tags = " ".join([f'<a href="https://t.me/{u[1:]}">{u}</a>' if u.startswith("@") else f'<a href="{u}">Ученик</a>' for u in chunk])
        try: 
            await message.answer(tags, parse_mode="HTML", link_preview_options=LinkPreviewOptions(is_disabled=True))
            await asyncio.sleep(0.8)
        except: pass
    try: await message.delete()
    except: pass

@dp.message(Command("fail"))
async def cmd_fail(m: types.Message, command: CommandObject):
    if m.chat.id not in config.CHAT_IDS:
        return
        
    if not command.args or " " not in command.args:
        return await m.answer("Используй: `/fail 03.02 Алгебра`", parse_mode="Markdown")
    try:
        parts = command.args.split(" ", 1)
        target_date = datetime(datetime.now().year, int(parts[0].split(".")[1]), int(parts[0].split(".")[0])).date()
        await m.answer(f"🔎 Ищу файлы по предмету **{parts[1]}** за {parts[0]}...", parse_mode="Markdown")
        res, data, _ = await take_action(target_date, parts[1])
        if res == "files":
            for f in data:
                await m.answer_document(document=FSInputFile(f), caption=f"📎 {parts[1]} ({parts[0]})")
                if os.path.exists(f): os.remove(f)
        elif res == "no_files": await m.answer("📎 Вложений (скрепок) не найдено.")
        elif res == "date_not_found": await m.answer("❌ Дата не найдена в архиве дневника.")
        else: await m.answer("🤷 Предмет не найден или произошла ошибка.")
    except Exception as e: await m.answer(f"❌ Ошибка: {e}")

# --- 7. ЗАПУСК ---

async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_logic, 'cron', hour='9-22', minute=5, args=[False])
    scheduler.add_job(send_logic, 'cron', hour='12,17,21', minute=0, args=[True])
    
    scheduler.start()
    logging.info("Бот запущен! Команды: /dz, /time, /all, /fail")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")