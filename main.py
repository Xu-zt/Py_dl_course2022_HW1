from utils import HtmlCrawler, HtmlParser, Outputer, StatisticsAnalyzer


# initial the web crawler
class My_Crawler(object):

    def __init__(self):
        self.crawler = HtmlCrawler()
        self.parser = HtmlParser()
        self.Outputer = Outputer()
        self.statistics_analyzer = StatisticsAnalyzer()

    def craw(self, search_str):
        pub_list_raw = self.crawler.Crawl_html(search_str)      # Step 1: Crawl the web
        pub_list_data = self.parser.Parse_html(pub_list_raw)    # Step 2: Parse the web
        
        # Step 3: Analyze statistics
        stats = self.statistics_analyzer.analyze_publications(pub_list_data)
        
        # Step 4: Output for visibility
        self.Outputer.output_terminal(pub_list_data)
        self.Outputer.output_terminal_statistics(stats)
        
        # Step 5: Generate HTML output with statistics
        self.Outputer.outputer_html(pub_list_data, search_str, self.statistics_analyzer)


if __name__ == "__main__":
    # search_str = "Houqiang Li"      # Enter the key words here
    crawler = My_Crawler()
    search_str = input("Please input the searching key words: \n")
    crawler.craw(search_str)
