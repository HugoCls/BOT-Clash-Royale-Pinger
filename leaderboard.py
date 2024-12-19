import discord
import pandas as pd
import ast
import json
from datetime import datetime
import logging as log

log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
 
SAVE_TIME_FILE = "data/save_time.json"

def add_day_suffix(day):
    if 10 <= day <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return str(day) + suffix


def generate_leaderboard(df_players_data, last_n_weeks=5):
    # Calculer les moyennes pour chaque joueur
    leaderboard_data = []
    
    for player_index in df_players_data.index:
        cr_id = df_players_data.at[player_index, "cr_id"]
        cr_name = df_players_data.at[player_index, "cr_name"]
        
        j = last_n_weeks if last_n_weeks <= len(df_players_data.at[player_index, "cw_last_scores"]) - 1 else -1
           
        player_data = ast.literal_eval(df_players_data.at[player_index, "cw_last_scores"])[:j]

        # Convertir la liste de dictionnaires en un DataFrame pour calculer les moyennes
        player_data_df = pd.DataFrame(player_data)

        # Calcul des moyennes avec arrondi à 2 décimales
        avg_contribution = round(player_data_df['contribution'].mean(), 2)
        avg_decks_used = round(player_data_df['decks_used'].mean(), 5)
        avg_clan_rank = round(player_data_df['clan_rank'].mean(), 1)
        
        log.info(cr_name)
        log.info(player_data_df)

        leaderboard_data.append({
            'cr_id': cr_id,
            'cr_name': cr_name,
            'avg_contribution': avg_contribution,
            'avg_decks_used': avg_decks_used
        })
    
    # Trier le leaderboard par la meilleure moyenne de contribution (en ordre décroissant)
    leaderboard_data.sort(key=lambda x: x['avg_contribution'], reverse=True)
    
    embeds = []

    # Créer le leaderboard pour Discord
    embed = discord.Embed(title=f"Leaderboard GDC (last {last_n_weeks} weeks)", colour=discord.Colour(0x3e038c))
    
    # Ajouter les résultats sous forme de champs
    embed_value = ""
    for data in leaderboard_data:
        
        avg_decks_used = data['avg_decks_used']

        if float(avg_decks_used) == 16:
            avg_decks_used = "16"
        else:
            avg_decks_used = str(round(avg_decks_used, 1))

        text = f":medal:{round(data['avg_contribution'])} | {avg_decks_used} **{data['cr_name']}**\n"

        if len(embed_value) + len(text) >= 980:
            embed.add_field(name="", value=embed_value, inline=False)
            embeds.append(embed)
            embed = discord.Embed(colour=discord.Colour(0x3e038c))
            embed_value = ""

        embed_value += text
    
    embed.add_field(name="", value=embed_value, inline=False)
    embeds.append(embed)
    return embeds


def get_missed_attacks_logs(df_players_data, last_n_weeks=5):
    all_player_data = []

    for player_index in df_players_data.index:
        cr_id = df_players_data.at[player_index, "cr_id"]
        cr_name = df_players_data.at[player_index, "cr_name"]
        
        # Récupérer la liste des dictionnaires à partir de la colonne "cw_last_scores"
        player_data = ast.literal_eval(df_players_data.at[player_index, "cw_last_scores"])
        player_data_df = pd.DataFrame(player_data)
        
        # Ajouter les colonnes `cr_id` et `cr_name` à chaque DataFrame
        player_data_df['cr_id'] = cr_id
        player_data_df['cr_name'] = cr_name
        
        # Ajouter le DataFrame au tableau principal
        all_player_data.append(player_data_df)

    final_df = pd.concat(all_player_data, ignore_index=True)
    final_df['log_date'] = pd.to_datetime(final_df['log_date'], format='%Y-%m-%d')

    # Trier le DataFrame par 'log_date' dans l'ordre décroissant
    final_df_sorted = final_df.sort_values(by='log_date', ascending=False)

    j = last_n_weeks if last_n_weeks <= len(final_df_sorted['log_date'].unique()) - 1 else -1
    
    dates = final_df_sorted['log_date'].unique()[:j]

    embeds = []
    
    try:
        with open(SAVE_TIME_FILE, 'r') as f:
            data = json.load(f)
            save_time = data.get("last_save_time", 0)  # Utiliser 0 si "last_save_time" est absent
    except (FileNotFoundError, json.JSONDecodeError):
        save_time = 0
        
        with open(SAVE_TIME_FILE, 'w') as f:
            json.dump({"last_save_time": save_time}, f)

    last_update = datetime.utcfromtimestamp(save_time).strftime('%Y-%m-%d %H:%M:%S')
    
    # Créer le leaderboard pour Discord
    embed = discord.Embed(title=f"Oublis en GDC (last {last_n_weeks} weeks)", colour=discord.Colour(0xf54242))
    embed.add_field(name="Data last updated:", value=last_update, inline=True)
    
    def choose_smile(forgotten_battles):
        if forgotten_battles <= 1:
            return "<:2222:913184619145334784>"
        elif forgotten_battles <= 3:
            return "<:123:913184574299856927>"
        else:
            return "<:111111:913173397079482378>"

        
    for i, date in enumerate(dates):
        embed_value = ""

        df_oublis = final_df_sorted.loc[(final_df_sorted["log_date"] == date) & (final_df_sorted["decks_used"] != 16), ["cr_name", "decks_used"]]

        df_oublis["forgotten_battles"] = 16 - df_oublis["decks_used"]
        
        df_oublis = df_oublis.sort_values(by='forgotten_battles', ascending=False)

        for index in df_oublis.index:
            cr_name = df_oublis.at[index, "cr_name"]
            forgotten_battles = df_oublis.at[index, "forgotten_battles"]

            text = f"{choose_smile(forgotten_battles)} {forgotten_battles} **{cr_name}** \n"
            
            embed_value += text

        if i != len(dates) - 1:
            embed_value += "--------\n"

        embed.add_field(name=f"{date.strftime('%b')} {add_day_suffix(date.day)}", value=f"{embed_value}\n", inline=False)


    
    embeds.append(embed)
    return embeds