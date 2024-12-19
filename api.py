from fastapi import FastAPI
import logging as log
from royaleapi_scraping_class import ScrapingRoyaleAPI
import httpx

app = FastAPI()

log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.get("/save_data")
def save_data():
    RoyaleAPI_scraper = ScrapingRoyaleAPI("UURJ9CG", None)

    RoyaleAPI_scraper.get_soup()
        
    RoyaleAPI_scraper.get_clan_data()

    RoyaleAPI_scraper.get_players_data()

    RoyaleAPI_scraper.get_players_advanced_stats()

    RoyaleAPI_scraper.df_players_data.to_csv("data/players_advanced_stats.csv")
    return {"message": "Data saved"}


@app.get("/ping")
def ping():
    httpx.get('https://eooaw9cy4csi4kr.m.pipedream.net?id=BOT-API')

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5555)
