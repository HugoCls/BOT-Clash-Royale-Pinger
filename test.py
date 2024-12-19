from royaleapi_scraping_class import ScrapingRoyaleAPI

RoyaleAPI_scraper = ScrapingRoyaleAPI("UURJ9CG", None)

RoyaleAPI_scraper.get_soup()
    
RoyaleAPI_scraper.get_clan_data()

RoyaleAPI_scraper.get_players_data()

RoyaleAPI_scraper.get_players_advanced_stats()

RoyaleAPI_scraper.df_players_data.to_csv("data/players_advanced_stats.csv")