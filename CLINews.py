#!/Users/edgrass/Documents/Vscode/CLINews/venv/bin/python3

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import click
from readability import Document
import feedparser
from functools import lru_cache
import time
import curses
import sys  
from string import Template
from sites import interests  
from deep_translator import GoogleTranslator
from langdetect import detect
import math
import textwrap

@dataclass
class FeedConfig:
    url: str
    desc: Optional[str] = None
    strip_url_parameters: bool = True
    referrer: Optional[str] = None
    headers: Optional[dict] = None

class NewsReader:
    def __init__(self):
        self.ua = "cmdline-news/2.0 +http://github.com/dpapathanasiou/cmdline-news"
        self.window_cols = 160  # 增加默认宽度以确保显示完整
        self.window_rows = 40
        self._init_terminal_size()
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.cache_ttl = 900  
        self.default_headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        self.translator = GoogleTranslator(source='auto', target='zh-CN')
        self.separator = " | " 
        total_width = self.window_cols - len(self.separator)
        self.left_width = total_width // 2   # 左侧占一半
        self.right_width = total_width - self.left_width  # 右侧占剩余空间（处理奇数情况）
        self.wrap_width = self.left_width  # 保持兼容性

    def _init_terminal_size(self) -> None:
        try:
            screen = curses.initscr()
            self.window_rows, self.window_cols = screen.getmaxyx()
            curses.endwin()
        except curses.error:
            pass

    def _purge_expired(self):
        now = time.time()
        expired = [key for key, (timestamp, _) in self._cache.items() 
                  if now - timestamp > self.cache_ttl]
        for key in expired:
            del self._cache[key]

    async def fetch_feed(self, url: str, feed_config: Optional[FeedConfig] = None) -> Optional[feedparser.FeedParserDict]:
        self._purge_expired()
        if url in self._cache:
            return self._cache[url][1]
        else:
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                headers = {**self.default_headers}
                if feed_config and feed_config.headers:
                    headers.update(feed_config.headers)
                    
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            text = await response.text()
                            feed = feedparser.parse(text)
                            if feed.version and len(feed.version) > 0:
                                self._cache[url] = (time.time(), feed)
                                return feed
                        else:
                            click.echo(f"Error: HTTP {response.status} for {url}")
            except asyncio.TimeoutError:
                click.echo(f"Timeout while fetching {url}")
            except Exception as e:
                click.echo(f"Error fetching feed: {e}")
        return None

    async def get_article_content(self, url: str, feed_config: FeedConfig) -> Optional[str]:
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {**self.default_headers}
            
            if feed_config.headers:
                headers.update(feed_config.headers)

            if 'zhihu.com' in url:
                if getattr(feed_config, 'use_mobile', False):
                    url = url.replace('www.zhihu.com', 'm.zhihu.com')
                click.echo(f"正在获取知乎文章: {url}") 
                
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        if 'zhihu.com' in url:
                            soup = BeautifulSoup(html, 'html.parser')
                            mobile_selectors = [
                                'div.RichContent',
                                'div.content',
                                'div.answer-content'
                            ]
                            desktop_selectors = [
                                'div.Post-RichText',
                                'div.RichText',
                                'div.ContentItem-content'
                            ]
                            
                            selectors = mobile_selectors if getattr(feed_config, 'use_mobile', False) else desktop_selectors
                            
                            for selector in selectors:
                                click.echo(f"尝试使用选择器: {selector}")  
                                content_div = soup.select_one(selector)
                                if content_div:
                                    text = content_div.get_text(separator='\n\n')
                                    if text.strip():
                                        return text.strip()
                            
                            click.echo("未能找到文章内容，保存HTML以供调试...")  
                            with open('debug_zhihu.html', 'w', encoding='utf-8') as f:
                                f.write(html)
                                
                            return None
                            
                        doc = Document(html)
                        content = doc.summary(html_partial=True)
                        soup = BeautifulSoup(content, 'html.parser')
                        return soup.get_text(separator='\n\n').strip()
                    else:
                        click.echo(f"获取文章失败: HTTP {response.status}")
                        click.echo(f"URL: {url}")
                        if response.status == 403:
                            click.echo("访问被拒绝，可能是因为:")
                            click.echo("1. 需要登录")
                            click.echo("2. 触发了反爬虫机制")
                            click.echo("3. 文章可能已被删除或设为私密")
        except Exception as e:
            click.echo(f"获取文章时出错: {str(e)}")
            click.echo(f"URL: {url}")
            import traceback
            click.echo(traceback.format_exc())  
        return None

    async def translate_text(self, text: str) -> str:
        try:
            lang = detect(text)
            if lang == 'zh-CN' or lang == 'zh-TW':
                return text
                
            MAX_LENGTH = 4900  
            chunks = []
            current_chunk = []
            current_length = 0
            
            for paragraph in text.split('\n'):
                if len(paragraph) + current_length > MAX_LENGTH:
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_length = 0
                current_chunk.append(paragraph)
                current_length += len(paragraph)
            
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            
            translated_chunks = []
            for chunk in chunks:
                translated = self.translator.translate(chunk)
                translated_chunks.append(translated)
                
            return '\n'.join(translated_chunks)
        except Exception as e:
            return f"[翻译错误: {str(e)}]"

    def _get_string_width(self, s: str) -> int:
        width = 0
        for char in s:
            # 更精确的东亚字符宽度判断
            if any([
                '\u4e00' <= char <= '\u9fff',  # CJK统一汉字
                '\u3000' <= char <= '\u303f',  # CJK标点符号
                '\u3040' <= char <= '\u309f',  # 平假名
                '\u30a0' <= char <= '\u30ff',  # 片假名
                '\uff00' <= char <= '\uffef'   # 全角字符
            ]):
                width += 2
            else:
                width += 1
        return width

    def _truncate_to_width(self, text: str, width: int) -> str:
        current_width = 0
        result = []
        
        for char in text:
            char_width = 2 if self._get_string_width(char) > 1 else 1
            if current_width + char_width > width:
                break
            result.append(char)
            current_width += char_width
            
        return ''.join(result)

    def format_parallel_text(self, original: str, translation: str) -> str:
        original_paragraphs = original.split('\n')
        translation_paragraphs = translation.split('\n')
        
        # 确保段落数量相同
        max_paragraphs = max(len(original_paragraphs), len(translation_paragraphs))
        original_paragraphs.extend([''] * (max_paragraphs - len(original_paragraphs)))
        translation_paragraphs.extend([''] * (max_paragraphs - len(translation_paragraphs)))
        
        formatted_lines = []
        
        for orig_p, trans_p in zip(original_paragraphs, translation_paragraphs):
            if not orig_p.strip() and not trans_p.strip():
                formatted_lines.append('')
                continue
            
            # 使用相同的宽度限制处理原文和翻译
            orig_lines = self._wrap_text_to_width(orig_p.strip(), self.left_width)
            trans_lines = self._wrap_text_to_width(trans_p.strip(), self.right_width)
            
            # 确保两侧行数相同
            max_lines = max(len(orig_lines), len(trans_lines))
            orig_lines.extend([''] * (max_lines - len(orig_lines)))
            trans_lines.extend([''] * (max_lines - len(trans_lines)))
            
            # 组装每一行
            for o, t in zip(orig_lines, trans_lines):
                o_width = self._get_string_width(o)
                t_width = self._get_string_width(t)
                
                # 添加填充以保持对齐
                left_padding = ' ' * (self.left_width - o_width)
                right_padding = ' ' * (self.right_width - t_width)
                
                line = f"{o}{left_padding}{self.separator}{t}{right_padding}"
                formatted_lines.append(line)
            
            # 段落之间添加空行
            if orig_p.strip() or trans_p.strip():
                formatted_lines.append('')
        
        # 清理多余的空行
        while formatted_lines and not formatted_lines[0].strip():
            formatted_lines.pop(0)
        while formatted_lines and not formatted_lines[-1].strip():
            formatted_lines.pop()
        
        return '\n'.join(formatted_lines)

    def _wrap_text_to_width(self, text: str, width: int) -> List[str]:
        """将文本按照指定宽度换行，考虑CJK字符"""
        lines = []
        remaining = text
        
        while remaining:
            current_width = 0
            cut_index = 0
            
            for i, char in enumerate(remaining):
                char_width = 2 if self._get_string_width(char) > 1 else 1
                if current_width + char_width > width:
                    break
                current_width += char_width
                cut_index = i + 1
            
            if cut_index == 0:  # 防止死循环
                cut_index = 1
            
            current_line = remaining[:cut_index]
            lines.append(current_line)
            remaining = remaining[cut_index:].strip()
        
        return lines if lines else ['']

    async def display_feed(self, feed_config: FeedConfig):
        while True:
            click.clear()
            feed = await self.fetch_feed(feed_config.url, feed_config)
            if not feed or not feed.entries:
                click.echo(f"No entries found in feed: {feed_config.url}")
                return

            entries = list(enumerate(feed.entries, 1))
            for i, entry in entries:
                title = getattr(entry, 'title', 'No title')
                link = getattr(entry, 'link', '')
                if feed_config.strip_url_parameters is not False:
                    link = link.split('?')[0]
                click.echo(f"\n  {i}.\t{title}\n  \t{link}")

            try:
                choice = input("\nChoose article number (Enter to exit): ").strip()
                
                if not choice:
                    return

                try:
                    article_num = int(choice)
                    if 1 <= article_num <= len(entries):
                        entry = feed.entries[article_num - 1]
                        if 'zhihu.com' in feed_config.url:
                            content = entry.get('description', '')
                            if content:
                                soup = BeautifulSoup(content, 'html.parser')
                                for img in soup.find_all('img'):
                                    if img.get('data-caption'):
                                        img.replace_with(f"\n[图片: {img['data-caption']}]\n")
                                    else:
                                        img.decompose()
                                content = soup.get_text(separator='\n\n')
                            else:
                                content = await self.get_article_content(entry.link, feed_config)
                        else:
                            content = await self.get_article_content(entry.link, feed_config)

                        if content:
                            click.clear()
                            margin = ' ' * 2  # 从6改为2
                            paragraphs = content.split('\n\n')
                            paragraphs = [p.strip() for p in paragraphs if p.strip()]
                            
                            try:
                                lang = detect(content)
                                if lang != 'zh-cn' and lang != 'zh-tw':
                                    click.echo("检测到非中文文章，正在翻译...")
                                    click.clear()
                                    
                                    # 先完成翻译
                                    translation = await self.translate_text(content)
                                    trans_paragraphs = translation.split('\n\n')
                                    trans_paragraphs = [p.strip() for p in trans_paragraphs if p.strip()]
                                    
                                    # 准备显示内容
                                    original_formatted = '\n'.join(
                                        f"{margin}{line}" for line in paragraphs
                                    )
                                    translation_formatted = '\n'.join(
                                        f"{margin}{line}" for line in trans_paragraphs
                                    )
                                    
                                    # 翻译完成后再格式化显示
                                    formatted_content = self.format_parallel_text(
                                        original_formatted,
                                        translation_formatted
                                    )
                                else:
                                    formatted_content = '\n'.join(
                                        f"{margin}{line}" for line in paragraphs
                                    )
                                    
                                click.clear()
                                click.echo_via_pager(formatted_content)
                            except Exception as e:
                                click.echo(f"翻译过程中出错: {str(e)}")
                                formatted_content = '\n'.join(
                                    f"{margin}{line}" for line in paragraphs
                                )
                                click.echo_via_pager(formatted_content)
                        else:
                            click.echo("Could not fetch article content")
                    else:
                        click.echo("Invalid article number")
                except ValueError:
                    if choice:
                        click.echo("Please enter a valid number")
            except (EOFError, KeyboardInterrupt):
                return

    async def interactive_mode(self):
        click.clear()
        while True:
            feed = click.prompt(
                "Which feed do you want to read?",
                prompt_suffix=" Input code (! for menu, [enter] to quit) ",
                default="",
                show_default=False
            ).strip().lower()  
            
            if not feed:
                break
                
            if feed == "!":
                self._show_menu()
                continue
                
            try:
                if feed in interests:  
                    feed_data = interests[feed]
                    config = FeedConfig(
                        url=feed_data['url'],
                        desc=feed_data.get('desc'),
                        strip_url_parameters=feed_data.get('strip_url_parameters', True),
                        referrer=feed_data.get('referrer'),
                        headers=feed_data.get('headers')
                    )
                    await self.display_feed(config)
                else:
                    if feed.startswith(('http://', 'https://')):
                        config = FeedConfig(url=feed)
                        await self.display_feed(config)
                    else:
                        click.echo(f"未找到源 '{feed}'，请使用 ! 查看可用的源列表")
                
            except Exception as e:
                click.echo(f"Error processing feed: {e}", err=True)

    def _show_menu(self):
        if not interests:
            click.echo("No feeds defined. Please edit the sites.py file.")
            return
            
        click.clear()  
        click.echo("\nCode       ==>  Description")
        click.echo("----            -----------\n")
        
        for code, feed in sorted(interests.items()):
            desc = feed.get('desc', feed['url'])
            click.echo(f"{code:<10} ==>  {desc}")
        click.echo()

@click.command()
@click.option('--menu', is_flag=True, help="Show available feeds menu")
@click.option('--timeout', default=10, help="Timeout in seconds for network requests")
def main(menu: bool, timeout: int):
    try:
        reader = NewsReader()
        
        if menu:
            reader._show_menu()
            return

        asyncio.run(reader.interactive_mode(), debug=True)
    except KeyboardInterrupt:
        click.echo("\nGoodbye!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
