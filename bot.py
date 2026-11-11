import os
import discord
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("NG_API_KEY")

SERVER = "jade"
PAYS_CIBLE = "tchad"
BASE_URL = f"https://publicapi.nationsglory.fr/v1/servers/{SERVER}"
HEADERS = {"X-API-Key": API_KEY}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.command(name="verifier")
async def verifier_joueur(ctx, pseudo: str):
    """Vérifie si un joueur fait partie du Tchad sur Jade."""
    await ctx.send(f"Vérification de `{pseudo}` en cours...")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        player_url = f"{BASE_URL}/players/{pseudo}"
        async with session.get(player_url) as resp:
            if resp.status == 404:
                await ctx.send(f"Le joueur `{pseudo}` est inconnu sur {SERVER.capitalize()} ou inactif depuis 90 jours.")
                return
            if resp.status == 403:
                await ctx.send(f"Le profil de `{pseudo}` est privé. Impossible d'accéder aux informations.")
                return
            if resp.status != 200:
                await ctx.send(f"Erreur API NationsGlory (Code: {resp.status}).")
                return

            player_data = (await resp.json()).get("data", {})
            country_id = player_data.get("country_id")
            role = player_data.get("role")

            if not country_id:
                await ctx.send(f"`{pseudo}` n'a aucun pays sur Jade.")
                return

        country_url = f"{BASE_URL}/countries/{country_id}"
        async with session.get(country_url) as resp:
            if resp.status != 200:
                await ctx.send("Erreur lors de la récupération des détails du pays.")
                return

            country_data = (await resp.json()).get("data", {})
            country_name = country_data.get("name")

            if country_name.lower() == PAYS_CIBLE.lower():
                power = country_data.get("power")
                score = country_data.get("score")
                bank = country_data.get("bank_balance")
                members = country_data.get("members_count")

                embed = discord.Embed(
                    title=f"{pseudo} appartient bien au {country_name} !",
                    color=0x2ecc71
                )
                embed.add_field(name="Grade", value=role, inline=False)
                embed.add_field(name="Membres du pays", value=str(members), inline=True)
                embed.add_field(name="Power du pays", value=str(power), inline=True)
                embed.add_field(name="Score du pays", value=str(score), inline=True)
                embed.add_field(name="Solde Banque", value=f"{bank} $", inline=True)

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"`{pseudo}` n'est pas au Tchad. Il appartient actuellement au pays **{country_name}**.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)