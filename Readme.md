# API d'Authentification JOJ Events

## Table des matières

1. [Introduction](#introduction)
2. [Technologies utilisees](#technologies-utilisees)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Structure du projet](#structure-du-projet)
6. [Endpoints de l'API](#endpoints-de-lapi)
7. [Gestion des tokens JWT](#gestion-des-tokens-jwt)
8. [Systeme de roles](#systeme-de-roles)
9. [Documentation Swagger](#documentation-swagger)
10. [Tests](#tests)
11. [FAQ](#faq)


## Introduction

L'API d'authentification de JOJ Events est un systeme complet de gestion des utilisateurs base sur Django REST Framework avec authentification JWT (JSON Web Tokens).

### Fonctionnalites principales

- Inscription des utilisateurs (Admin et SuperAdmin)
- Connexion avec generation de tokens JWT
- Rafraichissement des tokens
- Deconnexion (blacklist des tokens)
- Gestion du profil utilisateur
- Changement de mot de passe
- Gestion des roles (Admin/SuperAdmin)
- Liste des utilisateurs (reserve SuperAdmin)
- Revocation/reactivation des comptes (reserve SuperAdmin)
- Documentation Swagger/OpenAPI


## Technologies utilisees

| Technologie | Version | Role |
|-------------|---------|------|
| Django | 6.0.3 | Framework Web principal |
| Django REST Framework | 3.17.1 | Framework API REST |
| djangorestframework-simplejwt | 5.3.1 | Authentification JWT |
| django-cors-headers | 4.4.0 | Gestion CORS |
| drf-spectacular | 0.27.2 | Documentation API |
| mysqlclient | 2.2.8 | Driver MySQL |
| Python | 3.12+ | Langage de programmation |


## Installation

### Prérequis système

Installez les dépendances système nécessaires :
```bash
# Installer les dependances systeme
sudo apt-get update
sudo apt-get install -y pkg-config libmysqlclient-dev build-essential python3-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev libssl-dev
```

### Étapes d'installation

1.  **Cloner le projet**
    ```bash
git clone <url-du-projet>
cd JOJ_events_Backend
```

2.  **Créer l'environnement virtuel**
    ```bash
python -m venv .venv
source .venv/bin/activate  # Sur Linux/Mac
# .venv\Scripts\activate   # Sur Windows
```

3.  **Installer les dépendances**
    ```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4.  **Configurer la base de données**
    ```bash
# Creer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate
```

5.  **Créer le premier SuperAdmin**

    Via la commande Django admin :
    ```bash
# Via Django admin
python manage.py createsuperuser
```
    OU via l'API (recommandé) :
    ```bash
curl -X POST http://localhost:8000/api/auth/creer-superadmin/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin",
    "email": "superadmin@exemple.com",
    "password": "Super123456",
    "password2": "Super123456" }'
```

6.  **Démarrer le serveur**
    ```bash
python manage.py runserver
```

## Configuration

### Fichier `settings.py`

Les principales configurations se trouvent dans joj_events/settings.py :

#### Applications installées
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'evenements',
    'actualites',
    'paiements',
    'sites',
    'notifications',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',
    'drf_spectacular',
    'authentification',
]
```
#### Configuration JWT
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),      # Duree de vie du token d'acces
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),         # Duree de vie du token de rafraichissement
    'ROTATE_REFRESH_TOKENS': True,                       # Rotation des refresh tokens
    'BLACKLIST_AFTER_ROTATION': True,                    # Blacklist apres rotation
    'UPDATE_LAST_LOGIN': True,                           # Mise a jour de la derniere connexion
    'ALGORITHM': 'HS256',                                # Algorithme de signature
    'SIGNING_KEY': SECRET_KEY,                           # Cle de signature
    'AUTH_HEADER_TYPES': ('Bearer',),                    # Type de header
}
```
#### Configuration REST Framework
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```
## Structure du projet
```text
JOJ_events_Backend/
│
├── manage.py
│
├── joj_events/                    # Dossier de configuration
│   ├── __init__.py
│   ├── settings.py               # Configuration du projet
│   ├── urls.py                   # URLs principales
│   └── wsgi.py
│
├── authentification/              # Application d'authentification
│   ├── __init__.py
│   ├── admin.py                  # Configuration admin
│   ├── apps.py
│   ├── models.py                 # Modele Utilisateur
│   ├── serializers.py            # Serializers de donnees
│   ├── urls.py                   # URLs de l'application
│   ├── views.py                  # Vues de l'application
│   └── tests.py                  # Tests
│
├── evenements/                    # Application evenements
├── actualites/                    # Application actualites
├── paiements/                     # Application paiements
├── sites/                         # Application sites
├── notifications/                 # Application notifications
│
└── requirements.txt               # Dependances Python
```
## Endpoints de l'API

Tous les endpoints sont accessibles sous le prefixe /api/auth/.

### Points d'accès publics (sans authentification)

Methode	Endpoint	Description
POST	/api/auth/connexion/	Connexion et obtention des tokens
POST	/api/auth/inscription/	Inscription d'un nouvel utilisateur
POST	/api/auth/creer-superadmin/	Creation du premier SuperAdmin

### Points d'accès avec authentification JWT

#### Utilisateur

Methode	Endpoint	Description
GET	/api/auth/profil/	Obtenir le profil de l'utilisateur
PUT	/api/auth/profil/	Modifier le profil
POST	/api/auth/deconnexion/	Se deconnecter
POST	/api/auth/changer-mot-de-passe/	Changer le mot de passe
POST	/api/auth/rafraichir-token/	Rafraichir le token d'acces
POST	/api/auth/verifier-token/	Verifier la validite d'un token

#### SuperAdmin uniquement

Methode	Endpoint	Description
GET	/api/auth/utilisateurs/	Lister tous les utilisateurs
POST	/api/auth/creer-admin/	Creer un administrateur
POST	/api/auth/revoquer-acces/{id}/	Revoquer l'acces d'un administrateur
POST	/api/auth/reactiver-acces/{id}/	Reactiver l'acces d'un administrateur

## Gestion des tokens JWT

### Qu'est-ce qu'un token JWT ?

Un token JWT est un objet JSON signe qui contient des informations d'authentification.

### Les différents types de tokens

*   **Access Token**
    *   **Durée de vie :** 60 minutes
    *   **Utilisation :** Accéder aux endpoints protégés.
    *   **Inclusion :** Dans le header `Authorization: Bearer <token>`.

*   **Refresh Token**
    *   **Durée de vie :** 7 jours
    *   **Utilisation :** Obtenir un nouvel Access Token.
    *   **Inclusion :** UNIQUEMENT dans le corps (`body`) des requêtes.

### Flux d'authentification
```text
1. Connexion
   │
   ├── POST /api/auth/connexion/
   │   Body: {username, password}
   │
   └── Reponse: {access, refresh}
       
2. Utilisation normale
   │
   └── Header: Authorization: Bearer [access_token]
       
3. Expiration (60 min)
   │
   └── 401 Unauthorized
       
4. Rafraichissement
   │
   ├── POST /api/auth/rafraichir-token/
   │   Body: {refresh: [refresh_token]}
   │
   └── Reponse: Nouveau {access, refresh}
       
5. Deconnexion
   │
   └── POST /api/auth/deconnexion/
       Body: {refresh: [refresh_token]}
```
### Exemple de requêtes avec tokens
1.  **Connexion**
    ```bash
curl -X POST http://localhost:8000/api/auth/connexion/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123456"}'

# Reponse
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```
2.  **Accès à un endpoint protégé**
    ```bash
curl -X GET http://localhost:8000/api/auth/profil/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```
3.  **Rafraîchir le token**
    ```bash
curl -X POST http://localhost:8000/api/auth/rafraichir-token/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJhbGciOiJIUzI1NiIs..."}'
```
4.  **Déconnexion**
    ```bash
curl -X POST http://localhost:8000/api/auth/deconnexion/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJhbGciOiJIUzI1NiIs..."}'
```
## Système de rôles
### Les différents rôles
Role	Permissions
SuperAdmin	Acces total, peut creer des admins, lister tous les utilisateurs, revoquer/reactiver des comptes
Admin	Peut se connecter, gerer son profil, changer son mot de passe
Utilisateur	Par defaut, peut se connecter et gerer son profil
### Gestion des permissions
Exemple de vérification dans les vues :
```python
# Verifier si l'utilisateur est SuperAdmin
if not request.user.is_superuser:
    return Response(
        {'erreur': 'Seul un superadmin peut effectuer cette action'},
        status=status.HTTP_403_FORBIDDEN
    )
```
### Création d'administrateurs
Pour créer un admin (nécessite d'être SuperAdmin) :
```bash
curl -X POST http://localhost:8000/api/auth/creer-admin/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin1",
    "email": "admin1@exemple.com",
    "password": "Admin123456",
    "password2": "Admin123456"
  }'
```
## Documentation Swagger
### Accès à la documentation
*   **Swagger UI :** http://localhost:8000/api/docs/
*   **ReDoc :** http://localhost:8000/api/redoc/
*   **Schema OpenAPI :** http://localhost:8000/api/schema/

### Utilisation de Swagger pour tester l'API
Ouvre http://localhost:8000/api/docs/ dans ton navigateur

Pour les endpoints proteges, clique sur "Authorize" en haut a droite

Entre le token : Bearer [VOTRE_ACCESS_TOKEN]

Clique sur "Authorize"

Teste les differents endpoints directement depuis l'interface

Tests
Tester avec cURL
1. Connexion
bash
curl -X POST http://localhost:8000/api/auth/connexion/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin",
    "password": "Super123456"
  }'
2. Obtenir le profil
bash
curl -X GET http://localhost:8000/api/auth/profil/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]"
3. Changer le mot de passe
bash
curl -X PUT http://localhost:8000/api/auth/changer-mot-de-passe/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{
    "ancien_mot_de_passe": "Super123456",
    "nouveau_mot_de_passe": "Nouveau123456",
    "confirmation_nouveau_mot_de_passe": "Nouveau123456"
  }'
4. Lister tous les utilisateurs (SuperAdmin uniquement)
bash
curl -X GET http://localhost:8000/api/auth/utilisateurs/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]"
5. Revoquer l'acces d'un admin (SuperAdmin uniquement)
bash
curl -X POST http://localhost:8000/api/auth/revoquer-acces/2/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]"
6. Reactiver l'acces d'un admin (SuperAdmin uniquement)
bash
curl -X POST http://localhost:8000/api/auth/reactiver-acces/2/ \
  -H "Authorization: Bearer [ACCESS_TOKEN]"
FAQ
Q: L'erreur "Authentication credentials were not provided"
A: Tu n'as pas envoye le token dans le header. Utilise :

text
Authorization: Bearer [ACCESS_TOKEN]
Q: L'erreur "Token has wrong type"
A: Tu utilises un refresh token pour l'authentification. Utilise un access token dans le header Authorization.

Q: La deconnexion ne fonctionne pas
A: Assure-toi d'avoir active rest_framework_simplejwt.token_blacklist dans INSTALLED_APPS, puis applique les migrations.

Q: "Refresh token requis" dans la deconnexion
A: Tu dois envoyer le refresh token dans le body de la requete :

json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
Q: Acces encore possible apres deconnexion
A: C'est normal ! L'access token expire apres 60 minutes. La deconnexion invalide uniquement le refresh token.

Q: Comment changer la duree de vie des tokens ?
A: Modifie les valeurs dans settings.py :

python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
Q: Comment voir les tokens blacklistes ?
A: Va dans l'admin Django (`http://localhost:8000/admin/`) et regarde la section "Token Blacklist".

## Maintenance
### Mise à jour des dépendances
```bash
pip install --upgrade -r requirements.txt
```
### Sauvegarde de la base de données
```bash
python manage.py dumpdata > backup.json
```
### Restauration de la base de données
```bash
python manage.py loaddata backup.json
```
## Sécurité
*   Ne jamais partager le `SECRET_KEY`.
*   Utiliser HTTPS en production.
*   Changer la durée des tokens selon les besoins.
*   Activer CORS uniquement pour les origines autorisées.
*   Utiliser des mots de passe forts (minimum 8 caractères).

## License
Ce projet est sous licence MIT.
