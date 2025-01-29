#!/usr/bin/env python3

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
    headers: Optional[dict] = None  # 添加 headers 字段

class NewsReader:
    def __init__(self):
        self.ua = "cmdline-news/2.0 +http://github.com/dpapathanasiou/cmdline-news"
        self.window_cols = 80
        self.window_rows = 40
        self._init_terminal_size()
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.cache_ttl = 900  # 15 minutes
        self.default_headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        self.translator = GoogleTranslator(source='auto', target='zh-CN')
        self.separator = " | "  # 改回原来的分隔符
        self.wrap_width = (self.window_cols - len(self.separator)) // 2  # 调整宽度计算

    def _init_terminal_size(self) -> None:
        """初始化终端窗口大小"""
        try:
            screen = curses.initscr()
            self.window_rows, self.window_cols = screen.getmaxyx()
            curses.endwin()
        except curses.error:
            # 使用默认值
            pass

    def _purge_expired(self):
        """清理过期缓存"""
        now = time.time()
        expired = [key for key, (timestamp, _) in self._cache.items() 
                  if now - timestamp > self.cache_ttl]
        for key in expired:
            del self._cache[key]

    async def fetch_feed(self, url: str, feed_config: Optional[FeedConfig] = None) -> Optional[feedparser.FeedParserDict]:
        """获取RSS源内容"""
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
                # 如果是移动版，转换URL格式
                if getattr(feed_config, 'use_mobile', False):
                    url = url.replace('www.zhihu.com', 'm.zhihu.com')
                click.echo(f"正在获取知乎文章: {url}")  # 调试信息
                
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        if 'zhihu.com' in url:
                            soup = BeautifulSoup(html, 'html.parser')
                            # 移动版页面的内容选择器
                            mobile_selectors = [
                                'div.RichContent',
                                'div.content',
                                'div.answer-content'
                            ]
                            # 桌面版页面的内容选择器
                            desktop_selectors = [
                                'div.Post-RichText',
                                'div.RichText',
                                'div.ContentItem-content'
                            ]
                            
                            selectors = mobile_selectors if getattr(feed_config, 'use_mobile', False) else desktop_selectors
                            
                            for selector in selectors:
                                click.echo(f"尝试使用选择器: {selector}")  # 调试信息
                                content_div = soup.select_one(selector)
                                if content_div:
                                    text = content_div.get_text(separator='\n\n')
                                    if text.strip():
                                        return text.strip()
                            
                            click.echo("未能找到文章内容，保存HTML以供调试...")  # 调试信息
                            with open('debug_zhihu.html', 'w', encoding='utf-8') as f:
                                f.write(html)
                                
                            return None
                            
                        # 其他网站的处理保持不变
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
            click.echo(traceback.format_exc())  # 打印详细错误信息
        return None

    async def translate_text(self, text: str) -> str:
        """翻译文本到中文"""
        try:
            lang = detect(text)
            if lang == 'zh-CN' or lang == 'zh-TW':
                return text
                
            # 将文本分成小块进行翻译，避免超出长度限制
            MAX_LENGTH = 4900  # Google Translate API 限制
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
        """计算字符串的实际显示宽度（考虑中文字符）"""
        width = 0
        for char in s:
            # 使用东亚字符宽度特性
            if ord(char) > 0x1100 and any([
                0x4E00 <= ord(char) <= 0x9FFF,  # CJK统一汉字
                0x3000 <= ord(char) <= 0x303F,  # CJK符号和标点
                0xFF00 <= ord(char) <= 0xFFEF   # 全角ASCII、全角标点
            ]):
                width += 2
            else:
                width += 1
        return width

    def _truncate_to_width(self, text: str, width: int) -> str:
        """将文本截断到指定显示宽度"""
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
        """格式化双栏显示"""
        # 预处理文本，移除多余空行
        original_lines = [line for line in original.split('\n') if line.strip()]
        translation_lines = [line for line in translation.split('\n') if line.strip()]
        
        # 确保两边行数相等
        max_lines = max(len(original_lines), len(translation_lines))
        original_lines.extend([''] * (max_lines - len(original_lines)))
        translation_lines.extend([''] * (max_lines - len(translation_lines)))
        
        formatted_lines = []
        last_line_empty = True  # 跟踪上一行是否为空

        for orig, trans in zip(original_lines, translation_lines):
            orig = orig.strip()
            trans = trans.strip()
            
            # 只在段落之间添加一个空行
            if orig or trans:  # 如果至少有一边有内容
                if not last_line_empty and formatted_lines:
                    formatted_lines.append('')
                
                # 对原文和译文分别进行包装
                orig_wrapped = textwrap.wrap(orig, width=self.wrap_width) or ['']
                trans_wrapped = textwrap.wrap(trans, width=self.wrap_width * 2) or ['']
                
                # 确保每段的行数相等
                max_wrapped = max(len(orig_wrapped), len(trans_wrapped))
                orig_wrapped.extend([''] * (max_wrapped - len(orig_wrapped)))
                trans_wrapped.extend([''] * (max_wrapped - len(trans_wrapped)))
                
                # 处理每一行
                for o, t in zip(orig_wrapped, trans_wrapped):
                    left_part = self._truncate_to_width(o, self.wrap_width)
                    right_part = self._truncate_to_width(t, self.wrap_width)
                    
                    left_padding = ' ' * (self.wrap_width - self._get_string_width(left_part))
                    right_padding = ' ' * (self.wrap_width - self._get_string_width(right_part))
                    
                    line = f"{left_part}{left_padding}{self.separator}{right_part}{right_padding}"
                    formatted_lines.append(line)
                    last_line_empty = False
            else:
                last_line_empty = True
        
        # 移除开头和结尾的空行
        while formatted_lines and not formatted_lines[0].strip():
            formatted_lines.pop(0)
        while formatted_lines and not formatted_lines[-1].strip():
            formatted_lines.pop()
            
        return '\n'.join(formatted_lines)

    async def display_feed(self, feed_config: FeedConfig):
        """显示 RSS feed 内容"""
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
                        # 知乎RSS源的特殊处理
                        if 'zhihu.com' in feed_config.url:
                            content = entry.get('description', '')
                            if content:
                                # 使用BeautifulSoup处理HTML内容
                                soup = BeautifulSoup(content, 'html.parser')
                                # 移除图片标签但保留caption
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
                            margin = ' ' * 6
                            paragraphs = content.split('\n\n')
                            paragraphs = [p.strip() for p in paragraphs if p.strip()]
                            
                            try:
                                lang = detect(content)
                                if lang != 'zh-cn' and lang != 'zh-tw':
                                    click.echo("检测到非中文文章，正在翻译...")
                                    # 显示原文和翻译进度提示
                                    original_formatted = '\n'.join(
                                        f"{margin}{line}" for line in paragraphs
                                    )
                                    progress_text = "[翻译进行中...]"
                                    initial_display = self.format_parallel_text(
                                        original_formatted, 
                                        progress_text
                                    )
                                    click.echo(initial_display)
                                    
                                    # 进行翻译
                                    translation = await self.translate_text(content)
                                    trans_paragraphs = translation.split('\n\n')
                                    trans_paragraphs = [p.strip() for p in trans_paragraphs if p.strip()]
                                    
                                    # 格式化双栏显示
                                    formatted_content = self.format_parallel_text(
                                        original_formatted,
                                        '\n'.join(f"{margin}{line}" for line in trans_paragraphs)
                                    )
                                else:
                                    # 中文文章直接显示
                                    formatted_content = '\n'.join(
                                        f"{margin}{line}" for line in paragraphs
                                    )
                                    
                                click.clear()
                                click.echo_via_pager(formatted_content)
                            except Exception as e:
                                click.echo(f"翻译过程中出错: {str(e)}")
                                # 发生错误时显示原文
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
        """交互式模式，处理用户输入和显示内容"""
        click.clear()
        while True:
            feed = click.prompt(
                "Which feed do you want to read?",
                prompt_suffix=" Input code (! for menu, [enter] to quit) ",
                default="",
                show_default=False
            ).strip().lower()  # 添加 strip() 和 lower()
            
            if not feed:
                break
                
            if feed == "!":
                self._show_menu()
                continue
                
            try:
                # 尝试从预定义源获取
                if feed in interests:  # 移除 lower() 因为已经在输入时处理了
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
                    # 检查是否是有效的URL
                    if feed.startswith(('http://', 'https://')):
                        config = FeedConfig(url=feed)
                        await self.display_feed(config)
                    else:
                        click.echo(f"未找到源 '{feed}'，请使用 ! 查看可用的源列表")
                
            except Exception as e:
                click.echo(f"Error processing feed: {e}", err=True)

    def _show_menu(self):
        """显示可用的订阅源菜单"""
        if not interests:
            click.echo("No feeds defined. Please edit the sites.py file.")
            return
            
        click.clear()  # 添加清屏
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
    """Modern command-line RSS reader"""
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
