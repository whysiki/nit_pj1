from main_funcs import *
from playwright_pj_url_async import pj_urls as pj_urls_async

if __name__ == "__main__":
    # 设置学期
    semester = "2024-2025-1"
    aim_status = None
    sigle_pj_urls = get_single_pj_urls(semester=semester, aim_status=aim_status)
    if sigle_pj_urls:
        # pj_urls_async(sigle_pj_urls)
        asyncio.run(pj_urls_async(sigle_pj_urls, headless=False))
    sigle_pj_urls2 = get_single_pj_urls(semester=semester)
    assert not sigle_pj_urls2, "There are still some courses need to be evaluated"
    print("[green]All courses have been evaluated[/green]")
    jsons_ = Path(__file__).parent.glob("*.json")
    for json_ in jsons_:
        json_.unlink()
