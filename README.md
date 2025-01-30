# CLI News

---

**CLI News** 是一个命令行新闻阅读器，支持从 **RSS feed** 获取新闻，并提供中文（或其他语言）翻译功能，帮助用户快速获取最新新闻并进行本地化阅读（上班摸鱼）。

![](https://i.imgur.com/1najcuy.png)

![](https://i.imgur.com/ydxAA7H.png)

![](https://i.imgur.com/ebdRoFF.png)

![](https://i.imgur.com/wyZgwnq.png)

---

## 📜 功能

- 从指定的 **RSS feed** 获取新闻
- 提供 **中文翻译** 功能（可以方便的改为其他语言），支持多语言新闻的翻译
- 支持自定义 **RSS feed** 配置
- 简单易用的 **命令行界面**
- 贴心的 **终端适配**

---

## 🚀 安装

### 1. 克隆仓库到本地

首先，将仓库克隆到本地：

```sh
git clone https://github.com/EdGrass/CLINews.git
cd CLINews
```

### 2. 创建并激活虚拟环境

然后，创建并激活虚拟环境：

```sh
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

安装所需的依赖包：

```sh
pip install -r requirements.txt
```

### 4. 创建符号链接（可选）

为了方便运行 **CLI News**，你可以将其创建为全局可执行命令。

在 **macOS/Linux** 系统下：
```sh
# 将 /path/to/CLINews 替换为你的实际项目路径
sudo ln -s "/path/to/CLINews/CLINews.py" /usr/local/bin/News
```

在 **Windows** 系统下：
1. 打开系统环境变量设置
2. 编辑 `Path` 环境变量
3. 添加 CLINews.py 所在的完整目录路径
4. 也可以创建一个 .bat 文件来启动程序

---

## 🧑‍💻 使用

### 启动新闻阅读器

在终端中运行以下命令来启动 **CLI News**：

```sh
python CLINews.py
```

如果你已经创建了符号链接，可以直接运行：

```sh
News
```

### 阅读新闻

程序启动后，**CLI News** 会自动从配置中的 **RSS feed** 获取新闻并显示：

对于非中文文章（可以设置为别的语言）：
- 原文和翻译并排显示
- 使用 `|` 分隔符将屏幕分为左右两栏
- 左侧显示原文，右侧显示中文翻译
- 段落自动对齐，保持阅读连贯性

对于中文文章（同上）：
- 全屏显示原文内容
- 自动调整段落格式
- 保持原文排版风格

通用功能：
- 支持 `LESS COMMANDS`（按 `h` 键查看更多帮助）
- 自动适应终端大小
- 智能分页显示

---

## ⚙️ 配置

### 配置 RSS Feed

你可以通过修改 `sites.py` 文件来自定义你关注的 **RSS feed**。例如：

```python
interests = {
    "hkn": {
        "url": "https://news.ycombinator.com/rss",
        "desc": "Hacker News"
    },
    "bbc": {
        "url": "http://feeds.bbci.co.uk/news/rss.xml",
        "desc": "BBC News"
    }
}
```

在 `interests` 字典中添加你感兴趣的新闻源，其中 `url` 是 **RSS feed** 的链接，`desc` 是该源的描述。

### 更改默认语言

默认情况下，**CLI News** 使用中文进行翻译。如果你想更改默认翻译语言，请按照以下步骤操作：

1. 打开 `CLINews.py` 文件。

2. 找到以下代码：

    ```python
    self.translator = GoogleTranslator(source='auto', target='zh-CN')
    ```

3. 修改 `target` 参数为你希望的语言代码。例如，将默认语言更改为 **法语**（French）：

    ```python
    self.translator = GoogleTranslator(source='auto', target='fr')
    ```

    常见语言代码与 Google Translate 一致

4. 找到以下代码并类似于上面修改为不需要翻译的语言：

	```python
	lang = detect(text)
            if lang == 'zh-CN' or lang == 'zh-TW':
                return text
	```

5. 保存文件并重新运行程序。

---

## 📄 许可证

本项目采用 MIT 许可证。查看 [LICENSE](LICENSE) 文件了解更多详细信息。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 💬 反馈与贡献

如果你在使用过程中遇到任何问题，或者有好的改进建议，请随时通过 **GitHub Issues** 提交反馈，或创建 **Pull Request** 为项目贡献代码！

---