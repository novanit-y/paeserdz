import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Открываем браузер с ПАПКОЙ (памятью)
        context = await p.chromium.launch_persistent_context(
            "./user_data",
            headless=False, # Видимое окно
            viewport={'width': 1280, 'height': 1000}
        )
        page = context.pages[0]

        print("Перехожу на сайт...")
        await page.goto('https://sgo1.edu71.ru/app/school/studentdiary/')

        print("\nТВОЙ ВЫХОД:")
        print("1. Вводи пароль, СМС, выбирай школу.")
        print("2. Дойди до страницы, где ПРЯМО СЕЙЧАС видны оценки.")
        print("3. Как только оценки появились на экране, ничего не нажимай.")
        print("4. Вернись в это окно (VS Code) и нажми ENTER.")
        
        input() # Бот ждет твоего сигнала

        await context.close()
        print("Успех! Сессия полностью сохранена в папку user_data.")

if __name__ == "__main__":
    asyncio.run(run())