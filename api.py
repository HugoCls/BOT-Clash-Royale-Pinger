from fastapi import FastAPI
import logging as log
from royaleapi_scraping_class import ScrapingRoyaleAPI
import requests

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
    try:
        log.info("Sending request to the external service.")
        r = requests.get('https://eooaw9cy4csi4kr.m.pipedream.net/bot')
        log.info(f"Response from external service: {r.status_code}")
        return {"message": "Done"}
    except requests.exceptions.RequestException as e:
        log.error(f"Error while making the request: {e}")
        return {"message": "Error occurred"}

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5555)
