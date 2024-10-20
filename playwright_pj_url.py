from playwright.sync_api import sync_playwright
from playwright.sync_api import Page, BrowserContext, Browser
from dotenv import load_dotenv
import os
import urllib
from rich import print
import random

load_dotenv(".env")

USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")
assert (
    USER_NAME and PASSWORD and isinstance(USER_NAME, str) and isinstance(PASSWORD, str)
), "USER_NAME and PASSWORD must be set in .env file.Format: \nUSER_NAME=your_username\nPASSWORD=your_password"


def unquote_urlparams(urlparams: str) -> dict:
    urlparams = urllib.parse.unquote(urlparams)
    urlparams = urlparams.split("?")[1].split("&")
    urlparams = {
        param.split("=")[0]: (param.split("=")[1] if len(param.split("=")) > 1 else "")
        for param in urlparams
    }
    return urlparams


def run_single(
    single_url: str,
    page: Page,
) -> None:

    print(f"正在评价: {single_url}")
    url_params = unquote_urlparams(single_url)
    print(url_params)
    currentreferer = page.url
    print(currentreferer)
    page.goto(single_url, referer=currentreferer)
    page.wait_for_selector("tr.el-table__row")
    rows = page.query_selector_all("tr.el-table__row")

    len_rows = len(rows)  # 评价项目

    # 设置为B的评价
    B_index = random.randint(0, len_rows - 1)

    for index, row in enumerate(rows):
        labels = row.query_selector_all("label[role='radio']")  # A B C D 选项
        random_label = labels[0] if index != B_index else labels[1]
        input_span = random_label.query_selector("span.el-radio__label")
        random_label.click()
        print(input_span.inner_text())
    page.locator("textarea").click()
    page.locator("textarea").fill("老师很好，讲课细认真，对学生也很负责")
    page.get_by_role("button", name="确认").click()
    page.wait_for_timeout(1000)
    message_box = page.query_selector("div.el-message-box__btns")
    buttons = message_box.query_selector_all("button")
    for button in buttons:
        if button.inner_text() == "确定":
            button.click()
            page.wait_for_timeout(1000)


def pj_urls(single_urls: list) -> None:

    with sync_playwright() as playwright:
        browser: Browser = playwright.firefox.launch(headless=False)
        context: BrowserContext = browser.new_context()
        page1: Page = context.new_page()
        page1.goto(
            "http://portal.nit.edu.cn/index#/app/home/main",
            wait_until="domcontentloaded",
        )
        page1.get_by_placeholder("Username").fill(USER_NAME)
        page1.get_by_placeholder("Password").fill(PASSWORD)
        page1.get_by_role("button", name="LOGIN").click()
        with page1.expect_popup(timeout=600000) as page2_info:
            page1.get_by_text("教务管理系统").click()
        page2 = page2_info.value
        with page2.expect_popup(timeout=600000) as page3_info:
            page2.get_by_text("学生评教").click()
        page3 = page3_info.value
        page3.get_by_text("阶段评价").click()
        page3.get_by_role("row", name="2 2024-2025-1").get_by_role("button").click()
        for single_url in single_urls:
            run_single(single_url=single_url, page=page3)
        context.close()
        browser.close()
