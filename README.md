# TchadBot

> **Note :** Ce projet est actuellement **en cours de développement** et configuré pour un **usage personnel** sur le serveur Discord du pays Tchad (serveur Jade - NationsGlory).

Bot Discord basé sur l'API publique de NationsGlory pour vérifier l'appartenance des joueurs au pays et afficher leurs informations en jeu.

## Fonctionnalités

- Verification de la présence d'un joueur au Tchad sur le serveur Jade.
- Récupération du rang du joueur (Leader, Officier, Membre, Recrue).
- Affichage des statistiques globales du pays (membres, power, score, solde bancaire).
- Exécution asynchrone pour limiter le temps de réponse aux appels API.

> *Des fonctionnalités supplémentaires (attribution automatique de rôles, gestion des notifications) sont prévues au fil du développement.*

## Configuration

1. Récupérer les identifiants nécessaires :
   - Un token de bot Discord via le portail développeur Discord.
   - Une clé API valide enregistrée sur le portail développeur NationsGlory.

2. Cloner le dépôt et aller dans le dossier :
   ```bash
   git clone https://github.com/moi-le-chat/tchad-bot/
   cd tchad-bot
   ```

3. Créer un environnement virtuel et installer les dépendances :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Sur Windows : .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Créer un fichier `.env` à la racine du projet :
   ```env
   DISCORD_TOKEN=
   NG_API_KEY=
   ```

## Démarrage

Lancer le script :

```bash
python bot.py
```

Sur Discord :

```text
!verifier <pseudo>
```
## Note sur le développement

Une partie du code a été revue et corrigée à l'aide d'une IA.
