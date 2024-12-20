import httpx
from bs4 import BeautifulSoup
import pandas as pd
import re
import Levenshtein
import concurrent.futures
import logging as log
import traceback
import time
import json

log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SAVE_TIME_FILE = "data/save_time.json"

def calculate_match_percentage(name1, name2):
    # Convertir les noms en minuscules
    name1 = name1.lower()
    name2 = name2.lower()
    
    # Garder uniquement les caractères a-z et 0-9
    name1 = ''.join(re.findall(r'[a-z0-9]', name1))
    name2 = ''.join(re.findall(r'[a-z0-9]', name2))
    
    # Calculer la distance de Levenshtein
    max_length = max(len(name1), len(name2))
    distance = Levenshtein.distance(name1, name2)
    similarity = 1 - (distance / max_length)
    
    return round(similarity, 3)


class ScrapingRoyaleAPI:
    def __init__(self, clan_id, df_discord_data):
               
        self.clan_id = clan_id
        
        self.df_discord_data = df_discord_data
        
    def run(self):

        self.get_soup()
        
        self.get_clan_data()
        
        self.get_players_data()

        self.get_players_discords_matches()
    
    def get_soup(self):
        
        r = httpx.get(f'https://royaleapi.com/clan/{self.clan_id}/war/race')
        
        text = r.text
        
        self.soup = BeautifulSoup(text,'html.parser')
     
    def get_clan_data(self):
        
        self.day = self.soup.find_all('div',class_="day")[0].get_text().strip('\n')
        
        self.medals = self.soup.select("#page_content > div.ui.attached.container.sidemargin0.content_container > div:nth-child(2) > div > a.clan.row.active_clan > div.outline.cw2__standing_outline > div.item.value.medal")[0].text.strip('\n')[2:].strip('-')
        self.medals = re.search(r'\d+', self.medals).group()

        self.medals_avg = self.soup.select("#page_content > div.ui.attached.container.sidemargin0.content_container > div:nth-child(2) > div > a.clan.row.active_clan > div.outline.cw2__standing_outline > div.item.value.medal_avg")[0].text.strip('\n')
        self.medals_avg = re.search(r'[\d\.]+', self.medals_avg).group()

        self.decks_used_today = self.soup.select("#page_content > div.ui.attached.container.sidemargin0.content_container > div:nth-child(2) > div > a.clan.row.active_clan > div.outline.cw2__standing_outline > div.item.value.decks_used_today")[0].text.strip('\n')
        self.decks_used_today = self.decks_used_today.strip()

        [nb_decks_used,nb_decks_max] = self.decks_used_today.replace(' ','').split('/')

        self.decks_remaining = int(nb_decks_max) - int(nb_decks_used)
        
        self.clan_name = self.soup.select('#page_content > div:nth-child(5) > div.ui.attached.padded.segment > div.p_header_container > div:nth-child(1) > h1')[0].text.strip('\n')
        self.clan_name = self.clan_name.strip()
           
    def get_players_data(self):
        """
        Extract players data from the soup and stores it in a DataFrame
        """
        self.df_players_data = pd.DataFrame(columns=["cr_id", "cr_name", "player_role", "decks_used_today", "decks_used", "boat_attacks", "fame", "discord_name", "discord_id", "match_ratio"])

        players = self.soup.find_all('td', class_="player_name")

        for player in players:
            cr_id = '#' + player.find_all('a', href=True)[0]['href'].strip('/player/').strip('/battles').strip()
            name = player.find_all('a', class_='player_name force_single_line_hidden')[0].get_text().strip()
            player_role = player.find_all('div', class_='player_role')[0].get_text().strip()
            decks_used_today = player.find_all('div', class_='value_bg decks_used_today')[0].get_text().strip()
            decks_used = player.find_all('div', class_='value_bg decks_used')[0].get_text().strip()
            boat_attacks = player.find_all('div', class_='value_bg boat_attacks')[0].get_text().strip()
            fame = player.find_all('div', class_='value_bg fame')[0].get_text().strip()

            if player_role != "--":
                player_dict = {
                    "cr_id": [cr_id],
                    "cr_name": [name],
                    "player_role": [player_role],
                    "decks_used_today": [decks_used_today],
                    "decks_used": [decks_used],
                    "boat_attacks": [boat_attacks],
                    "fame": [fame],
                }

                self.df_players_data = pd.concat(
                    [self.df_players_data, pd.DataFrame.from_dict(player_dict)], 
                    ignore_index=True
                )

        self.slots = len(self.df_players_data[self.df_players_data['decks_used_today'] == "0"])


    def get_players_discords_matches(self):
        """
        Determines the best matching Discord IDs for each player based on their pseudonyms.
        Modifies the DataFrame in-place to update with matched Discord names, IDs, and ratios.
        """
        #log.info("Determining which discord ids are the best for these pseudos")

        for player_index in self.df_players_data.index:
            cr_name = self.df_players_data.at[player_index, "cr_name"]
            best_match_name = ""
            best_match_disc_id = ""
            best_match_ratio = 0

            for discord_index in self.df_discord_data.index:
                disc_name = self.df_discord_data.at[discord_index, "discord_name"]
                disc_id = self.df_discord_data.at[discord_index, "discord_id"]

                ratio = calculate_match_percentage(cr_name, disc_name)

                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_name = disc_name
                    best_match_disc_id = disc_id

            # Update the player row directly in the DataFrame
            self.df_players_data.at[player_index, "discord_name"] = best_match_name
            self.df_players_data.at[player_index, "discord_id"] = best_match_disc_id
            self.df_players_data.at[player_index, "match_ratio"] = best_match_ratio

    def get_players_advanced_stats(self):
        log.info("Saving players advanced stats")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.get_player_advanced_stats, self.df_players_data.at[player_index, "cr_id"])
                for player_index in self.df_players_data.index
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log.info(f"{e}")
                    

    def get_player_advanced_stats(self, cr_id):
        try:
            r = httpx.get(f'https://royaleapi.com/player/{cr_id.replace("#","").lower()}/')
            
            token = re.search("token: '(.+)'", r.text).group(1).replace('\n','').replace(' ','')
            cookies = r.cookies
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "fr-FR,fr;q=0.9",
                #"Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://royaleapi.com/player/YLLVYYRU",
                "Authorization": f"Bearer {token}",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Priority": "u=1, i",
                "Te": "trailers",
                "Connection": "keep-alive"
            }

            r = httpx.get(f'https://royaleapi.com/player/cw2_history/{cr_id.replace("#","").lower()}', cookies=cookies, headers=headers)
            
            player_data = pd.DataFrame(r.json()["rows"])

            # Supprimer les lignes contenant des NaN dans les colonnes spécifiques avant conversion
            player_data = player_data.dropna(subset=['contribution', 'decks_used', 'clan_rank'])

            # Convertir les colonnes en numérique et gérer les erreurs
            player_data['contribution'] = pd.to_numeric(player_data['contribution'], errors='coerce')
            player_data['decks_used'] = pd.to_numeric(player_data['decks_used'], errors='coerce')
            player_data['clan_rank'] = pd.to_numeric(player_data['clan_rank'], errors='coerce')

            # Supprimer les lignes où des NaN sont encore présents après conversion
            player_data = player_data.dropna(subset=['contribution', 'decks_used', 'clan_rank'])

            # Calcul des moyennes avec arrondi à 2 décimales
            avg_contribution = round(player_data['contribution'].mean(), 2) if not player_data['contribution'].isna().all() else None
            avg_decks_used = round(player_data['decks_used'].mean(), 2) if not player_data['decks_used'].isna().all() else None
            avg_clan_rank = round(player_data['clan_rank'].mean(), 2) if not player_data['clan_rank'].isna().all() else None
            avg_real_contribution = round(player_data.loc[~((player_data['decks_used'] >= 16) & (player_data['contribution'] < 1800)), 'contribution'].mean(), 2) if not player_data['contribution'].isna().all() else None

            self.df_players_data.loc[self.df_players_data["cr_id"] == cr_id, "avg_contribution"] = [str(avg_contribution)]
            self.df_players_data.loc[self.df_players_data["cr_id"] == cr_id, "avg_real_contribution"] = [str(avg_real_contribution)]
            self.df_players_data.loc[self.df_players_data["cr_id"] == cr_id, "avg_decks_used"] = [str(avg_decks_used)]
            self.df_players_data.loc[self.df_players_data["cr_id"] == cr_id, "avg_clan_rank"] = [str(avg_clan_rank)]
            
            # Ajout des données des scores
            _data = r.json()["rows"]
            _data = [{key: value for key, value in d.items() if key in ["contribution","decks_used", "clan_rank", "log_date"]} for d in _data]
            self.df_players_data.loc[self.df_players_data["cr_id"] == cr_id, "cw_last_scores"] = [str(_data)]  
            log.info(f"{cr_id} went well: avg_contribution:{avg_contribution}, avg_real_contribution: {avg_real_contribution}, avg_decks_used:{avg_decks_used}, avg_clan_rank:{avg_clan_rank}")
            
            with open(SAVE_TIME_FILE, "w") as f:
                current_time = time.time()
                json.dump({"last_save_time": current_time}, f)
            
        except Exception as e:
            log.error(f"Something went wrong with {cr_id}: {str(e)}")
            log.error(f"Traceback: {traceback.format_exc()}")


    def print_clan_data(self):
        """
        log.infos the clan data collected in a readable format.
        """
        log.info("Clan Data:")
        log.info(f"  Day: {self.day}")
        log.info(f"  Clan Name: {self.clan_name}")
        log.info(f"  Total Medals: {self.medals}")
        log.info(f"  Average Medals: {self.medals_avg}")
        log.info(f"  Decks Used Today: {self.decks_used_today}")
        log.info(f"  Decks Remaining: {self.decks_remaining}")
        log.info(f"  Slots: {self.slots}")


if __name__ == "__main__":

    RoyaleAPI_scraper = ScrapingRoyaleAPI("UURJ9CG", pd.read_csv("data/discord.csv"))

    RoyaleAPI_scraper.get_soup()
        
    RoyaleAPI_scraper.get_clan_data()
    
    RoyaleAPI_scraper.get_players_data()

    RoyaleAPI_scraper.get_players_advanced_stats()

    RoyaleAPI_scraper.df_players_data.to_csv("data/players_advanced_stats.csv")
