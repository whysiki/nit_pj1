### 环境

- Python 3.12
- 安装依赖`pip install -r requirements.txt`
- 下载firefox浏览器`playwright install firefox`

### 配置

在根目录新建一个`.env`文件(没有文件名，后缀env)，内容如下：
```shell
USER_NAME = 2021100xxx
PASSWORD = 你的密码
```

### 运行

启动爬虫`python main.py`，爬虫会自动登录并评价所有未评价的课程。
```python
semester = "2024-2025-1" # 学期
aim_status = None # 评价状态 None表示所有没用提交评价或者没有评价的课程。
```

