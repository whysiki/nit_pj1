from playwright.async_api import async_playwright
from playwright.async_api import Page, BrowserContext, Browser
from dotenv import load_dotenv
import os
import urllib
import random
from functools import wraps
from rich import print
import re
from playwright_stealth import stealth_async
from pathlib import Path
import asyncio
from tqdm.asyncio import tqdm as atqdm

# from undetected_chromedriver import Chrome, ChromeOptions
import json

# Load environment variables
load_dotenv(".env")


# Get credentials from environment variables
USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")
assert (
    USER_NAME and PASSWORD and isinstance(USER_NAME, str) and isinstance(PASSWORD, str)
), "USER_NAME and PASSWORD must be set in .env file. Format: \nUSER_NAME=your_username\nPASSWORD=your_password"


def unquote_urlparams(urlparams: str) -> dict:
    urlparams = urllib.parse.unquote(urlparams)  # type: ignore
    urlparams = urlparams.split("?")[1].split("&")  # type: ignore
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
    try:
        print(f"Evaluating: {single_url}")
        url_params = unquote_urlparams(single_url)
        kcmc = url_params["kcmc"]  # 课程名称
        jgxm = url_params["jgxm"]  # 教工姓名
        xnxqid = url_params["xnxqid"]  # 学年学期ID
        print(f"学年学期ID: {xnxqid},课程名称: {kcmc}, 教工姓名: {jgxm}")
        await page.evaluate(f"window.open('{single_url}')")  # 打开新标签页
        await page.wait_for_selector("div.evaluation-btns", timeout=60000)
        evaluation_buttons_container = await page.query_selector("div.evaluation-btns")
        if evaluation_buttons_container:
            await page.wait_for_selector("tr.el-table__row")
            rows = await page.query_selector_all("tr.el-table__row")
            # 设置为B的评价
            B_index = random.randint(0, len(rows) - 1)
            for index, row in enumerate(rows):
                print(
                    f"index: {index}, B_index: {B_index}, row: {(await row.inner_text()).replace(' ', '').replace('\n', '')}"
                )
                labels = await row.query_selector_all("label[role='radio']")  # ABCD
                random_label = labels[0] if index != B_index else labels[1]
                input_span = await random_label.query_selector("span.el-radio__label")
                while not await random_label.is_visible():
                    print(f"index: {index}, B_index: {B_index}, not visible")
                    await page.wait_for_timeout(1000)
                await random_label.scroll_into_view_if_needed()
                await random_label.click()
                if input_span:
                    print(await input_span.inner_text())
                else:
                    print(f"index: {index}, B_index: {B_index}, No input_span")
            await page.locator("textarea").click()
            await page.locator("textarea").fill("好")
            await page.get_by_role("button", name="确认").click()
            await page.wait_for_selector("div.el-textarea")
            await page.wait_for_selector("button")
            affirm_pop_windows = page.get_by_text("提示确认提交? 取消 确定")
            if affirm_pop_windows:
                affirm_buttons = affirm_pop_windows.locator("button", has_text="确定")
                if affirm_buttons:
                    await affirm_buttons.click()
                else:
                    raise Exception("No affirm_buttons")
            else:
                raise Exception("No affirm_pop_windows")
        else:
            raise Exception("No message_box")
    except Exception as e:
        with open("cache/error.html", "w", encoding="utf-8", errors="ignore") as f:
            f.write(await page.content())
        await page.pause()
    finally:
        pass


