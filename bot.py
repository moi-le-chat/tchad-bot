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
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

ROLES_MAPPING = {
    "leader": "Chef d'État",
    "officer": "Officier du Pays",
    "member": "Citoyen",
    "recruit": "Recrue"
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
TCHAD_COUNTRY_ID = None

@bot.event
async def on_ready():
    print(f'✅ Bot connecté en tant que {bot.user} sur {len(bot.guilds)} serveur(s).')
    await bot.change_presence(activity=discord.Game(name="NationsGlory Jade | !aide"))

@bot.command(name="aide")
async def menu_aide(ctx):
    """Affiche toutes les commandes disponibles du bot."""
    embed = discord.Embed(
        title="🇹🇩 Commandes du Bot Officiel du Tchad",
        description="Voici la liste des commandes utilisables sur le serveur :",
        color=0xf1c40f
    )
    embed.add_field(
        name="🌍 Infos & NationsGlory",
        value="`!drapeau` : Affiche le drapeau du Tchad en jeu\n`!forum` : Dernières annonces officielles NG\n`!pays` : Stats du pays *(nécessite clé API)*\n`!verifier <pseudo>` : Vérifie un joueur et donne son rôle *(nécessite clé API)*",
        inline=False
    )
    embed.add_field(
        name="🛠️ Vie du Pays (Membres & Staff)",
        value="`!sondage <question>` : Lance un vote 👍/👎\n`!don @membre <contenu>` : Enregistre un don dans `#banque-et-dons`",
        inline=False
    )
    embed.add_field(
        name="🛡️ État-Major (Chef & Officiers)",
        value="`!objectif <titre> | <détails>` : Poste un objectif de farm/build\n`!notation <note> <rang> [remarque]` : Publie la notation du dimanche\n`!assaut [message]` : Lance une alerte `@everyone` militaire\n`!convoc @membre [raison]` : Convoque un joueur en MP et en vocal\n`!clear <nombre>` : Supprime des messages",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="drapeau")
async def afficher_drapeau(ctx):
    """Affiche le drapeau officiel du Tchad sur Jade (sans clé API)."""
    url = f"https://publicapi.nationsglory.fr/v1/servers/{SERVER}/flags"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("⚠️ Impossible de récupérer les drapeaux pour le moment.")
                return
            flags = (await resp.json()).get("data", {}).get("flags", {})
            flag_url = next((v for k, v in flags.items() if k.lower() == PAYS_CIBLE.lower()), None)
            
            if flag_url:
                embed = discord.Embed(title="🇹🇩 Drapeau officiel du Tchad (Jade)", color=0xf1c40f)
                embed.set_image(url=flag_url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Aucun drapeau enregistré en jeu pour le Tchad.")

@bot.command(name="forum")
async def annonces_forum(ctx):
    """Affiche les 3 dernières annonces du forum officiel NationsGlory (sans clé API)."""
    url = "https://publicapi.nationsglory.fr/v1/forum/categories/12/feed.rss?format=json&limit=3"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await ctx.send("⚠️ Impossible de lire le forum NationsGlory.")
                return
            threads = (await resp.json()).get("data", {}).get("threads", [])
            if not threads:
                await ctx.send("Aucune annonce récente trouvée.")
                return

            embed = discord.Embed(
                title="📰 Dernières Annonces Officielles NationsGlory",
                color=0x3498db
            )
            for t in threads:
                auteur = t.get("author") or "Staff NG"
                embed.add_field(
                    name=f"📌 {t.get('title')}",
                    value=f"Par **{auteur}** • [Lire sur le forum]({t.get('url')})",
                    inline=False
                )
            await ctx.send(embed=embed)

@bot.command(name="sondage")
async def creer_sondage(ctx, *, question: str):
    """Crée un sondage rapide avec réactions."""
    embed = discord.Embed(
        title="📊 SONDAGE DU PAYS",
        description=f"**{question}**\n\nVotez avec les réactions ci-dessous :",
        color=0x9b59b6
    )
    embed.set_footer(text=f"Proposé par {ctx.author.display_name}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await msg.add_reaction("🤷")

@bot.command(name="don")
@commands.has_any_role("Chef d'État", "Officier du Pays")
async def enregistrer_don(ctx, membre: discord.Member, *, contenu: str):
    """Enregistre un don dans #banque-et-dons."""
    salon = discord.utils.get(ctx.guild.text_channels, name="🏦・banque-et-dons")
    cible = salon if salon else ctx.channel

    embed = discord.Embed(
        title="💰 NOUVEAU DON AU PAYS",
        description=f"Merci à {membre.mention} pour sa contribution au développement du **Tchad** !",
        color=0x2ecc71
    )
    embed.add_field(name="📦 Contribution", value=contenu, inline=False)
    embed.set_footer(text=f"Validé par {ctx.author.display_name}")

    await cible.send(embed=embed)
    if salon and cible != ctx.channel:
        await ctx.send(f"✅ Don de {membre.display_name} enregistré dans {salon.mention}.")

@bot.command(name="objectif")
@commands.has_any_role("Chef d'État", "Officier du Pays")
async def poster_objectif(ctx, *, texte: str):
    """Poste un objectif de farm/build (Format: !objectif Titre | Description)."""
    if "|" in texte:
        titre, desc = [part.strip() for part in texte.split("|", 1)]
    else:
        titre, desc = "Objectif du Pays", texte

    salon = discord.utils.get(ctx.guild.text_channels, name="🏗️・builds-et-farm")
    cible = salon if salon else ctx.channel

    embed = discord.Embed(
        title=f"🏗️ OBJECTIF : {titre.upper()}",
        description=f"{desc}\n\n*Réagissez avec ✅ quand vous participez ou que c'est terminé !*",
        color=0xe67e22
    )
    embed.set_footer(text=f"Assigné par {ctx.author.display_name}")

    msg = await cible.send(embed=embed)
    await msg.add_reaction("✅")
    if salon and cible != ctx.channel:
        await ctx.send(f"✅ Objectif publié dans {salon.mention}.")

@bot.command(name="notation")
@commands.has_any_role("Chef d'État", "Officier du Pays")
async def publier_notation(ctx, note: str, classement: str, *, remarque: str = "Continuez comme ça !"):
    """Publie le résultat de la notation du dimanche dans #notation."""
    salon = discord.utils.get(ctx.guild.text_channels, name="📈・notation")
    cible = salon if salon else ctx.channel

    embed = discord.Embed(
        title="📈 RÉSULTATS DE LA NOTATION HEBDOMADAIRE",
        description=f"Bilan de la semaine pour le **Tchad** sur **{SERVER.capitalize()}** :",
        color=0x3498db
    )
    embed.add_field(name="⭐ Note obtenue", value=f"**{note}**", inline=True)
    embed.add_field(name="🏆 Classement", value=f"**{classement}**", inline=True)
    embed.add_field(name="📝 Mot de l'État-Major", value=remarque, inline=False)
    embed.set_footer(text=f"Publié par {ctx.author.display_name}")

    await cible.send(embed=embed)
    if salon and cible != ctx.channel:
        await ctx.send(f"✅ Résultats publiés dans {salon.mention}.")

@bot.command(name="assaut")
@commands.has_any_role("Chef d'État", "Officier du Pays")
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

@bot.command(name="convoc")
@commands.has_any_role("Chef d'État", "Officier du Pays")
async def convoquer_membre(ctx, membre: discord.Member, *, raison: str = "Entretien avec l'État-Major"):
    """Envoie un MP de convocation et déplace le joueur en vocal s'il est connecté."""
    try:
        await membre.send(f"📩 **Convocation officielle du Tchad :**\nTu es attendu par {ctx.author.mention} dans le salon vocal **`🔊・Convocation Staff`**.\n**Motif :** {raison}")
        mp_statut = "MP envoyé"
    except discord.Forbidden:
        mp_statut = "MP bloqués par le joueur"

    vocal_statut = "joueur non connecté en vocal"
    if membre.voice and membre.voice.channel:
        salon_convoc = discord.utils.get(ctx.guild.voice_channels, name="🔊・Convocation Staff")
        if salon_convoc:
            try:
                await membre.move_to(salon_convoc)
                vocal_statut = f"déplacé dans {salon_convoc.name}"
            except discord.Forbidden:
                vocal_statut = "permission vocale manquante"

    await ctx.send(f"📢 Convocation lancée pour {membre.mention} ({mp_statut}, {vocal_statut}).")

@bot.command(name="clear")
@commands.has_any_role("Chef d'État", "Officier du Pays")
async def nettoyer_messages(ctx, nombre: int = 5):
    """Supprime un nombre donné de messages dans le salon."""
    if nombre < 1 or nombre > 50:
        await ctx.send("⚠️ Choisis un nombre entre 1 et 50.")
        return
    await ctx.channel.purge(limit=nombre + 1)
    msg = await ctx.send(f"🧹 {nombre} message(s) supprimé(s).")
    await msg.delete(delay=3)

async def get_tchad_id(session):
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

@bot.command(name="verifier")
async def verifier_joueur(ctx, pseudo: str, membre: discord.Member = None):
    """Vérifie le joueur sur Jade et lui attribue son rôle Discord."""
    if not API_KEY:
        await ctx.send("⏳ La clé API NationsGlory n'est pas encore configurée dans le bot.")
        return

    cible_discord = membre or ctx.author
    await ctx.send(f"🔍 Vérification de `{pseudo}` en cours...")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(f"{BASE_URL}/players/{pseudo}") as resp:
            if resp.status == 404:
                await ctx.send(f"❌ Le joueur `{pseudo}` est inconnu sur {SERVER.capitalize()} ou inactif depuis 90 jours.")
                return
            if resp.status == 403:
                await ctx.send(f"🔒 Le profil de `{pseudo}` est privé. Il doit le rendre public sur le site NationsGlory.")
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

        async with session.get(f"{BASE_URL}/countries/{country_id}") as resp:
            if resp.status != 200:
                await ctx.send("⚠️ Erreur lors de la récupération des détails du pays.")
                return

            country_data = (await resp.json()).get("data", {})
            country_name = country_data.get("name", "")

            if country_name.lower() == PAYS_CIBLE.lower():
                global TCHAD_COUNTRY_ID
                TCHAD_COUNTRY_ID = country_id

                nom_role_discord = ROLES_MAPPING.get(role_api)
                statut_role = f"Grade API détecté : `{role_api}`"

                if nom_role_discord:
                    role_discord = discord.utils.get(ctx.guild.roles, name=nom_role_discord)
                    if role_discord:
                        anciens_roles = [r for r in cible_discord.roles if r.name in ROLES_MAPPING.values()]
                        if anciens_roles:
                            await cible_discord.remove_roles(*anciens_roles)
                        await cible_discord.add_roles(role_discord)
                        statut_role = f"✅ Rôle **{nom_role_discord}** attribué à {cible_discord.mention} !"

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
                await ctx.send(f"❌ `{exact_username}` n'est pas au Tchad (pays actuel : **{country_name}**).")

@bot.command(name="pays")
async def infos_pays(ctx):
    """Affiche les statistiques actuelles du Tchad sur Jade."""
    if not API_KEY:
        await ctx.send("⏳ La clé API NationsGlory n'est pas encore configurée dans le bot.")
        return

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        country_id = await get_tchad_id(session)
        if not country_id:
            await ctx.send(f"⚠️ Impossible de trouver le pays `{PAYS_CIBLE}` sur {SERVER.capitalize()}.")
            return

        async with session.get(f"{BASE_URL}/countries/{country_id}") as resp:
            if resp.status != 200:
                await ctx.send(f"⚠️ Erreur API (Code: {resp.status}).")
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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("⛔ Tu n'as pas le grade suffisant (**Chef d'État** ou **Officier du Pays**) pour utiliser cette commande.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Il manque un argument dans ta commande. Tape `!aide` pour voir comment l'utiliser.")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)