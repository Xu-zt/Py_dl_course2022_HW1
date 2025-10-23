import requests
from bs4 import BeautifulSoup
from collections import Counter
import json

TEST_STR = ["Yaqin Zhang"]
DBLP_BASE_URL = 'https://dblp.org/'
SEARCH_URL = DBLP_BASE_URL + "search/"

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
    Chrome/55.0.2883.87 Safari/537.36'
}


def get_pub_data(pub):

    ptype, link, authors, title, where = '', '', [], '', ''

    if 'year' in pub.get('class'):
        # Debug: In dblp serch web, year will be singally shown in the contents, so must be judged independentlly  2022.3.27
        # continue
        return int(pub.contents[0])  # provide following criteria
    else:
        ptype = pub.attrs.get('class')[1]  # 'Type' can be judged bufore we judge the class of the item
        for content_item in pub.contents:
            class_of_content_item = content_item.attrs.get('class', [0])
            if 'data' in class_of_content_item:
                for author in content_item.findAll('span', attrs={"itemprop": "author"}):
                    authors.append(author.text)
                title = content_item.find('span', attrs={"class": "title"}).text
                for where_data in content_item.findAll('span', attrs={"itemprop": "isPartOf"}):
                    found_where = where_data.find('span', attrs={"itemprop": "name"})
                    if found_where:
                        where = found_where.text
            if 'publ' in class_of_content_item:  # Debug: Here we need to judge wether the kind of the item is 'publication'  2022.3.27
                link = content_item.contents[0].find('a').attrs.get('href', "nothing")
    return {'Type': ptype, 'Link': link, 'Authors': authors, 'Title': title, 'Where': where}  # Create data structure: Dictionary


class HtmlCrawler(object):

    # Debug 2022/4/4: When writing functions in class, we should add param "self" in each fuction
    def Crawl_html(self, key=TEST_STR):      # if input param is none, we use TEST_STR defaultly
        soup = BeautifulSoup(
            requests.get(SEARCH_URL, params={'q': key}).content, "html.parser")
        pub_list_raw = soup.find("ul", attrs={"class": "publ-list"})
        return pub_list_raw


class HtmlParser(object):

    def Parse_html(self, pub_list_raw):
        pub_list_data = []  # the list of dictionaries

        curr_year = 0
        for child in pub_list_raw.children:
            pub_data = get_pub_data(child)
            # pub_list_data.append(pub_data)
            if type(pub_data) == int:  # Debug: To follow the rule of dblp serch web  2022.3.29
                curr_year = pub_data
            else:
                pub_data['Year'] = curr_year
                pub_list_data.append(pub_data)

        return pub_list_data


