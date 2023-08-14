from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
import Levenshtein
    
def calculate_match_percentage(name1, name2):
    max_length = max(len(name1), len(name2))
    distance = Levenshtein.distance(name1, name2)
    similarity = 1 - (distance / max_length)
    return round(similarity, 3)

class ScrapingRoyaleAPI:
    def __init__(self, clan_id, df_discord_data):
        
        self.session=HTMLSession()
        
        self.clan_id = clan_id
        
        self.df_discord_data = df_discord_data
        
    def run(self):

        self.get_soup()
        
        self.get_clan_data()
        
        self.get_players_data()

        self.get_players_discords_matches()
        
        return(self.df_players_data)
    
    def get_soup(self):
        
        r = self.session.get(f'https://royaleapi.com/clan/{self.clan_id}/war/race')
        
        text = r.text
        
        self.soup = BeautifulSoup(text,'html.parser')
     
    def get_clan_data(self):
        
        self.day = self.soup.find_all('div',class_="day")[0].get_text().strip('\n')
        
        self.medals = self.soup.select("#page_content > div.ui.attached.container.sidemargin0.content_container > div:nth-child(2) > div > a.clan.row.active_clan > div.outline.cw2__standing_outline > div.item.value.medal")[0].text.strip('\n')[2:].strip('-')
        
        self.medals_avg = self.soup.select("#page_content > div.ui.attached.container.sidemargin0.content_container > div:nth-child(2) > div > a.clan.row.active_clan > div.outline.cw2__standing_outline > div.item.value.medal_avg")[0].text.strip('\n')
        
        self.decks_used_today = self.soup.select("#page_content > div.ui.attached.container.sidemargin0.content_container > div:nth-child(2) > div > a.clan.row.active_clan > div.outline.cw2__standing_outline > div.item.value.decks_used_today")[0].text.strip('\n')
       
        [nb_decks_used,nb_decks_max] = self.decks_used_today.replace(' ','').split('/')

        self.decks_remaining = int(nb_decks_max) - int(nb_decks_used)
        
        self.clan_name = self.soup.select('#page_content > div:nth-child(5) > div.ui.attached.padded.segment > div.p_header_container > div:nth-child(1) > h1')[0].text.strip('\n')
           
    def get_players_data(self):
        
        self.df_players_data = pd.DataFrame(columns=["cr_id","cr_name","player_role","decks_used_today","decks_used","boat_attacks","fame","discord_name","discord_id","match_ratio"])
        
        players = self.soup.find_all('td',class_="player_name")
        
        for player in players:
            
            cr_id = '#'+player.find_all('a',href=True)[0]['href'].strip('/player/').strip('/battles')
            
            name = player.find_all('a',class_='player_name force_single_line_hidden')[0].get_text().strip('\n')
            
            player_role = player.find_all('div',class_='player_role')[0].get_text().strip('\n')

            decks_used_today = player.find_all('div',class_='value_bg decks_used_today')[0].get_text().strip('\n')
            
            decks_used = player.find_all('div',class_='value_bg decks_used')[0].get_text().strip('\n')
            
            boat_attacks = player.find_all('div',class_='value_bg boat_attacks')[0].get_text().strip('\n')
            
            fame = player.find_all('div',class_='value_bg fame')[0].get_text().strip('\n')
            
            if player_role != "--":
                
                player_dict = {
                    "cr_id":[cr_id],
                    "cr_name":[name],
                    "player_role":[player_role],
                    "decks_used_today":[decks_used_today],
                    "decks_used":[decks_used],
                    "boat_attacks":[boat_attacks],
                    "fame":[fame],
                }
                
                self.df_players_data = pd.concat([self.df_players_data, pd.DataFrame.from_dict(player_dict)], ignore_index=True)

        self.slots = len(self.df_players_data[self.df_players_data['decks_used_today'] == 0])

    def get_players_discords_matches(self):
        
        print("Determining which discord ids are the best for these pseudos")

        for index, player_row in self.df_players_data.iterrows():
            cr_name = player_row["cr_name"]
            best_match_name = ""
            best_match_disc_id = ""
            best_match_ratio = 0

            for index, discord_row in self.df_discord_data.iterrows():
                
                disc_name = discord_row["discord_name"]
                disc_id = discord_row["discord_id"]
                
                ratio = calculate_match_percentage(cr_name, disc_name)
                
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
                    best_match_disc_name = disc_name
                    best_match_disc_id = disc_id
            
            player_row["discord_name"] = best_match_disc_name
            player_row["discord_id"] = best_match_disc_id 
            player_row["match_ratio"] = best_match_ratio