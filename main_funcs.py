# encoding: utf-8
from jwt_ import *
import urllib
import json
import asyncio
from pathlib import Path


# get user info
async def get_user_info(jwt: str) -> dict:
    url = "http://jiaowupj.nit.edu.cn/api/AuthenticationController/user/info"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Authorization": f"Bearer {jwt}",
        "Sec-GPC": "1",
        "Referer": "http://jiaowupj.nit.edu.cn/evaluate/studentEvaluate/student-jdp/index",
        "Host": "jiaowupj.nit.edu.cn",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            user_info = await response.json()
            user_info = {
                "id": user_info["id"],
                "userAccount": user_info["userAccount"],
                "userNameZh": user_info["userNameZh"],
                "userType": user_info["userType"],
            }
            return user_info


# get bj tasks
async def get_bj_tasks(
    jwt: str,
    semester: str = "2024-2025-1",
) -> dict:
    url = "http://jiaowupj.nit.edu.cn/api/TSysDdJxapController/tSysDdJxap/findJdpXqByTaskidHZ"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt}",
        "Sec-GPC": "1",
        "Priority": "u=0",
        "Referer": "http://jiaowupj.nit.edu.cn/evaluate/studentEvaluate/student-jdp/index",
    }
    body = {
        "page": {
            "conditions": "",
            "custom": {},
            "orderBy": "",
            "pageIndex": 1,
            "pageSize": 20,
            "paginationEnable": False,
        },
        "xnxq": semester,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as response:
            tasks_json = await response.json()
            return tasks_json


# get pj detailed coures , all coures
async def get_pj_detailed_coures(
    jwt: str, taskid: str, semester: str, status: str
) -> dict:
    url = "http://jiaowupj.nit.edu.cn/api/TSysDdJxapController/tSysDdJxap/findJdpXqByTaskid"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt}",
        "Sec-GPC": "1",
        "Priority": "u=0",
        "Referer": f"http://jiaowupj.nit.edu.cn/evaluate/studentEvaluate/student-jdp/two-index?taskid={taskid}&xnxq={semester}",
    }

    if status.strip() == "未评":
        issubmit = "1"
        issave = "1"
    elif status.strip() == "已评":  # 临时保存了，但是未提交
        issubmit = "1"
        issave = "0"
    elif status.strip() == "全部":
        issubmit = ""
        issave = ""

    else:

        print("[red]Error: status must be '未评' or '已评' or '全部'[/red]")

        raise ValueError("status must be '未评' or '已评' or '全部'")

    body = {
        "page": {
            "conditions": "",
            "custom": {},
            "orderBy": "",
            "pageIndex": 1,
            "pageSize": 20,
            "paginationEnable": False,
        },
        "kcmc": "",
        "jgxm": "",
        "xnxq": semester,
        "taskid": taskid,
        "issubmit": issubmit,
        "issave": issave,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as response:
            courses = await response.json()
            return courses


async def get_tasklib(course: dict, task: dict) -> dict:
    taskid = course["taskid"]
    baseurl = "http://jiaowupj.nit.edu.cn/api/TSysDdKbxxController/getTasklib"
    url = f"{baseurl}/{taskid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Authorization": f"Bearer {jwt}",
        "Sec-GPC": "1",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            course_info = await response.json()
            # print(f"getTasklib: {course_info}")
            return course_info[0]


# get pj detailed coures single
async def get_pj_detailed_coures_single(jwt: str, course: dict, task: dict) -> dict:
    assert isinstance(course, dict), "course must be a dict"

    async def get_pj_items(course: dict, tasklib: dict, task: dict) -> dict:
        base_url = "http://jiaowupj.nit.edu.cn/api/TSysDdEvalTargetController/queryEvalTargetTreeForEval"
        params = {
            "libid": tasklib["id"],
            "tkid": "",
            "taskid": course["xspjid"],
            "xnxqid": course["xnxqid"],
            "type": "student_jdp",
            "jxapid": "",
            "jg0101id": "",
            "libtaskid": course["taskid"],
            "kkdwid": "",
            "kclbcode": "",
        }
        url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Authorization": f"Bearer {jwt}",
            "Sec-GPC": "1",
            "Host": "jiaowupj.nit.edu.cn",
            "Origin": "http://jiaowupj.nit.edu.cn",
            "Connection": "keep-alive",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                items = await response.json()
                return items

    tasklib: dict = await get_tasklib(course, task)
    pj_items: dict = await get_pj_items(course, tasklib, task)
    return pj_items


async def pj_upload(jwt: str, course: dict, task: dict, urlparams: dict) -> dict:
    print("This function is not implemented yet.")


def get_pj_single_class_url(course: dict, task: dict) -> tuple[str, dict]:
    # tasklib = asyncio.run(get_tasklib(course, task))
    baseurl = (
        "http://jiaowupj.nit.edu.cn/evaluate/studentEvaluate/evaluate-jdpdetail/index"
    )
    params = {
        "taskid": course["xspjid"],
        "libtaskid": [
            item["taskid"]
            for item in task["items"]
            if item["taskname"] == course["taskname"]
        ][0],
        "type": "student_jdp",
        "jgxm": course["jgxm"],
        "kcmc": course["kcmc"],
        "kcsxcode": course["kcsxcode"],
        "pjsjid": course["pjsjid"],
        "cpztcode": course["cpztcode"],
        "xnxqid": course["xnxqid"],
        "pjrid": course["pjrid"],
        "iskpj": (
            course["iskpj"] if course["iskpj"] and course["iskpj"] != "null" else ""
        ),
        "isyx": course["isyx"] if course["isyx"] and course["isyx"] != "null" else "",
        "issubmit": course["issubmit"],
        # "libid": tasklib["id"],
        "libid": (
            course["libid"]
            if course["libid"] and course["libid"] != "null" in course
            else ""
        ),
        "isjdp": "true",
        "kkdwid": course["kkdwid"],
        "dwid": course["kkdwid"],
    }
    # url编码
    full_url = f"{baseurl}?{urllib.parse.urlencode(params)}"
    return full_url, params


def get_single_pj_urls(
    semester: str, aim_status: str | list = None, taskname: str = None
) -> list[str]:

    assert semester and isinstance(semester, str), "semester must be a string"

    tasks = asyncio.run(get_bj_tasks(jwt, semester))
    taskscopy = tasks.copy()
    print(tasks)
    with open("tasks.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(tasks, ensure_ascii=False, indent=4))

    sigle_pj_urls = []

    for item in tasks["items"]:
        # 符合条件的任务
        # 如果没有指定taskname，就是所有的任务
        if (taskname and item["taskname"].strip() == taskname.strip()) or (
            not taskname
        ):
            for status in (
                ["未评", "已评"]
                if not aim_status
                else ([aim_status] if isinstance(aim_status, str) else aim_status)
            ):
                example_task = item
                coures = asyncio.run(
                    get_pj_detailed_coures(
                        jwt, example_task["taskid"], semester, status=status
                    )
                )
                with open(
                    f"{item["taskname"]}-{status}.json", "w", encoding="UTF-8"
                ) as f:
                    f.write(json.dumps(coures, ensure_ascii=False, indent=4))
                rowCount = coures["rowCount"]
                items = coures["items"]
                print(
                    f"{item["taskname"]} {status},Courses count:{rowCount} {len(items)}"
                )
                assert rowCount == len(items), "rowCount not equal to items length"

                for c in items:
                    print(c["jgxm"])
                    sigle_pj_url, urlparams = get_pj_single_class_url(c, taskscopy)
                    sigle_pj_urls.append(sigle_pj_url)

    return sigle_pj_urls


# get jwt

jwt: str = None
if not Path("jwt.txt").exists():
    print("jwt.txt not exists, getting jwt...")
    jwt = asyncio.run(get_jwt())
    user_info = asyncio.run(get_user_info(jwt))
    print(user_info)
    with open("jwt.txt", "w") as f:
        f.write(jwt)
else:
    with open("jwt.txt", "r") as f:
        jwt = f.read()
    try:
        print("jwt.txt exists, checking jwt...")
        user_info = asyncio.run(get_user_info(jwt))
        print(user_info)
    except Exception as e:
        print(f"Error: {str(e)}")
        print("jwt expired, getting jwt...")
        jwt = asyncio.run(get_jwt())
        # print(jwt)
        user_info = asyncio.run(get_user_info(jwt))
        print(user_info)
        with open("jwt.txt", "w") as f:
            f.write(jwt)
