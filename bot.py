import discord
import pandas as pd
from royaleapi_scraping_class import ScrapingRoyaleAPI
from leaderboard import generate_leaderboard, get_missed_attacks_logs
from discord import app_commands
import os
import time
import json
import logging as log
from dotenv import load_dotenv

load_dotenv()

log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

last_save_time = None

TOKEN = os.getenv("TOKEN")
SERVER_ID = int(os.getenv("SERVER_ID"))
CLAN_ID = os.getenv("CLAN_ID")
MIN_RATIO = os.getenv("MIN_RATIO")
SAVE_TIME_FILE = "data/save_time.json"

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def get_last_save_time():
    """
    Lit le fichier `save_time.json` pour obtenir l'heure du dernier enregistrement des données.

    Retourne :
        - last_save_time (float): Heure de la dernière sauvegarde sous forme de timestamp.
    """
    try:
        with open(SAVE_TIME_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_save_time", None)
    except FileNotFoundError:
        return None

def save_last_save_time(current_time):
    """
    Sauvegarde l'heure actuelle dans le fichier `save_time.json` pour référence future.
    
    Arguments :
        - current_time (float): L'heure actuelle sous forme de timestamp.
    """
    with open(SAVE_TIME_FILE, "w") as f:
        json.dump({"last_save_time": current_time}, f)


def save_discord_data(client):
    """
    Sauvegarde les données des membres Discord dans un fichier CSV.

    Effectue un scan actif des membres du serveur Discord et récupère les informations nécessaires.

    Arguments :
        - client (discord.Client): Instance du client Discord.

    Retourne :
        - df_discord_data (pandas.DataFrame): DataFrame contenant les données des membres Discord.
    """
    log.info("Saving discord data")
    guild = client.get_guild(SERVER_ID)
    members = guild.members

    user_info = []
    
    for member in members:
        user_info.append({
            "name": member.name,
            "discord_id": member.id,
            "nickname": member.nick,
            "global_name": member.global_name,
            "discord_name": member.nick or member.global_name or member.name,
        })
    
    df_discord_data = pd.DataFrame(user_info)

    df_discord_data.to_csv("data/discord.csv")

    return df_discord_data


def save_cr_data():
    """
    Sauvegarde les données de Clash Royale des joueurs dans un fichier CSV.

    Effectue un scan actif des données de clan et des joueurs à partir de RoyaleAPI.

    Retourne :
        - RoyaleAPI_scraper (ScrapingRoyaleAPI): Instance de la classe `ScrapingRoyaleAPI` utilisée pour l'extraction des données.
    """
    log.info("Saving deep cr_data")
    RoyaleAPI_scraper = ScrapingRoyaleAPI("UURJ9CG", pd.read_csv("data/discord.csv"))

    RoyaleAPI_scraper.get_soup()
        
    RoyaleAPI_scraper.get_clan_data()
    
    RoyaleAPI_scraper.get_players_data()
    
    RoyaleAPI_scraper.get_players_discords_matches()

    RoyaleAPI_scraper.df_players_data.to_csv("data/players_stats.csv")

    return RoyaleAPI_scraper


def save_deep_cr_data():
    """
    Sauvegarde des données de Clash Royale des joueurs de manière approfondie dans un fichier CSV.

    Effectue un scan actif des données de clan, des joueurs et des statistiques avancées via RoyaleAPI.

    Retourne :
        - df_players_data (pandas.DataFrame): DataFrame contenant les données des joueurs extraites.
    """
    log.info("Saving deep cr_data")
    RoyaleAPI_scraper = ScrapingRoyaleAPI("UURJ9CG", pd.read_csv("data/discord.csv"))

    RoyaleAPI_scraper.get_soup()
        
    RoyaleAPI_scraper.get_clan_data()
    
    RoyaleAPI_scraper.get_players_data()

    RoyaleAPI_scraper.get_players_advanced_stats()

    RoyaleAPI_scraper.df_players_data.to_csv("data/players_stats.csv")

    return RoyaleAPI_scraper.df_players_data


@client.event
async def on_ready():
    """
    Gère l'événement lorsque le bot se connecte à Discord.

    Synchronise les commandes avec le serveur et enregistre un message de connexion dans les logs.
    """
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    log.info("Logged in as Clash Royale Pinger!")


@tree.command(name="save_data", description="Save all needed data for other functions", guild=discord.Object(id=SERVER_ID))
async def save_data(ctx):
    """
    Sauvegarde toutes les données nécessaires pour d'autres fonctions du bot.

    Type : ACTIVE (cr+discord)
    
    Arguments :
        - ctx (discord.Interaction): L'interaction qui a déclenché la commande.

    Retourne :
        - Un message de confirmation dans Discord si les données ont été sauvegardées avec succès, 
          ou un message d'attente si une sauvegarde a eu lieu récemment.
    """
    await ctx.response.defer()

    current_time = time.time()
    last_save_time = get_last_save_time()

    if last_save_time is not None and current_time - last_save_time < 300:
        remaining_time = 300 - (current_time - last_save_time)
        minutes, seconds = divmod(int(remaining_time), 60)
        await ctx.followup.send(content=f"Please wait {minutes} minute(s) and {seconds} second(s) before saving the data again.")
        return

    try:
        save_discord_data(client)
        save_deep_cr_data()
        save_last_save_time(current_time)
    except:
        log.info("Something went wrong")

    await ctx.followup.send(content="Data saved!")


@tree.command(name="correspondances", description="Know which CR player is related to which discord id", guild=discord.Object(id=SERVER_ID))
async def correspondances(ctx):
    """
    Affiche les correspondances entre les joueurs de Clash Royale et leurs IDs Discord.

    Type : ACTIVE (cr+discord)

    Arguments :
        - ctx (discord.Interaction): L'interaction qui a déclenché la commande.

    Retourne :
        - Un embed Discord affichant les correspondances avec un ratio de correspondance.
    """
    await ctx.response.defer()
    
    df_discord_data = save_discord_data(client)
    
    RoyaleAPI_Scraper = save_cr_data()

    df_players_data = RoyaleAPI_Scraper.df_players_data
    
    df_players_data = df_players_data.astype(str)
    
    embed = discord.Embed(title="Discord & Clash Royale",description="Correspondances", colour=discord.Colour(0x3e038c))

    dico_certainty = {"Uncertain":(0.9,0.5),"Bad":(0.5,0)}
    
    for certainty in dico_certainty.keys():
        
        (x_max, x_min) = dico_certainty[certainty]
        
        df_players_data["match_ratio"] = df_players_data["match_ratio"].astype(float)
        
        df_certainty = df_players_data.query(f'{x_max} >= match_ratio > {x_min}').sort_values(by='match_ratio', ascending=False)
        
        if len(df_certainty) >= 1:
            
            embed_name = f"**{certainty}**"
            
            embed_value = ""
            
            for index, row in df_certainty.iterrows():
                
                embed_value += f"•{row['cr_name']} <@{row['discord_id']}> {row['match_ratio']}\n"
            
            embed.add_field(name=embed_name, value=embed_value, inline=False)
        
    await ctx.followup.send(embed=embed)


@tree.command(name="leaderboard", description="Shows clan leaderboard", guild=discord.Object(id=SERVER_ID))
@app_commands.describe(last_n_weeks="Number of weeks to include in the leaderboard")  
async def leaderboard(ctx, last_n_weeks: int):
    """
    Affiche le leaderboard des joueurs de Clash Royale du clan.

    Type : PASSIVE (cr)

    Arguments :
        - ctx (discord.Interaction): L'interaction qui a déclenché la commande.
        - last_n_weeks (int): Nombre de semaines à inclure dans le leaderboard.

    Retourne :
        - Un ou plusieurs embeds Discord contenant le leaderboard des joueurs.
    """
    await ctx.response.defer()

    df_players_data = pd.read_csv('data/players_advanced_stats.csv')

    embeds = generate_leaderboard(df_players_data, last_n_weeks)

    for embed in embeds:
        await ctx.followup.send(embed=embed)


@tree.command(name="oublis", description="Shows forgotten battles from players in clan wars", guild=discord.Object(id=SERVER_ID))
@app_commands.describe(last_n_weeks="Number of weeks to include in the logs")  
async def oublis(ctx, last_n_weeks: int):
    """
    Affiche les batailles oubliées des joueurs dans les guerres de clan.

    Type : PASSIVE (cr)

    Arguments :
        - ctx (discord.Interaction): L'interaction qui a déclenché la commande.
        - last_n_weeks (int): Nombre de semaines à inclure dans les logs.

    Retourne :
        - Un ou plusieurs embeds Discord affichant les batailles oubliées.
    """
    await ctx.response.defer()

    df_players_data = pd.read_csv('data/players_advanced_stats.csv')

    embeds = get_missed_attacks_logs(df_players_data, last_n_weeks)

    for embed in embeds:
        await ctx.followup.send(embed=embed)


@tree.command(name="attacks", description="Identify GDC players", guild=discord.Object(id=SERVER_ID))
async def attacks(ctx):
    """
    Identifie les joueurs du clan qui ont des attaques restantes dans le cadre de la guerre de clans.

    Type : ACTIVE (cr+discord)
    
    Arguments :
        - ctx (discord.Interaction): L'interaction qui a déclenché la commande.

    Retourne :
        - Un embed Discord affichant les joueurs avec les attaques restantes.
    """
    await ctx.response.defer()

    df_discord_data = save_discord_data(client)  

    RoyaleAPI_scraper = save_cr_data()
    
    df_players_data = RoyaleAPI_scraper.df_players_data
    
    embed = discord.Embed(title="War | "+str(RoyaleAPI_scraper.day), colour=discord.Colour(0x3e038c))
        
    clan_stats = [
        f"<:sign:913172154269442048> **{RoyaleAPI_scraper.clan_name}**",
        f"<:medals:1017445552859906148> **{RoyaleAPI_scraper.medals}**",
        f"<:decksremaining:1017445543108165713> **{RoyaleAPI_scraper.decks_remaining}**",
        f"<:slots:1017445562779435169> **{RoyaleAPI_scraper.slots}**",
        ]
    
    embed.add_field(name=f"**Remaining Attacks**", value='\n'.join(clan_stats), inline=False)
    
    for i in range(4):
        
        df_i_attacks = df_players_data[df_players_data["decks_used_today"] == str(i)]
        
        if len(df_i_attacks) >= 1:
            
            embed_name = f"**{4-i} Attacks**"
            
            embed_value = ""
            
            for index, row in df_i_attacks.iterrows():
                
                if float(row["match_ratio"]) >= float(MIN_RATIO):
                    embed_value += f"•{row['cr_name']} <@{row['discord_id']}>\n"
                else:
                    embed_value += f"•{row['cr_name']}\n"
            
            embed.add_field(name=embed_name, value=embed_value, inline=False)
        
    await ctx.followup.send(embed=embed)

client.run(TOKEN)