class Outputer(object):

    # def output_terminal(self, datas):  # see results on terminal
    #     print("------------------------------------------------------------------------------------------------------------------------------------------")
    #     print("|  Type  |                  Link                  |  First Author  |                          Title                             |  year  |")
    #     for item in datas:
    #         if item.get('Link') == '':
    #             continue
    #         print("------------------------------------------------------------------------------------------------------------------------------------------")
    #         print("|{:^8}|{:^40}|{:^16}|{:^60}|{:^8}|".format(item.get('Type'),
    #                                                           item.get('Link'),
    #                                                           (item.get('Authors')[0] if len(item.get('Authors')) else ''),
    #                                                           item.get('Title'),
    #                                                           item.get('Year')))
    #     print("------------------------------------------------------------------------------------------------------------------------------------------")
    def output_terminal(self, datas):      # simple terminal output
        print("\nAll related publications links are listed as belows:")
        for item in datas:
            if item.get('Link') == '':
                continue
            print(item.get('Link'))
        print("For more details, please refer the document \"result.html\" in web page.\n")
    
    def output_terminal_statistics(self, stats):
        """在终端输出统计信息"""
        if stats:
            analyzer = StatisticsAnalyzer()
            analyzer.stats = stats
            print(analyzer.generate_statistics_report())
            print()

    def outputer_html(self, datas, search_str, statistics_analyzer=None):

        f = open("result.html", "w", encoding='utf-8')

        f.write('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DBLP Searching Information</title>
        </head>
        ''')

        f.write("<body>\n")
        f.write("<table border='1' width='100%' cellspacing='0' cellpadding='4' bgcolor='#EEF7F2'>\n")
        f.write("<caption><h3>Searching Result for \"%s\"</h3></caption>\n" % search_str)
        f.write('''
        <tr>
            <th>Type</th>
            <th>Link</th>
            <th>First Author</th>
            <th>Title</th>
            <th>Source</th>
            <th>Year</th>
        </tr>
        ''')
        for item in datas:
            if item.get('Link') == '':
                continue
            f.write("<tr>\n")
            f.write("   <td>{}</td>\n".format(item.get('Type')))
            f.write("   <td><a href='{}'>{}</a></td>\n".format(item.get('Link'), item.get('Link')))
            f.write("   <td><a href='{}'>{}</a></td>\n".format(("https://dblp.org/search?q=" + item.get('Authors')[0]), item.get('Authors')[0] if len(item.get('Authors')) else ''))
            f.write("   <td>{}</td>\n".format(item.get('Title')))
            f.write("   <td>{}</td>\n".format(item.get('Where')))
            f.write("   <td>{}</td>\n".format(item.get('Year')))
            f.write("</tr>\n")

        f.write("</table>\n")

        f.write("<br/>")
        
        # 添加统计信息部分
        if statistics_analyzer and statistics_analyzer.stats:
            f.write(statistics_analyzer.get_html_statistics_section())
            f.write("<br/>")
        
        f.write("<div align='right'>Note: The data shown above is from <a href='https://dblp.org/'>https://dblp.org/</a> </div>\n")
        f.write("<div align='right'>For py_dl_course2022 larning only    --Ruizhe Wang </div>\n")
        f.write("</body>\n")
        f.write("</html>\n")
        f.close()


class StatisticsAnalyzer(object):
    """
    文献统计和分析器
    提供对检索结果的统计分析功能
    """
    
    def __init__(self):
        self.stats = {}
    
    def analyze_publications(self, pub_list_data):
        """
        分析文献数据并生成统计信息
        
        Args:
            pub_list_data: 文献数据列表
            
        Returns:
            dict: 包含各种统计信息的字典
        """
        if not pub_list_data:
            return {}
        
        # 基本统计
        total_pubs = len(pub_list_data)
        
        # 年份统计
        years = [pub.get('Year', 0) for pub in pub_list_data if pub.get('Year', 0) > 0]
        year_distribution = Counter(years)
        
        # 文献类型统计
        types = [pub.get('Type', 'Unknown') for pub in pub_list_data]
        type_distribution = Counter(types)
        
        # 作者统计
        all_authors = []
        for pub in pub_list_data:
            authors = pub.get('Authors', [])
            all_authors.extend(authors)
        author_distribution = Counter(all_authors)
        
        # 期刊/会议统计
        venues = [pub.get('Where', 'Unknown') for pub in pub_list_data if pub.get('Where', '')]
        venue_distribution = Counter(venues)
        
        # 计算统计指标
        avg_authors_per_paper = len(all_authors) / total_pubs if total_pubs > 0 else 0
        most_recent_year = max(years) if years else 0
        oldest_year = min(years) if years else 0
        
        # 最活跃的作者（前10名）
        top_authors = author_distribution.most_common(10)
        
        # 最热门的期刊/会议（前10名）
        top_venues = venue_distribution.most_common(10)
        
        # 年份分布（前10年）
        top_years = year_distribution.most_common(10)
        
        self.stats = {
            'total_publications': total_pubs,
            'year_range': {
                'oldest': oldest_year,
                'most_recent': most_recent_year,
                'span': most_recent_year - oldest_year if most_recent_year > 0 and oldest_year > 0 else 0
            },
            'average_authors_per_paper': round(avg_authors_per_paper, 2),
            'type_distribution': dict(type_distribution),
            'top_authors': top_authors,
            'top_venues': top_venues,
            'top_years': top_years,
            'total_unique_authors': len(author_distribution),
            'total_unique_venues': len(venue_distribution)
        }
        
        return self.stats
    
    def generate_statistics_report(self):
        """
        生成统计报告文本
        
        Returns:
            str: 格式化的统计报告
        """
        if not self.stats:
            return "暂无统计数据"
        
        report = []
        report.append("=" * 60)
        report.append("文献检索统计报告")
        report.append("=" * 60)
        
        # 基本统计
        report.append(f"总文献数量: {self.stats['total_publications']}")
        report.append(f"年份范围: {self.stats['year_range']['oldest']} - {self.stats['year_range']['most_recent']}")
        report.append(f"年份跨度: {self.stats['year_range']['span']} 年")
        report.append(f"平均每篇文献作者数: {self.stats['average_authors_per_paper']}")
        report.append(f"涉及作者总数: {self.stats['total_unique_authors']}")
        report.append(f"涉及期刊/会议总数: {self.stats['total_unique_venues']}")
        
        # 文献类型分布
        report.append("\n文献类型分布:")
        report.append("-" * 30)
        for pub_type, count in self.stats['type_distribution'].items():
            report.append(f"{pub_type}: {count} 篇")
        
        # 最活跃的作者
        report.append("\n最活跃的作者 (前10名):")
        report.append("-" * 30)
        for i, (author, count) in enumerate(self.stats['top_authors'], 1):
            report.append(f"{i:2d}. {author}: {count} 篇")
        
        # 最热门的期刊/会议
        report.append("\n最热门的期刊/会议 (前10名):")
        report.append("-" * 30)
        for i, (venue, count) in enumerate(self.stats['top_venues'], 1):
            report.append(f"{i:2d}. {venue}: {count} 篇")
        
        # 年份分布
        report.append("\n年份分布 (前10年):")
        report.append("-" * 30)
        for year, count in self.stats['top_years']:
            report.append(f"{year}: {count} 篇")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_html_statistics_section(self):
        """
        生成HTML格式的统计信息部分
        
        Returns:
            str: HTML格式的统计信息
        """
        if not self.stats:
            return ""
        
        html = []
        html.append('<div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px;">')
        html.append('<h3 style="color: #2c3e50; margin-bottom: 15px;">📊 文献统计报告</h3>')
        
        # 基本统计卡片
        html.append('<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">')
        html.append(f'<div style="background: white; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px;">')
        html.append(f'<h4 style="margin: 0 0 10px 0; color: #3498db;">📚 总文献数</h4>')
        html.append(f'<p style="font-size: 24px; font-weight: bold; margin: 0; color: #2c3e50;">{self.stats["total_publications"]}</p>')
        html.append('</div>')
        
        html.append(f'<div style="background: white; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px;">')
        html.append(f'<h4 style="margin: 0 0 10px 0; color: #e74c3c;">👥 作者总数</h4>')
        html.append(f'<p style="font-size: 24px; font-weight: bold; margin: 0; color: #2c3e50;">{self.stats["total_unique_authors"]}</p>')
        html.append('</div>')
        
        html.append(f'<div style="background: white; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px;">')
        html.append(f'<h4 style="margin: 0 0 10px 0; color: #27ae60;">🏛️ 期刊/会议数</h4>')
        html.append(f'<p style="font-size: 24px; font-weight: bold; margin: 0; color: #2c3e50;">{self.stats["total_unique_venues"]}</p>')
        html.append('</div>')
        
        html.append(f'<div style="background: white; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px;">')
        html.append(f'<h4 style="margin: 0 0 10px 0; color: #f39c12;">📅 年份跨度</h4>')
        html.append(f'<p style="font-size: 24px; font-weight: bold; margin: 0; color: #2c3e50;">{self.stats["year_range"]["span"]} 年</p>')
        html.append('</div>')
        html.append('</div>')
        
        # 详细统计表格
        html.append('<div style="display: flex; gap: 20px; flex-wrap: wrap;">')
        
        # 最活跃的作者
        html.append('<div style="flex: 1; min-width: 300px;">')
        html.append('<h4 style="color: #2c3e50; margin-bottom: 10px;">👥 最活跃的作者</h4>')
        html.append('<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden;">')
        html.append('<tr style="background-color: #3498db; color: white;"><th style="padding: 8px; text-align: left;">排名</th><th style="padding: 8px; text-align: left;">作者</th><th style="padding: 8px; text-align: left;">文献数</th></tr>')
        for i, (author, count) in enumerate(self.stats['top_authors'][:5], 1):
            html.append(f'<tr><td style="padding: 8px; border-bottom: 1px solid #eee;">{i}</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{author}</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{count}</td></tr>')
        html.append('</table>')
        html.append('</div>')
        
        # 最热门的期刊/会议
        html.append('<div style="flex: 1; min-width: 300px;">')
        html.append('<h4 style="color: #2c3e50; margin-bottom: 10px;">🏛️ 最热门的期刊/会议</h4>')
        html.append('<table style="width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden;">')
        html.append('<tr style="background-color: #e74c3c; color: white;"><th style="padding: 8px; text-align: left;">排名</th><th style="padding: 8px; text-align: left;">期刊/会议</th><th style="padding: 8px; text-align: left;">文献数</th></tr>')
        for i, (venue, count) in enumerate(self.stats['top_venues'][:5], 1):
            html.append(f'<tr><td style="padding: 8px; border-bottom: 1px solid #eee;">{i}</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{venue}</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{count}</td></tr>')
        html.append('</table>')
        html.append('</div>')
        
        html.append('</div>')
        html.append('</div>')
        
        return '\n'.join(html)
