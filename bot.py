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

ROLES_MAPPING = {
    "leader": "Chef d'État",
    "officer": "Officier",
    "member": "Membre",
    "recruit": "Recrue"
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TCHAD_COUNTRY_ID = None

async def get_tchad_id(session):
    """Récupère l'UUID (country_id) du Tchad sur Jade."""
    global TCHAD_COUNTRY_ID
    if TCHAD_COUNTRY_ID:
        return TCHAD_COUNTRY_ID

    cursor = None
    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        async with session.get(f"{BASE_URL}/countries", params=params) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
            for country in payload.get("data", []):
                if country.get("name", "").lower() == PAYS_CIBLE.lower():
                    TCHAD_COUNTRY_ID = country.get("country_id")
                    return TCHAD_COUNTRY_ID
            page = payload.get("meta", {}).get("page", {})
            if not page.get("has_more"):
                break
            cursor = page.get("next_cursor")
    return None

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user} sur {len(bot.guilds)} serveur(s).')

@bot.command(name="verifier")
async def verifier_joueur(ctx, pseudo: str, membre: discord.Member = None):
    """Vérifie le joueur sur Jade et lui attribue son rôle Discord."""
    cible_discord = membre or ctx.author
    await ctx.send(f"🔍 Vérification de `{pseudo}` en cours...")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        player_url = f"{BASE_URL}/players/{pseudo}"
        async with session.get(player_url) as resp:
            if resp.status == 404:
                await ctx.send(f"❌ Le joueur `{pseudo}` est inconnu sur {SERVER.capitalize()} ou inactif depuis 90 jours.")
                return
            if resp.status == 403:
                await ctx.send(f"🔒 Le profil de `{pseudo}` est privé (`profile_private`). Le joueur doit le passer en public sur le site NG.")
                return
            if resp.status != 200:
                await ctx.send(f"⚠️ Erreur API NationsGlory (Code: {resp.status}).")
                return

            player_data = (await resp.json()).get("data", {})
            exact_username = player_data.get("username", pseudo)
            country_id = player_data.get("country_id")
            role_api = str(player_data.get("role") or "").lower()

            if not country_id:
                await ctx.send(f"❌ `{exact_username}` n'a aucun pays sur {SERVER.capitalize()}.")
                return

        country_url = f"{BASE_URL}/countries/{country_id}"
        async with session.get(country_url) as resp:
            if resp.status != 200:
                await ctx.send("⚠️ Erreur lors de la récupération des détails du pays.")
                return

            country_data = (await resp.json()).get("data", {})
            country_name = country_data.get("name", "")

            if country_name.lower() == PAYS_CIBLE.lower():
                global TCHAD_COUNTRY_ID
                TCHAD_COUNTRY_ID = country_id  # On sauvegarde l'ID au passage

                nom_role_discord = ROLES_MAPPING.get(role_api)
                statut_role = f"Grade API détecté : `{role_api}` (aucun rôle Discord associé)"

                if nom_role_discord:
                    role_discord = discord.utils.get(ctx.guild.roles, name=nom_role_discord)
                    if role_discord:
                        anciens_roles = [r for r in cible_discord.roles if r.name in ROLES_MAPPING.values()]
                        if anciens_roles:
                            await cible_discord.remove_roles(*anciens_roles)
                        await cible_discord.add_roles(role_discord)
                        statut_role = f"✅ Rôle **{nom_role_discord}** attribué à {cible_discord.mention} !"
                    else:
                        statut_role = f"⚠️ Le rôle `{nom_role_discord}` est introuvable sur ce serveur."

                try:
                    if cible_discord != ctx.guild.owner:
                        await cible_discord.edit(nick=exact_username)
                except discord.Forbidden:
                    pass

                bank = country_data.get("bank_balance")
                bank_str = f"{bank:,} $".replace(",", " ") if bank is not None else "Inconnu"

                embed = discord.Embed(
                    title=f"🇹🇩 {exact_username} appartient bien au {country_name} !",
                    description=statut_role,
                    color=0x2ecc71
                )
                embed.add_field(name="Grade IG", value=role_api.upper(), inline=True)
                embed.add_field(name="Membres", value=str(country_data.get("members_count", "?")), inline=True)
                embed.add_field(name="Power", value=f"{country_data.get('power', '?')} / {country_data.get('power_max', '?')}", inline=True)
                embed.add_field(name="Score", value=str(country_data.get("score", "?")), inline=True)
                embed.add_field(name="Banque", value=bank_str, inline=True)

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ `{exact_username}` n'est pas au Tchad. Il appartient actuellement au pays **{country_name}**.")

@bot.command(name="pays")
async def infos_pays(ctx):
    """Affiche les statistiques actuelles du Tchad sur Jade."""
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        country_id = await get_tchad_id(session)
        if not country_id:
            await ctx.send(f"⚠️ Impossible de trouver le pays `{PAYS_CIBLE}` sur {SERVER.capitalize()}.")
            return

        async with session.get(f"{BASE_URL}/countries/{country_id}") as resp:
            if resp.status != 200:
                await ctx.send(f"⚠️ Erreur lors de la lecture de la fiche pays (Code: {resp.status}).")
                return

            data = (await resp.json()).get("data", {})
            bank = data.get("bank_balance")
            bank_str = f"{bank:,} $".replace(",", " ") if bank is not None else "Inconnu"

            embed = discord.Embed(
                title=f"🇹🇩 Tableau de bord : {data.get('name', 'Tchad')} ({SERVER.capitalize()})",
                color=0xf1c40f
            )
            embed.add_field(name="👑 Chef", value=data.get("leader") or "Inconnu", inline=True)
            embed.add_field(name="👥 Membres", value=str(data.get("members_count", "?")), inline=True)
            embed.add_field(name="⚡ Power", value=f"{data.get('power', '?')} / {data.get('power_max', '?')}", inline=True)
            embed.add_field(name="🏆 Score", value=str(data.get("score", "?")), inline=True)
            embed.add_field(name="🗺️ Claims", value=str(data.get("claims", "?")), inline=True)
            embed.add_field(name="🏦 Banque", value=bank_str, inline=True)
            await ctx.send(embed=embed)

@bot.command(name="assaut")
@commands.has_any_role("Chef d'État", "Officier")
async def alerte_assaut(ctx, *, message: str = "Mobilisation générale immédiate !"):
    """Envoie une alerte d'assaut dans #alerte-assaut."""
    salon_alerte = discord.utils.get(ctx.guild.text_channels, name="🚨・alerte-assaut")
    cible = salon_alerte if salon_alerte else ctx.channel

    embed = discord.Embed(
        title="🚨 ALERTE MILITAIRE - MOBILISATION 🚨",
        description=f"**Ordre de {ctx.author.mention} :**\n{message}\n\n👉 Rejoignez immédiatement le vocal **`🔊・Assaut / PvP`** !",
        color=0xe74c3c
    )
    await cible.send(content="@everyone", embed=embed)
    if salon_alerte and cible != ctx.channel:
        await ctx.send(f"✅ Alerte envoyée dans {salon_alerte.mention}.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)