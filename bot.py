import discord
import pandas as pd
from royaleapi_scraping_class import ScrapingRoyaleAPI
from discord import app_commands

TOKEN = "MTEzOTk1NTAxOTc4NTk2MTU1Mg.GRziG1.okuLmjskQZ6S9WJLVRcfX-mvFgC6uWkiH_wh4g"
SERVER_ID = 913101617639862362
CLAN_ID = "UURJ9CG"

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print("Logged in as Clash Royale Pinger!")
    
@tree.command(name="correspondances", description="Know which CR player is related to which discord id", guild=discord.Object(id=SERVER_ID))
async def correspondances(ctx):
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
    
    RoyaleAPI_scraper = ScrapingRoyaleAPI("UURJ9CG", df_discord_data)
    
    df_players_data = RoyaleAPI_scraper.run()
    
    df_players_data = df_players_data.astype(str)
    
    embed = discord.Embed(title="Discord & Clash Royale",description="Correspondances", colour=discord.Colour(0x3e038c))

    dico_certainty = {"Confirmed":(1,0.9),"Uncertain":(0.9,0.5),"Bad":(0.5,0)}
    
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
        
    await ctx.response.send_message(embed=embed)

@tree.command(name="attacks", description="Identify GDC players", guild=discord.Object(id=SERVER_ID))
async def attacks(ctx):
    min_ratio = 0.8
    
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
    
    print(df_discord_data)
    
    RoyaleAPI_scraper = ScrapingRoyaleAPI(CLAN_ID, df_discord_data)
    
    df_players_data = RoyaleAPI_scraper.run()
    
    df_players_data = df_players_data.astype(str)
    
    df_players_data.to_csv("data/result.csv")
    
    embed = discord.Embed(title="War | "+str(RoyaleAPI_scraper.day), colour=discord.Colour(0x3e038c))
        
    clan_stats = [
        f"<:sign:913172154269442048> **{RoyaleAPI_scraper.clan_name}**",
        f"<:medals:1017445552859906148> **{RoyaleAPI_scraper.medals}**",
        f"<:decksremaining:1017445543108165713> **{RoyaleAPI_scraper.decks_remaining}**",
        f"<:slots:1017445562779435169> **{RoyaleAPI_scraper.slots}**",
        ]
    
    embed.add_field(name=f"**Remaining Attacks**", value='\n'.join(clan_stats), inline=False)

    for i in reversed(range(0, 3)):
        
        df_i_attacks = df_players_data[df_players_data["decks_used_today"] == str(i)]
        
        if len(df_i_attacks) >= 1:
            
            embed_name = f"**{4-i} Attacks**"
            
            embed_value = ""
            
            for index, row in df_i_attacks.iterrows():
                
                if float(row["match_ratio"]) >= min_ratio:
                    embed_value += f"•{row['cr_name']} <@{row['discord_id']}>\n"
                else:
                    embed_value += f"•{row['cr_name']}\n"
            
            embed.add_field(name=embed_name, value=embed_value, inline=False)
        
    await ctx.response.send_message(embed=embed)
    
client.run(TOKEN)