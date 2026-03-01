"""
新闻数据采集（使用真实API + 情感分析）
"""
import logging
from datetime import datetime, timedelta
import random
import sys
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import StockNews, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻数据采集器"""

    def __init__(self):
        """初始化"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.use_real_api = os.getenv('USE_REAL_NEWS_API', 'true').lower() == 'true'

        # 尝试导入情感分析库
        self.sentiment_analyzer = None
        try:
            from snownlp import SnowNLP
            self.sentiment_analyzer = 'snownlp'
            logger.info("✅ SnowNLP 情感分析已启用")
        except ImportError:
            logger.warning("⚠️  SnowNLP 未安装，使用简单情感分析")

    def _simple_sentiment(self, text: str) -> float:
        """
简单的情感分析（基于关键词）

        Args:
            text: 文本

        Returns:
            情感得分 (-1 到 1)
        """
        # 正面关键词
        positive_words = ['增长', '上涨', '利好', '突破', '创新', '强势', '盈利', '收益', '增长', '扩展',
                          '提升', '改善', '向好', '优秀', '成功', '发布', '推出', '获得', '达成']

        # 负面关键词
        negative_words = ['下跌', '下跌', '亏损', '风险', '下滑', '回落', '警告', '危机', '暴跌', '暴跌',
                          '下滑', '下降', '恶化', '失败', '延迟', '取消', '停止', '撤回', '违约']

        score = 0
        text_lower = text.lower()

        for word in positive_words:
            score += text_lower.count(word) * 0.5

        for word in negative_words:
            score -= text_lower.count(word) * 0.5

        # 归一化到 -1 到 1
        return max(-1, min(1, score / 10))

    def _analyze_sentiment(self, text: str) -> float:
        """
        分析情感倾向

        Args:
            text: 文本

        Returns:
            情感得分 (-1 到 1)
        """
        if not text:
            return 0.0

        try:
            # 使用 SnowNLP 进行中文情感分析
            if self.sentiment_analyzer == 'snownlp':
                from snownlp import SnowNLP
                s = SnowNLP(text)
                # SnowNLP 返回 0-1，转换到 -1 到 1
                return (s.sentiments - 0.5) * 2
            else:
                return self._simple_sentiment(text)
        except Exception as e:
            logger.debug(f"情感分析失败: {e}，使用简单分析")
            return self._simple_sentiment(text)

    def _get_sentiment_label(self, score: float) -> str:
        """
        获取情感标签

        Args:
            score: 情感得分

        Returns:
            情感标签
        """
        if score > 0.2:
            return 'positive'
        elif score < -0.2:
            return 'negative'
        else:
            return 'neutral'

    def fetch_financial_news_from_eastmoney(self, limit: int = 50) -> List[Dict]:
        """
        从东方财富网获取财经新闻

        Args:
            limit: 获取数量

        Returns:
            新闻列表
        """
        news_list = []

        try:
            # 东方财富新闻 API
            url = f"http://api.eastmoney.com/aapi/st/cgt/list/CgtpGG/newsList?limit={limit}&fields=f1,f2,f3,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f22,f23,f24,f25,f26,f27,f28,f29,f30,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f41,f42,f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65,f66,f67,f68,f69,f70,f71,f72,f73,f74,f75,f76,f77,f78,f79,f80,f81,f82,f83,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['rc'] == 0 and 'data' in data and 'diff' in data['data']:
                for item in data['data']['diff']:
                    news_item = {
                        'title': item.get('a2', ''),
                        'content': item.get('a6', '') or item.get('a2', ''),
                        'url': item.get('a1', ''),
                        'pub_date': datetime.fromtimestamp(item.get('a16', 0) / 1000) if item.get('a16') else datetime.now(),
                        'source': 'eastmoney'
                    }

                    # 情感分析
                    sentiment_score = self._analyze_sentiment(news_item['title'] + ' ' + news_item['content'])
                    news_item['sentiment'] = sentiment_score
                    news_item['sentiment_label'] = self._get_sentiment_label(sentiment_score)

                    news_list.append(news_item)

                logger.info(f"✅ 从东方财富获取新闻: {len(news_list)} 条")

        except Exception as e:
            logger.warning(f"⚠️  从东方财富获取新闻失败: {e}")

        return news_list[:limit]

    def fetch_financial_news_from_sina(self, limit: int = 50) -> List[Dict]:
        """
        从新浪财经获取财经新闻

        Args:
            limit: 获取数量

        Returns:
            新闻列表
        """
        news_list = []

        try:
            # 新浪财经滚动新闻
            url = "https://finance.sina.com.cn/roll/index.d.html"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找新闻列表
            news_items = soup.find_all('li', class_='feed-item')

            for idx, item in enumerate(news_items):
                if idx >= limit:
                    break

                try:
                    link_tag = item.find('a')
                    if not link_tag:
                        continue

                    title = link_tag.get_text(strip=True)
                    url_link = link_tag.get('href', '')
                    time_tag = item.find('span', class_='date')

                    pub_date = datetime.now()
                    if time_tag:
                        time_text = time_tag.get_text(strip=True)
                        # 尝试解析时间
                        try:
                            if '今天' in time_text:
                                pub_date = datetime.now()
                            elif '分钟' in time_text:
                                minutes = int(re.search(r'\d+', time_text).group())
                                pub_date = datetime.now() - timedelta(minutes=minutes)
                        except:
                            pass

                    news_item = {
                        'title': title,
                        'content': title,  # 新浪滚动新闻只有标题
                        'url': url_link,
                        'pub_date': pub_date,
                        'source': 'sina'
                    }

                    # 情感分析
                    sentiment_score = self._analyze_sentiment(title)
                    news_item['sentiment'] = sentiment_score
                    news_item['sentiment_label'] = self._get_sentiment_label(sentiment_score)

                    news_list.append(news_item)

                except Exception as e:
                    logger.debug(f"解析新闻项失败: {e}")
                    continue

            logger.info(f"✅ 从新浪财经获取新闻: {len(news_list)} 条")

        except Exception as e:
            logger.warning(f"⚠️  从新浪财经获取新闻失败: {e}")

        return news_list[:limit]

    def fetch_financial_news(self, limit: int = 50, source: str = 'all') -> List[Dict]:
        """
        获取财经新闻

        Args:
            limit: 获取数量
            source: 新闻源 ('eastmoney', 'sina', 'all')

        Returns:
            新闻列表
        """
        if not self.use_real_api:
            logger.info("使用模拟新闻数据")
            return self._get_mock_news(limit)

        news_list = []

        if source == 'all' or source == 'eastmoney':
            news_list.extend(self.fetch_financial_news_from_eastmoney(limit))

        if source == 'all' or source == 'sina':
            news_list.extend(self.fetch_financial_news_from_sina(limit))

        if not news_list:
            logger.warning("获取新闻失败，使用模拟数据")
            return self._get_mock_news(limit)

        # 去重（基于标题）
        seen_titles = set()
        unique_news = []
        for news in news_list:
            title = news['title']
            if title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)

        logger.info(f"去重后新闻数量: {len(unique_news)}")
        return unique_news[:limit]

    def _get_mock_news(self, limit: int = 50) -> List[Dict]:
        """
        获取模拟新闻数据

        Args:
            limit: 获取数量

        Returns:
            新闻列表
        """
        mock_news = [
            {
                "title": "央行降准释放万亿资金，市场信心大增",
                "content": "央行宣布全面降准0.25个百分点，释放长期资金约1万亿元，有利于支持实体经济发展。",
                "url": "https://finance.example.com/news/1",
                "sentiment": 0.8,
                "sentiment_label": "positive",
                "source": "mock"
            },
            {
                "title": "新能源汽车销量持续增长，产业链受益",
                "content": "新能源汽车产销两旺，带动锂电池、电机等产业链企业业绩提升。",
                "url": "https://finance.example.com/news/2",
                "sentiment": 0.7,
                "sentiment_label": "positive",
                "source": "mock"
            },
            {
                "title": "美联储加息预期升温，全球市场波动",
                "content": "美联储多位官员释放鹰派信号，市场对加息预期升温。",
                "url": "https://finance.example.com/news/3",
                "sentiment": -0.5,
                "sentiment_label": "negative",
                "source": "mock"
            },
            {
                "title": "科技板块再获政策支持",
                "content": "多项科技创新政策出台，支持人工智能、半导体等前沿领域发展。",
                "url": "https://finance.example.com/news/4",
                "sentiment": 0.6,
            "sentiment_label": "positive",
                "source": "mock"
            },
            {
                "title": "市场震荡调整，投资者需保持理性",
                "content": "当前市场处于震荡调整期，建议投资者保持理性，关注基本面良好的优质标的。",
                "url": "https://finance.example.com/news/5",
                "sentiment": 0.0,
                "sentiment_label": "neutral",
                "source": "mock"
            }
        ]
        return mock_news[:limit]

    def update_news(self, db_session=None, limit: int = 50, source: str = 'all'):
        """
        更新新闻到数据库

        Args:
            db_session: 数据库会话
            limit: 获取数量
            source: 新闻源
        """
        try:
            logger.info("开始更新新闻数据...")

            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            news_list = self.fetch_financial_news(limit=limit, source=source)

            # 检查最近24小时的新闻，避免重复
            yesterday = datetime.now() - timedelta(hours=24)
            recent_news = db.query(StockNews).filter(
                StockNews.created_at > yesterday
            ).all()

            recent_titles = {news.title for news in recent_news}

            added_count = 0
            for news in news_list:
                # 去重
                if news['title'] in recent_titles:
                    continue

                news_obj = StockNews(
                    title=news['title'],
                    content=news['content'],
                    url=news['url'],
                    sentiment=news['sentiment'],
                    pub_date=news.get('pub_date', datetime.now())
                )
                db.add(news_obj)
                added_count += 1

            db.commit()
            logger.info(f"新闻数据更新完成: 添加 {added_count} 条 (共获取 {len(news_list)} 条)")

            if db_session is None:
                db.close()

        except Exception as e:
            logger.error(f"更新新闻数据失败: {e}")
            if db_session is None and 'db' in locals():
                db.rollback()
                db.close()
            raise

    def get_news_by_page(self, page: int = 1, page_size: int = 20, stock_code: Optional[str] = None,
                         sentiment_label: Optional[str] = None, db_session=None) -> Dict:
        """
        分页获取新闻

        Args:
            page: 页码 (从1开始)
            page_size: 每页数量
            stock_code: 股票代码 (可选)
            sentiment_label: 情感标签 ('positive', 'negative', 'neutral')
            db_session: 数据库会话

        Returns:
            {
                'total': 总数,
                'page': 当前页,
                'page_size': 每页数量,
                'total_pages': 总页数,
                'data': 新闻列表
            }
        """
        try:
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session

            query = db.query(StockNews)

            # 筛选条件
            if stock_code:
                # 假设新闻标题中包含股票代码或名称
                query = query.filter(StockNews.title.contains(stock_code))

            if sentiment_label:
                if sentiment_label == 'positive':
                    query = query.filter(StockNews.sentiment > 0.2)
                elif sentiment_label == 'negative':
                    query = query.filter(StockNews.sentiment < -0.2)
                elif sentiment_label == 'neutral':
                    query = query.filter(StockNews.sentiment.between(-0.2, 0.2))

            # 总数
            total = query.count()

            # 分页
            offset = (page - 1) * page_size
            news_items = query.order_by(StockNews.pub_date.desc()).offset(offset).limit(page_size).all()

            data = []
            for news in news_items:
                data.append({
                    'id': news.id,
                    'title': news.title,
                    'content': news.content,
                    'url': news.url,
                    'sentiment': news.sentiment,
                    'sentiment_label': self._get_sentiment_label(news.sentiment),
                    'pub_date': news.pub_date.strftime('%Y-%m-%d %H:%M:%S') if news.pub_date else None,
                    'created_at': news.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            result = {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'data': data
            }

            if db_session is None:
                db.close()

            return result

        except Exception as e:
            logger.error(f"获取新闻分页失败: {e}")
            if db_session is None and 'db' in locals():
                db.close()
            raise


if __name__ == "__main__":
    # 测试
    from database import init_db
    init_db()

    collector = NewsCollector()

    # 测试获取新闻
    print("测试获取新闻:")
    news_list = collector.fetch_financial_news(limit=5, source='all')
    for news in news_list:
        sentiment_str = f"{news['sentiment']:.2f}"
        print(f"  [{news['sentiment_label']}] {sentiment_str:6s} {news['title'][:50]}")

    # 测试更新数据库
    print("\n测试更新数据库:")
    collector.update_news(limit=10)

    # 测试分页
    print("\n测试分页获取:")
    result = collector.get_news_by_page(page=1, page_size=3)
    print(f"总计: {result['total']}, 当前页: {result['page']}, 总页数: {result['total_pages']}")
    for news in result['data']:
        print(f"  {news['title'][:50]}")
