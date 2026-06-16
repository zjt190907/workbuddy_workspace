"""
禅道浏览器自动化模块 - 使用 Playwright 抓取"我的bug"列表
"""

from playwright.sync_api import sync_playwright, Page, BrowserContext
import logging
import time
import os
import glob

logger = logging.getLogger(__name__)


def _find_chrome() -> str | None:
    """查找本地已安装的Chrome浏览器路径"""
    possible_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome Beta\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome Beta\Application\chrome.exe"),
        # Edge浏览器也可以
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


class ZentaoChecker:
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password

    def _login(self, page: Page) -> bool:
        """登录禅道"""
        try:
            login_url = f"{self.url}/user-login.html"
            logger.info(f"访问登录页: {login_url}")
            page.goto(login_url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # 填写用户名密码
            page.fill('input[name="account"]', self.username)
            page.fill('input[name="password"]', self.password)

            # 点击登录按钮
            page.click('button[type="submit"], button.btn-primary, input[type="submit"], #submit')

            # 等待登录完成
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)

            # 检查是否登录成功（URL不再包含user-login，或页面上有用户信息）
            current_url = page.url
            if "user-login" not in current_url:
                logger.info("登录成功")
                return True

            # 二次检查：页面是否有用户头像或退出按钮
            user_menu = page.query_selector('#userNav, .user-name, .avatar, a[href*="my"], #my')
            if user_menu:
                logger.info("登录成功（检测到用户元素）")
                return True

            logger.warning("登录可能失败，当前URL: %s", current_url)
            return False

        except Exception as e:
            logger.error("登录异常: %s", e)
            return False

    def _get_bug_list_from_my_page(self, page: Page) -> list[dict]:
        """从'我的地盘-首页'获取我的bug列表"""
        bugs = []
        try:
            # 先尝试直接访问"我的bug"列表页
            # 禅道12+版本: /my-bug.html 或 /bug-browse-my.html
            bug_urls = [
                f"{self.url}/my-bug.html",
                f"{self.url}/bug-browse-my.html",
                f"{self.url}/bug-browse-0-byMe.html",
            ]

            bug_page_loaded = False
            for bug_url in bug_urls:
                try:
                    logger.info(f"尝试访问bug列表: {bug_url}")
                    page.goto(bug_url, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(2)

                    # 检查页面是否有bug表格
                    table = page.query_selector('table.table, table.table-fixed, .table-responsive table, #bugList')
                    if table:
                        bug_page_loaded = True
                        logger.info(f"成功加载bug列表页: {bug_url}")
                        break
                except Exception:
                    continue

            if not bug_page_loaded:
                # 回退方案：从我的地盘首页进入
                logger.info("直接URL失败，尝试从我的地盘首页进入")
                page.goto(f"{self.url}/my.html", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(2)

                # 点击"我的bug"区块的"更多"链接
                bug_link = page.query_selector('a[href*="bug"][href*="my"], a[href*="bug-browse"], .block-bugs a.more, a:has-text("我的Bug"), a:has-text("指派给我的Bug")')
                if bug_link:
                    bug_link.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(2)

            # 解析bug表格
            bugs = self._parse_bug_table(page)

        except Exception as e:
            logger.error("获取bug列表异常: %s", e)

        return bugs

    def _parse_bug_table(self, page: Page) -> list[dict]:
        """解析页面上的bug表格"""
        bugs = []

        # 尝试多种选择器定位bug行
        rows = page.query_selector_all('table tbody tr, .table-sorter tbody tr, #bugList tr')

        if not rows:
            # 尝试新版禅道的卡片/列表布局
            rows = page.query_selector_all('.bug-item, .list-group-item, [data-id]')

        for row in rows:
            try:
                bug = self._parse_bug_row(row, page)
                if bug and bug.get("id"):
                    bugs.append(bug)
            except Exception as e:
                logger.debug("解析行失败: %s", e)
                continue

        logger.info(f"共解析到 {len(bugs)} 条bug")
        return bugs

    def _parse_bug_row(self, row, page: Page) -> dict | None:
        """解析单行bug数据"""
        cells = row.query_selector_all('td')
        if not cells:
            return None

        bug = {}

        # 提取bug ID（通常是第一列或ID列）
        for cell in cells:
            text = cell.inner_text().strip()
            link = cell.query_selector('a')
            if link:
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip()
                # 从链接中提取bug ID
                import re
                id_match = re.search(r'bug-view-(\d+)|bugID=(\d+)|/bug-(\d+)', href)
                if id_match:
                    bug["id"] = next(g for g in id_match.groups() if g)
                    bug["url"] = f"{self.url}/bug-view-{bug['id']}.html" if not href.startswith("http") else href
                    break

            # 尝试纯数字ID
            if text.isdigit() and not bug.get("id"):
                bug["id"] = text
                bug["url"] = f"{self.url}/bug-view-{text}.html"
                break

        if not bug.get("id"):
            return None

        # 提取其他字段（根据禅道列顺序：ID/严重程度/优先级/标题/模块/指派给...）
        cell_texts = [c.inner_text().strip() for c in cells]

        # 尝试智能匹配各字段
        for i, text in enumerate(cell_texts):
            if i == 0:
                continue  # ID已处理
            # 标题通常是最长的文本
            if len(text) > 5 and not bug.get("title"):
                bug["title"] = text
            # 严重程度
            if text in ["致命", "严重", "主要", "次要", "轻微", "建议", "1", "2", "3", "4"]:
                if not bug.get("severity"):
                    bug["severity"] = text
            # 优先级
            if text in ["高", "中", "低", "1", "2", "3", "4"]:
                if not bug.get("priority") and bug.get("severity"):
                    bug["priority"] = text

        # 如果标题没提取到，用第二列之后最长的文本
        if not bug.get("title"):
            for text in cell_texts[1:]:
                if len(text) > 3:
                    bug["title"] = text
                    break

        return bug

    def _get_bug_detail(self, page: Page, bug_url: str) -> dict:
        """获取bug详情页的完整信息"""
        detail = {}
        try:
            page.goto(bug_url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(1)

            # 提取详情页各字段
            # 标题
            title_el = page.query_selector('.detail-title, .page-title, h2, #title, .bug-title')
            if title_el:
                detail["title"] = title_el.inner_text().strip()

            # 严重程度、优先级、指派给等（禅道详情页的table）
            detail_table = page.query_selector('.detail-content table, .table-details, .content table')
            if detail_table:
                ths = detail_table.query_selector_all('th')
                tds = detail_table.query_selector_all('td')
                for th, td in zip(ths, tds):
                    key = th.inner_text().strip()
                    val = td.inner_text().strip()
                    if "严重" in key:
                        detail["severity"] = val
                    elif "优先" in key:
                        detail["priority"] = val
                    elif "指派" in key:
                        detail["assigned_to"] = val
                    elif "模块" in key:
                        detail["module"] = val
                    elif "影响版本" in key or "版本" in key:
                        detail["version"] = val

            # 重现步骤
            steps_el = page.query_selector('.steps-content, #steps, .detail-steps, [name="steps"]')
            if steps_el:
                detail["steps"] = steps_el.inner_text().strip()[:500]  # 限制长度

        except Exception as e:
            logger.warning("获取bug详情失败 %s: %s", bug_url, e)

        return detail

    def check_bugs(self) -> list[dict]:
        """主入口：检查禅道我的bug，返回bug列表"""
        with sync_playwright() as p:
            # 优先使用本地Chrome浏览器，避免等待Playwright自带Chromium下载
            chrome_path = _find_chrome()
            if chrome_path:
                logger.info("使用本地Chrome: %s", chrome_path)
                browser = p.chromium.launch(headless=True, executable_path=chrome_path)
            else:
                logger.info("使用Playwright自带Chromium")
                browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
            )
            page = context.new_page()

            try:
                # 登录
                if not self._login(page):
                    logger.error("登录失败，尝试重试一次")
                    if not self._login(page):
                        logger.error("重试登录仍然失败")
                        return []

                # 获取bug列表
                bugs = self._get_bug_list_from_my_page(page)

                # 获取每个bug的详情（限制前5个，避免太慢）
                for bug in bugs[:5]:
                    if bug.get("url"):
                        detail = self._get_bug_detail(page, bug["url"])
                        # 合并详情，不覆盖已有字段
                        for k, v in detail.items():
                            if v and not bug.get(k):
                                bug[k] = v

                # 超过5个的bug，标记为未获取详情
                for bug in bugs[5:]:
                    if not bug.get("steps"):
                        bug["steps"] = "（详情未自动获取，请点击链接查看）"

                return bugs

            except Exception as e:
                logger.error("检查bug异常: %s", e)
                return []
            finally:
                context.close()
                browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    checker = ZentaoChecker(
        url="http://172.16.1.138:8080/zentao",
        username="zhr",
        password="7890-poi",
    )
    bugs = checker.check_bugs()
    for b in bugs:
        print(b)
