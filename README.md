---

# CLI News

**CLI News** 是一个命令行新闻阅读器，支持从 **RSS feed** 获取新闻，并提供中文（或其他语言）翻译功能，帮助用户快速获取最新新闻并进行本地化阅读（上班摸鱼）。

![](https://i.imgur.com/1najcuy.png)

![](https://i.imgur.com/ydxAA7H.png)

![](https://i.imgur.com/hnDCSWP.png)

![](https://i.imgur.com/wyZgwnq.png)

---

## 📜 功能

- 从指定的 **RSS feed** 获取新闻
- 提供 **中文翻译** 功能（可以方便的改为其他语言），支持多语言新闻的翻译
- 支持自定义 **RSS feed** 配置
- 简单易用的 **命令行界面**

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

为了方便运行 **CLI News**，你可以将其创建为全局可执行命令：

```sh
sudo ln -s /Users/edgrass/Documents/Vscode/CLI\ News/CLINews.py /usr/local/bin/News
```

如果你使用的是 **Windows** 系统，可以考虑手动将 `CLINews.py` 文件路径添加到系统环境变量中。

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

程序启动后，**CLI News** 会自动从配置中的 **RSS feed** 获取新闻并显示。你可以使用 `LESS COMMANDS`（例如 `h` 键）来查看更多帮助。

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

## 🛠️ 常见问题

### 1. `No such file or directory` 错误

如果你在创建符号链接时遇到 `No such file or directory` 错误，通常是因为路径中有空格。可以使用以下两种方法之一解决：

- **方法 1**：使用引号包裹路径：

  ```sh
  sudo ln -s "/Users/edgrass/Documents/Vscode/CLI News/CLINews.py" /usr/local/bin/News
  ```

- **方法 2**：使用反斜杠转义空格：

  ```sh
  sudo ln -s /Users/edgrass/Documents/Vscode/CLI\ News/CLINews.py /usr/local/bin/News
  ```

---

## 📄 许可证

本项目采用 MIT 许可证。查看 [LICENSE](LICENSE) 文件了解更多详细信息。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 💬 反馈与贡献

如果你在使用过程中遇到任何问题，或者有好的改进建议，请随时通过 **GitHub Issues** 提交反馈，或创建 **Pull Request** 为项目贡献代码！

---