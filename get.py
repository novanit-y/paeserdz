import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Правильный запуск браузера с сохранением сессии (куки и паролей)
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=False,
            slow_mo=500,
            viewport={'width': 1280, 'height': 720}
        )
        
        # Берем первую открытую вкладку
        page = context.pages
        
        try:
            print("Пытаюсь зайти на сайт...")
            await page.goto('https://sgo1.edu71.ru/', timeout=60000)
            print("Сайт загружен. Теперь войди в аккаунт вручную.")
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
            print("Не закрывай окно, попробуй ввести адрес вручную в адресной строке.")

        # ПАУЗА: Скрипт ждет нажатия Enter в консоли VS Code
        await asyncio.get_event_loop().run_in_executor(None, input, "Нажми Enter в КОНСОЛИ, чтобы закрыть браузер и сохранить сессию...")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())