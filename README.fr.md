# Burgonet - Enterprise AI Gateway

<p align="center">
  <img src="frontend/app/static/images/logo.png?raw=true" style="width: 200px; height: auto;" />
</p>

## À propos

Burgonet Gateway est une passerelle d'entreprise DevSecOps pour l'IA qui fournit un accès sécurisé aux LLM et des contrôles de conformité pour les systèmes d'IA.

L'objectif est de fournir aux employés, unités et projets un accès unique aux fournisseurs de LLM basés sur le cloud ou aux modèles auto-hébergés.

<p align="center">
  <img src="docs/images/overview.png?raw=true" " />
</p>

Les utilisateurs peuvent :
- demander facilement de nouveaux jetons en libre-service
- surveiller leur consommation

Les administrateurs peuvent :
- configurer les fournisseurs (OpenAI, Claude, DeepSeek, Ollama, ...) en un seul endroit
- définir des quotas par jetons ou solde par utilisateur, groupe ou projet
- surveiller l'utilisation
- auditer les journaux d'entrées/sorties
- créer des listes de contrôle d'accès par règles

Fonctionnalités fournies :
- Authentification API par jeton
- Gestion des utilisateurs via LDAP
- Gestion des configurations Nginx
- Génération et stockage sécurisé des jetons

Prévu :
- Intégration WebSSO
- Gestion des quotas (par groupe/utilisateur)
- Liste de contrôle d'accès pour répartir entre fournisseurs sur site et cloud
- Routage sémantique
- Filtrage des mots-clés et des PII

La documentation complète est disponible sur [https://burgonet.eu/](https://burgonet.eu/)

## Fonctionnalités

- **Gestion des jetons** : Générer, voir et supprimer des jetons API
- **Authentification LDAP** : Intégration avec les systèmes LDAP d'entreprise
- **Stockage Redis** : Stockage sécurisé des jetons avec Redis
- **Intégration Nginx** : Gestion des configurations Nginx via interface web

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/your-repo/burgonet-gateway.git
   cd burgonet-gateway
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurer l'application en éditant `frontend/app/config.py`

4. Lancer l'application :
   ```bash
   python wsgi.py
   ```

## Configuration

Le fichier de configuration principal se trouve dans `flask_app/app/config.py`. Les paramètres clés incluent :

- Détails de connexion LDAP
- Paramètres de connexion Redis
- Chemins de configuration Nginx
- Paramètres de sécurité

## Licence

Ce projet est sous licence GNU Affero General Public License v3.0 - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Auteur & Support Entreprise

Sébastien Campion - sebastien.campion@foss4.eu

## Origine du nom

La [burgonnette](https://fr.wikipedia.org/wiki/Burgonnette) est un casque ancien, une protection pour le cerveau.
Protégez votre savoir.

---

**Note** : Ce projet est en développement actif. Veuillez signaler tout problème ou demande de fonctionnalité via le système de suivi des problèmes.
