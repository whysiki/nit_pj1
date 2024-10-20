# encoding: utf-8
from bs4 import BeautifulSoup
import aiohttp
from rich import print
import http.cookies
from dotenv import load_dotenv
import os

load_dotenv(".env")

USER_NAME = os.getenv("USER_NAME")
PASSWORD = os.getenv("PASSWORD")
assert (
    USER_NAME and PASSWORD and isinstance(USER_NAME, str) and isinstance(PASSWORD, str)
), "USER_NAME and PASSWORD must be set in .env file.Format: \nUSER_NAME=your_username\nPASSWORD=your_password"


# get execution in login page
async def get_execution() -> str:
    url = r"https://eapp2.nit.edu.cn:9443/cas/login?service=http%3A%2F%2Fportal.nit.edu.cn%2Fcas%2Flogin_portal"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "max-age=0",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            execution = soup.select_one(
                '#login_content > span.landing_btn_bg > input[type="hidden"][name="execution"]'
            )
            value = execution["value"]
            return value


# get PORTAL_TOKEN cookie
async def get_PORTAL_TOKEN_cookie() -> dict:
    url = "https://eapp2.nit.edu.cn:9443/cas/login"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Content-Type": "application/x-www-form-urlencoded",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "Referrer": "https://eapp2.nit.edu.cn:9443/cas/login?service=http%3A%2F%2Fportal.nit.edu.cn%2Fcas%2Flogin_portal",
    }

    body = {
        "username": USER_NAME,
        "password": PASSWORD,
        "execution": await get_execution(),
        "_eventId": "submit",
        "geolocation": "",
        "submit": "��¼",
    }

    async with aiohttp.ClientSession() as session:

        async with session.post(
            url, headers=headers, data=body, allow_redirects=True
        ) as response:
            cookies: http.cookies.SimpleCookie = response.cookies
            cookies_text = cookies.get("PORTAL_TOKEN").value
            PORTAL_TOKEN_cookie = {"PORTAL_TOKEN": cookies_text}
            JSESSIONID_1 = response.history[0].cookies.get("JSESSIONID").value
            TGC = response.history[0].cookies.get("TGC").value
            PORTAL_TOKEN_cookie.update({"JSESSIONID": JSESSIONID_1, "TGC": TGC})
            return PORTAL_TOKEN_cookie


# get bzb_njw and bzb_jsxsd cookies
async def get_bzb_njw_bzb_jsxsd_cookies() -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "Priority": "u=0, i",
        "referrer": "http://portal.nit.edu.cn/",
    }
    url = "http://jiaowu.nit.edu.cn/sso.jsp"
    url2 = "https://eapp2.nit.edu.cn:9443/cas/login?service=http%3A%2F%2Fjiaowu.nit.edu.cn%2Fsso.jsp"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            cookies_njw: http.cookies.SimpleCookie = response.cookies
            cookies_njw_text: str = cookies_njw.get("bzb_njw").value
            headers2 = headers.copy()
            headers2.update({"referrer": "http://jiaowu.nit.edu.cn/"})
            Portal_cookies_dict = await get_PORTAL_TOKEN_cookie()
            headers2.update(
                {
                    "Cookie": f"TGC={Portal_cookies_dict["TGC"]}; JSESSIONID={Portal_cookies_dict["JSESSIONID"]}; randomBgIndex=0"
                }
            )
            async with session.get(url2, headers=headers2, allow_redirects=True) as re2:
                bzb_jsxsd_with_equal_text = (
                    re2.history[-1].headers.get("Set-Cookie").split(";")[0]
                )
                cookies_str = f"bzb_njw={cookies_njw_text};{bzb_jsxsd_with_equal_text}"
                return cookies_str


# get final jwt auth url
async def fetch_pj_url(jwt_auth_url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "Priority": "u=0, i",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(jwt_auth_url, headers=headers) as response:
            if response.status == 200:
                final_url = str(response.url)
                return final_url
            else:
                print("Error:", response.status)
                return None


# get jwt
async def get_jwt(menu: str = "jwxsjdp") -> str:
    str_url = "http://jiaowu.nit.edu.cn:8080/jsxsd/qzzlpt/getToken_11319"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "text/plain, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "http://jiaowu.nit.edu.cn:8080",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Referer": "http://jiaowu.nit.edu.cn:8080/jsxsd/framework/xsMainV.htmlx",
        "Cookie": await get_bzb_njw_bzb_jsxsd_cookies(),
        "Content-Length": "0",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(str_url, headers=headers) as response:
            data_str = await response.text()
            jwt_auth_url = f"{data_str}/{menu}"
    final_url = await fetch_pj_url(jwt_auth_url)
    print(f"final_url: {final_url}")
    jwt = final_url.split("xlgToken=")[-1]
    return jwt


async def construct_cookie() -> list[dict]:

    print("This function is unsuccesfully tested, please test it manually.")

    return None

    PORTAL_TOKEN_dict = await get_PORTAL_TOKEN_cookie()
    # JSESSIONID = PORTAL_TOKEN_dict["JSESSIONID"]
    PORTAL_TOKEN = PORTAL_TOKEN_dict["PORTAL_TOKEN"]
    TGC = PORTAL_TOKEN_dict["TGC"]
    bzb_njw_bzb_jsxsd_cookies_str = await get_bzb_njw_bzb_jsxsd_cookies()

    bzb_njw = bzb_njw_bzb_jsxsd_cookies_str.split(";")[0]
    bzb_jsxsd = bzb_njw_bzb_jsxsd_cookies_str.split(";")[1]

    cookie_dict_list = [
        {
            "name": "JSESSIONID",
            "value": "BE151D805F3CF58AD6ED41480D0794CB",
            "domain": "www.nit.edu.cn",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": False,
            "sameSite": "Lax",
        },
        {
            "name": "JSESSIONID",
            "value": "2f097871-e9ec-40ad-8f99-604240554dd1",
            "domain": "portal.nit.edu.cn",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": False,
            "sameSite": "Lax",
        },
        {
            "name": "routeportal",
            "value": "548d04fcc76dab117e1bf9f71dbe495a",
            "domain": "portal.nit.edu.cn",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": False,
            "sameSite": "None",
        },
        {
            "name": "JSESSIONID",
            "value": "DAD27B3386CC4D652A6C5F29AF8A16D7",
            "domain": "eapp2.nit.edu.cn",
            "path": "/cas",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None",
        },
        {
            "name": "randomBgIndex",
            "value": "0",
            "domain": "eapp2.nit.edu.cn",
            "path": "/",
            "expires": 1731825276,
            "httpOnly": False,
            "secure": False,
            "sameSite": "None",
        },
        {
            "name": "TGC",
            "value": TGC,
            "domain": "eapp2.nit.edu.cn",
            "path": "/cas/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "None",
        },
        {
            "name": "PORTAL_TOKEN",
            "value": PORTAL_TOKEN,
            "domain": "portal.nit.edu.cn",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": False,
            "sameSite": "None",
        },
        {
            "name": "bzb_njw",
            "value": bzb_njw,
            "domain": "jiaowu.nit.edu.cn",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": False,
            "sameSite": "None",
        },
        {
            "name": "bzb_jsxsd",
            "value": bzb_jsxsd,
            "domain": "jiaowu.nit.edu.cn",
            "path": "/jsxsd",
            "expires": -1,
            "httpOnly": True,
            "secure": False,
            "sameSite": "None",
        },
    ]
    return cookie_dict_list
