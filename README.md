# Weibo Web Crawler

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

这是一个用于爬取微博搜索结果的 Python 脚本，支持按关键词、时间范围和原创内容筛选，自动下载微博中的图片并保存相关信息到 CSV 文件。

## 功能

- **关键词搜索**：根据指定关键词爬取微博内容。
- **时间范围筛选**：支持自定义时间段（如 "2024-06-18" 至 "2024-12-31"）。
- **原创内容过滤**：仅爬取原创微博（`scope=ori`）。
- **图片下载**：自动下载微博中的图片并保存到本地。
- **动态页数处理**：
  - 如果结果页数 > 49，自动二分时间段并依次处理。
  - 如果结果 ≤ 49 页，按实际页数爬取。
- **网络容错**：请求失败时自动重试3次，每次间隔10秒。

## 安装

1. **克隆仓库**：
   ```bash
   git clone https://github.com/ohemarla/weibo_advanced_crawler.git
   cd weibo-web-crawler
2. **安装依赖**:
   
   确保你有 Python 3.7 或更高版本，然后安装所需库：
   ```bash
   pip install -r requirements.txt
3. **配置cookie**：

   打开 `weibo_advanced_crawler.py`，在 `__request` 方法中将 `Cookie` 字段替换为你的微博登录 Cookie（需要登录微博后从浏览器获取）。

## 使用方法

1. **修改参数**：
   
   编辑 `weibo_crawler.py` 的主程序部分，例如：
    ```python
   if __name__ == "__main__":
       weibo = WeiboWebCrawler()
       weibo.set_search_params(
           keywords=["缅甸地震"],
           start_date="2025-03-28",
           end_date="2025-04-05",
           scope="ori",
           has_pic=True
       )
       weibo.search(pages=49)
2. **运行脚本**：
   ```bash
   python weibo_advanced_crawler.py
3. **输出**：
  - 图片保存至 `./微博图片动态/` 目录。
  - 微博信息保存至 `微博记录.csv` 文件。
  - 日志记录至 `log.txt` 文件。

## 注意事项

- Cookie 更新：微博需要登录态，定期更新 __request 中的 Cookie，否则请求会失败。
- 网络稳定性：脚本会在请求失败时重试3次，每次间隔10秒，若仍失败则跳过当前时间段。
- 文件权限：确保运行目录有写入权限，用于保存图片和 CSV 文件。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进代码！如果有建议或问题，请随时联系。

##许可证

本项目采用 MIT 许可证 (LICENSE)。你可以自由使用、修改和分发代码，但请保留版权声明。
"""


   
