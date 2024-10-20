from playwright.async_api import async_playwright
from playwright.async_api import Page, BrowserContext, Browser
from dotenv import load_dotenv
import os
import urllib
import random
from functools import wraps
import asyncio
from rich import print

from playwright_stealth import stealth_async

# from undetected_chromedriver import Chrome, ChromeOptions

# Load environment variables
load_dotenv(".env")


# Get credentials from environment variables
USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")
assert (
    USER_NAME and PASSWORD and isinstance(USER_NAME, str) and isinstance(PASSWORD, str)
), "USER_NAME and PASSWORD must be set in .env file. Format: \nUSER_NAME=your_username\nPASSWORD=your_password"


def unquote_urlparams(urlparams: str) -> dict:
    urlparams = urllib.parse.unquote(urlparams)
    urlparams = urlparams.split("?")[1].split("&")
    return {
        param.split("=")[0]: (param.split("=")[1] if len(param.split("=")) > 1 else "")
        for param in urlparams
    }


def retry_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        for i in range(3):
            try:
                await func(*args, **kwargs)
                break
            except Exception as e:
                print(f"[red]Attempt {i+1} failed: {type(e).__name__}: {str(e)}[/red]")
                continue

    return wrapper


# @retry_decorator
async def run_single(single_url: str, page: Page) -> None:
    print(f"Evaluating: {single_url}")

    url_params = unquote_urlparams(single_url)
    # print(url_params)
    kcmc = url_params["kcmc"]  # 课程名称
    jgxm = url_params["jgxm"]  # 教工姓名
    xnxqid = url_params["xnxqid"]  # 学年学期ID
    print(f"学年学期ID: {xnxqid},课程名称: {kcmc}, 教工姓名: {jgxm}")
    current_referer = page.url
    print(current_referer)
    # await page.goto(single_url, referer=current_referer)
    # 打开窗口
    await page.evaluate(f"window.open('{single_url}')")
    await page.wait_for_selector("tr.el-table__row")

    message_box = await page.query_selector("div.el-message-box__btns")
    if message_box:
        rows = await page.query_selector_all("tr.el-table__row")
        for row in rows:
            labels = await row.query_selector_all("label[role='radio']")
            random_label = labels[random.randint(0, 1)]
            input_span = await random_label.query_selector("span.el-radio__label")
            await random_label.click()
            print(await input_span.inner_text())
        await page.locator("textarea").click()
        await page.locator("textarea").fill("好")
        await page.get_by_role("button", name="确认").click()
        await page.wait_for_selector("div.el-message-box__btns")
        await page.wait_for_selector("button")
        buttons = await message_box.query_selector_all("button")
        for button in buttons:
            if await button.inner_text() == "确定":
                await button.click()
                await page.wait_for_timeout(1000)
        print(
            f"[green]学年学期ID: {xnxqid}, 课程名称: {kcmc}, 教工姓名: {jgxm} Already evaluated[/green]"
        )
    else:
        print(
            f"[yellow]学年学期ID: {xnxqid}, 课程名称: {kcmc}, 教工姓名: {jgxm} Already evaluated[/yellow]"
        )


async def pj_urls(single_urls: list, headless: bool) -> None:
    # save-browser-state
    state_path = "cache/brower_state.json"
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    async with async_playwright() as playwright:
        browser: Browser = await playwright.firefox.launch(headless=headless)
        async with browser:
            # if not os.path.exists(state_path):
            if True:
                context: BrowserContext = await browser.new_context()
                page1: Page = await context.new_page()
                if headless:
                    await stealth_async(page1)
                await page1.goto(
                    "http://portal.nit.edu.cn/index#/app/home/main",
                    wait_until="domcontentloaded",
                )
                await page1.wait_for_selector("input[placeholder='Username']")
                await page1.get_by_placeholder("Username").fill(USER_NAME)
                await page1.get_by_placeholder("Password").fill(PASSWORD)
                await page1.get_by_role("button", name="LOGIN").click()
                async with page1.expect_popup(timeout=600000) as page2_info:
                    await page1.get_by_text("教务管理系统").click()
                page2 = await page2_info.value
                async with page2.expect_popup(timeout=600000) as page3_info:
                    await page2.wait_for_selector("div.menu-one-label")
                    await page2.locator("div.menu-one-label").filter(
                        has_text="学生评教"
                    ).click(click_count=2, delay=1000)
                page3 = await page3_info.value
                await page3.get_by_text("阶段评价").click()
                await page3.wait_for_selector(
                    "td.el-table_1_column_9.is-center.el-table__cell > div > button"
                )
                button = await page3.query_selector(
                    "td.el-table_1_column_9.is-center.el-table__cell > div > button"
                )
                await button.click()
                await context.storage_state(path=state_path)
            else:
                pass
                # context: BrowserContext = await browser.new_context(
                #     storage_state=state_path
                # )
                # page3: Page = await context.new_page()
            async with context:
                await asyncio.gather(*[run_single(url, page3) for url in single_urls])
