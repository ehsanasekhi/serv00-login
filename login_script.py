import json
import asyncio
from pyppeteer import launch
from datetime import datetime, timedelta
import aiofiles
import random
import requests
import os

# 从环境变量中获取 Telegram Bot Token 和 Chat ID
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def format_to_iso(date):
    return date.strftime('%Y-%m-%d %H:%M:%S')

async def delay_time(ms):
    await asyncio.sleep(ms / 1000)

# 全局浏览器实例
browser = None

# telegram消息
message = ""

async def login(username, password, panel):
    global browser

    page = None  # 确保 page 在任何情况下都被定义
    serviceName = 'ct8' if 'ct8' in panel else 'serv00'
    try:
        if not browser:
            browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])

        page = await browser.newPage()
        url = f'https://{panel}/login/?next=/'
        await page.goto(url)

        username_input = await page.querySelector('#id_username')
        if username_input:
            await page.evaluate('''(input) => input.value = ""''', username_input)

        await page.type('#id_username', username)
        await page.type('#id_password', password)

        login_button = await page.querySelector('#submit')
        if login_button:
            await login_button.click()
        else:
            raise Exception('Unable to find the login button')

        await page.waitForNavigation()

        is_logged_in = await page.evaluate('''() => {
            const logoutButton = document.querySelector('a[href="/logout/"]');
            return logoutButton !== null;
        }''')

        return is_logged_in

    except Exception as e:
        print(f'{serviceName}account {username} Error logging in: {e}')
        return False

    finally:
        if page:
            await page.close()
# 显式的浏览器关闭函数
async def shutdown_browser():
    global browser
    if browser:
        await browser.close()
        browser = None

async def main():
    global message

    try:
        async with aiofiles.open('accounts.json', mode='r', encoding='utf-8') as f:
            accounts_json = await f.read()
        accounts = json.loads(accounts_json)
    except Exception as e:
        print(f'Error reading accounts.json file: {e}')
        return

    for account in accounts:
        username = account['username']
        password = account['password']
        panel = account['panel']

        serviceName = 'ct8' if 'ct8' in panel else 'serv00'
        is_logged_in = await login(username, password, panel)

        now_beijing = format_to_iso(datetime.utcnow() + timedelta(hours=8))
        if is_logged_in:
            message += f"✅*{serviceName}*account *{username}* At Beijing time {now_beijing}Login panel successfully！\n\n"
            print(f"{serviceName}account {username} At Beijing time {now_beijing}Login panel successfull！")
        else:
            message += f"❌*{serviceName}*account *{username}* At Beijing time {now_beijing}Login Failed\n\n❗please check*{username}*Are the account and password correct?。\n\n"
            print(f"{serviceName}account {username} Login Failed，please check{serviceName}Are the account and password correct?。")

        delay = random.randint(1000, 8000)
        await delay_time(delay)
        
    message += f"🔚The script ends. If there is any abnormality, click the button below👇"
    await send_telegram_message(message)
    print(f'all{serviceName}Account login completed！')
    # 退出时关闭浏览器
    await shutdown_browser()

async def send_telegram_message(message):
    # 使用 Markdown 格式
    formatted_message = f"""
*🎯 serv00&ct8 automated number reservation script operation report*

🕰 *Beijing Time*: {format_to_iso(datetime.utcnow() + timedelta(hours=8))}

⏰ *UTC time*: {format_to_iso(datetime.utcnow())}

📝 *Mission Report*:

{message}

    """

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': formatted_message,
        'parse_mode': 'Markdown',  # 使用 Markdown 格式
        'reply_markup': {
            'inline_keyboard': [
                [
                    {
                        'text': 'Question Feedback❓',
                        'url': 'https://t.me/yxjsjl'  # 点击按钮后跳转到问题反馈的链接
                    }
                ]
            ]
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Failed to send message to Telegram: {response.text}")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

if __name__ == '__main__':
    asyncio.run(main())