async def pj_urls(headless: bool) -> None:
    state_path = "cache/brower_state.json"
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    async with async_playwright() as playwright:
        browser: Browser = await playwright.chromium.launch(headless=headless)
        async with browser:
            context: BrowserContext = (
                await browser.new_context()
                if not os.path.exists(state_path)
                else await browser.new_context(storage_state=state_path)
            )
            page1: Page = await context.new_page()
            if headless:
                await stealth_async(page1)
            await page1.goto(
                "http://portal.nit.edu.cn/index#/app/home/main",
                wait_until="domcontentloaded",
            )
            if not os.path.exists(state_path):
                await page1.wait_for_selector("input[placeholder='Username']")
                await page1.get_by_placeholder("Username").fill(USER_NAME)  # type: ignore
                await page1.get_by_placeholder("Password").fill(PASSWORD)  # type: ignore
                await page1.get_by_role("button", name="LOGIN").click()
            async with page1.expect_popup(timeout=600000) as page2_info:
                await page1.get_by_text("教务管理系统").click()
            # await page1.close()
            page2 = await page2_info.value
            async with page2.expect_popup(timeout=600000) as page3_info:
                await page2.wait_for_selector("div.menu-one-label")
                await page2.locator("div.menu-one-label").filter(
                    has_text="学生评教"
                ).click(click_count=2, delay=1000)
            # await page2.close()
            page = await page3_info.value
            await page.get_by_text("阶段评价").click()
            await page.wait_for_selector(
                "td.el-table_1_column_9.is-center.el-table__cell > div > button"
            )
            buttons = await page.query_selector_all(
                "td.el-table_1_column_9.is-center.el-table__cell > div > button"
            )
            print(f"找到{len(buttons)}个课程类型")
            original_url_main = page.url
            print(f"original_url_main: {original_url_main}")
            # http://jiaowupj.nit.edu.cn/evaluate/studentEvaluate/student-jdp/index
            tasksjson: dict = json.loads(Path("tasks.json").read_text(encoding="utf-8"))
            # 关闭之前的所有page
            for page_ in context.pages:
                if page_ != page:
                    await page_.close()

            single_urls = []
            tasks = []
            for item in tasksjson.get("items", []):
                taskname = item["taskname"]
                print(f"taskname: {taskname}")
                semester = re.search(r"\d{4}-\d{4}-\d", item["taskname"])
                if semester:
                    semester = semester.group()
                else:
                    raise Exception("No semester")
                pjbuttons_url = f"http://jiaowupj.nit.edu.cn/evaluate/studentEvaluate/student-jdp/two-index?taskid={item['taskid']}&xnxq={semester}"
                print(f"pjbuttons_url: {pjbuttons_url}")
                await page.goto(pjbuttons_url)

                pjbutton_selector = "#myTableWrapper > div > div > div > table > tbody > tr > td > div > button"
                await page.wait_for_selector(pjbutton_selector)
                pjbuttons = page.locator(
                    pjbutton_selector,
                    has_not_text="查看",
                )
                pjbutton_count = await pjbuttons.count()
                print(f"找到{pjbutton_count}个课程评价按钮")
                # original_url = page.url

                if pjbutton_count:
                    for i in range(pjbutton_count):

                        async def task(i, page: Page):
                            try:
                                await page.goto(pjbuttons_url)  # 回到二级页面
                                print(f"第{i+1}个课程评价按钮")
                                pjbutton = page.locator(
                                    pjbutton_selector,
                                    has_not_text="查看",
                                )
                                if pjbutton:
                                    # 获取按钮的父级 div 元素
                                    pjbutton = pjbutton.first
                                    parent_div = pjbutton.locator(
                                        ".."
                                    )  # ".." 选择父元素
                                    parent_html = await parent_div.inner_html()
                                    print(f"父级 div HTML: {parent_html}")

                                    await parent_div.click()
                                    await page.wait_for_selector(
                                        "div.lecture-evaluation-header > h2"
                                    )
                                    nev_url = page.url
                                    print(f"nev_url: {nev_url}")
                                    # print(f"{unquote_urlparams(nev_url)}")
                                    single_urls.append(nev_url)
                                else:
                                    print("No pjbutton")
                            finally:
                                await page.close()

                        tasks.append(task(i, (await context.new_page())))
                else:
                    print("No pjbuttons")
            await atqdm.gather(*tasks)
            await context.storage_state(path=state_path)

            # 关闭所有页面
            for page_ in context.pages:
                if page_ != page:
                    await page_.close()

            # 评教
            await atqdm.gather(
                *[run_single(single_url, page) for single_url in single_urls]
            )
