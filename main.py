import discord
from discord.ext import commands
import requests
import asyncio
import aiosqlite
import os

import sqlite_Leaderboard

from dotenv import load_dotenv

load_dotenv()
client = commands.Bot(command_prefix='?', intents=discord.Intents.all())
client.remove_command('help')

TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("RIOT_API_KEY")


@client.event
async def on_ready():
    print("Bot is ready.")
    sqlite_Leaderboard.create_db()


# get player rank
@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def rank(ctx, region, username):
    if not username.isalnum() or not region.isalnum():
        await ctx.send("Invalid username or region.")
        return
    response = requests.get(
        f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{username}?api_key={API_KEY}")
    if response.status_code == 200:
        data = response.json()
        level = data["summonerLevel"]
        # Get the player's rank from the response JSON
        summoner_id = response.json()["id"]
        response = requests.get(
            f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={API_KEY}")
        if response.status_code == 200:
            for entry in response.json():
                queatype = entry["queueType"]
            if queatype == "RANKED_SOLO_5x5":
                Rank = entry["tier"] + " " + entry["rank"]
                LP = entry["leaguePoints"]
                wins_losses = str(entry["wins"]) + "/" + str(entry["losses"])

                embed = discord.Embed(title=f"Rank for {username} lvl: {level}", color=discord.Color.blue())
                embed.add_field(name="Type", value=queatype, inline=True)
                embed.add_field(name="Rank", value=Rank, inline=True)
                embed.add_field(name="LP", value=LP, inline=True)
                embed.add_field(name="Wins/Losses", value=wins_losses, inline=True)
                await ctx.send(embed=embed)

    else:
        await ctx.send(f"> Failed to get details for player {username}")


# get player matches history
@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def matches(ctx, region, username):
    summoner = ""
    if not username.isalnum() or not region.isalnum():
        await ctx.send("Invalid username or region.")
        return
    response = requests.get(
        f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{username}?api_key={API_KEY}")
    if response.status_code == 200:
        # Get the player's matches from the response JSON
        summoner_puuid = response.json()["puuid"]
        if region == "euw1":
            region = "europe"
        else:
            region = "americas"
        response = requests.get(
            f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{summoner_puuid}/ids?start=0&count=10"
            f"&api_key={API_KEY}")
        if response.status_code == 200:
            match_ids = response.json()
            index = 0
            while True:
                match_id = match_ids[index]
                response = requests.get(
                    f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}")
                if response.status_code == 200:
                    for participant in response.json()["info"]["participants"]:
                        if participant["puuid"] == summoner_puuid:
                            summoner = participant
                            break
                else:
                    await ctx.send("Failed to get match details.")
                    return

                # Display match stats
                embed = discord.Embed(title=f"Match {index + 1}", color=discord.Color.green())
                embed.add_field(name="Champion", value=summoner["championName"], inline=True)
                embed.add_field(name="Kills", value=summoner["kills"], inline=True)
                embed.add_field(name="Deaths", value=summoner["deaths"], inline=True)
                embed.add_field(name="Assists", value=summoner["assists"], inline=True)
                embed.add_field(name="Damage Dealt", value=summoner["totalDamageDealtToChampions"], inline=True)
                embed.add_field(name="Win", value=summoner["win"], inline=True)

                message = await ctx.send(embed=embed)

                # Add reactions to allow the user to navigate between matches
                if index == 0:
                    await message.add_reaction("➡️")
                elif index == len(match_ids) - 1:
                    await message.add_reaction("⬅️")
                else:
                    await message.add_reaction("⬅️")
                    await message.add_reaction("➡️")

                # Wait for user input
                try:
                    reaction, user = await client.wait_for("reaction_add", timeout=30.0,
                                                           check=lambda reaction, user: user == ctx.author and
                                                                                        reaction.message.id == message.id and
                                                                                        reaction.emoji in ["⬅️", "➡️"])
                except asyncio.TimeoutError:
                    await message.clear_reactions()
                    return

                # Remove the user's reaction
                await message.remove_reaction(reaction, user)

                # Navigate to the next/previous match or exit the menu
                if reaction.emoji == "➡️":
                    index += 1
                    # delete
                    await message.delete()
                elif reaction.emoji == "⬅️":
                    index -= 1
                    # delete
                    await message.delete()
                else:
                    await message.clear_reactions()
                    return


# add player to leaderboard
@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def add(ctx, region, username):
    valid_regions = ["na1", "euw1"]
    guildID = ctx.message.guild.id
    if region.lower() not in valid_regions:
        await ctx.send("Invalid region. Please choose one of the following regions: na1, euw1")
        return

    # Check if the username is valid
    if not username.isalnum():
        await ctx.send("Invalid username. Please enter a username containing only letters and numbers.")
        return


# remove player from leaderboard
@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def remove(ctx, username):
    guildID = ctx.message.guild.id


# print leaderboard
@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def lb(ctx):
    guildID = ctx.message.guild.id


# create leaderboard table
@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def create_lb(ctx):
    guildID = ctx.message.guild.id


# clear leaderboard table
@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def clear_lb(ctx):
    guildID = ctx.message.guild.id


# Help
@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def help(ctx):
    help_embed = discord.Embed(title="Help", color=discord.Color.dark_gold())

    help_embed.set_author(name="League of Legends Discord Bot")
    help_embed.add_field(name="!rank [region] [username]", value="Get the rank of a player.", inline=False)
    help_embed.add_field(name="!matches [region] [username]", value="Get the last 10 matches of a player.",
                         inline=False)
    help_embed.add_field(name="!add [region] [username]", value="Add a player to the leaderboard.", inline=False)
    help_embed.add_field(name="!remove [username]", value="Remove a player from the leaderboard.", inline=False)
    help_embed.add_field(name="!lb", value="Print the leaderboard.", inline=False)
    help_embed.set_footer(text="Created by @Bayms.")

    await ctx.send(embed=help_embed)


# Error handling
@client.event
async def Wait_time(ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(f"Please wait {error.retry_after:.0f} seconds before using this command again.")
    else:
        raise error


client.run(TOKEN)
