# API JOJ Events - Backend

## Table des matières

1. [Introduction](#introduction)
2. [Technologies utilisées](#technologies-utilisées)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Structure du projet](#structure-du-projet)
6. [Endpoints de l'API](#endpoints-de-lapi)
7. [Gestion des tokens JWT](#gestion-des-tokens-jwt)
8. [Système de rôles](#système-de-rôles)
9. [Documentation Swagger](#documentation-swagger)
10. [Tests](#tests)
11. [FAQ](#faq)


## Introduction

JOJ Events Backend est une API complète pour la gestion des Jeux Olympiques de la Jeunesse. Elle couvre l'authentification JWT, la gestion des événements, des disciplines, des compétiteurs, des actualités, des sites, des paiements et des notifications.

### Fonctionnalités principales

- Authentification JWT (connexion, déconnexion, rafraîchissement de token)
- Gestion des utilisateurs avec deux rôles : **Admin** et **SuperAdmin**
- Création de comptes Admin et SuperAdmin (réservée aux SuperAdmins, sauf le premier)
- Profil utilisateur : nom, prénom, email, téléphone
- Changement de mot de passe
- Révocation / réactivation de comptes Admin
- Gestion des événements, disciplines, catégories et compétiteurs
- Gestion des actualités, sites, paiements et notifications
- Documentation interactive Swagger / ReDoc


## Technologies utilisées

| Technologie | Version | Rôle |
|---|---|---|
| Python | 3.12+ | Langage de programmation |
| Django | 5.x | Framework Web principal |
| Django REST Framework | 3.x | Framework API REST |
| djangorestframework-simplejwt | 5.x | Authentification JWT |
| drf-spectacular | 0.27.x | Documentation OpenAPI / Swagger |
| django-cors-headers | 4.x | Gestion CORS |
| Pillow | — | Gestion des images (compétiteurs, événements) |
| python-dotenv | — | Variables d'environnement |


## Installation

### Prérequis système

```bash
sudo apt-get update
sudo apt-get install -y pkg-config build-essential python3-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev libssl-dev
```

### Étapes d'installation

1. **Cloner le projet**
   ```bash
   git clone <url-du-projet>
   cd JOJ_events_Backend
   ```

2. **Créer l'environnement virtuel**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux / Mac
   # .venv\Scripts\activate    # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**

   Créer un fichier `.env` à la racine :
   ```env
   SECRET_KEY=votre_clé_secrète
   DEBUG=True
   DB_ENGINE=django.db.backends.sqlite3
   DB_NAME=db.sqlite3
   ```

5. **Appliquer les migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Créer le premier SuperAdmin**

   Via la commande Django :
   ```bash
   python manage.py createsuperuser
   ```
   Le rôle `SUPERADMIN` est attribué automatiquement à tout utilisateur `is_superuser=True`.

   Ou via l'API (si aucun superadmin n'existe encore) :
   ```bash
   curl -X POST http://localhost:8000/api/auth/creer-superadmin/ \
     -H "Content-Type: application/json" \
     -d '{
       "username": "superadmin",
       "email": "superadmin@exemple.com",
       "first_name": "Prénom",
       "last_name": "Nom",
       "tel": "771234567",
       "password": "Super123456",
       "password2": "Super123456"
     }'
   ```

7. **Démarrer le serveur**
   ```bash
   python manage.py runserver
   ```


## Configuration

### Variables d'environnement (`.env`)

```env
SECRET_KEY=votre_clé_secrète_django
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3   # ou postgresql
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

### Applications installées

```python
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    # JOJ Events
    'utilisateurs',      # Modèle utilisateur personnalisé (Personnel)
    'evenements',
    'actualites',
    'paiements',
    'sites',
    'notifications',
    'authentification',  # Serializers, vues et URLs d'authentification
    # Tiers
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',
]
```

### Modèle utilisateur personnalisé

```python
AUTH_USER_MODEL = 'utilisateurs.Personnel'
```

Le modèle `Personnel` étend `AbstractUser` avec :
- `tel` : numéro de téléphone
- `role` : `ADMIN` ou `SUPERADMIN` (synchronisé automatiquement avec `is_superuser`)

La logique d'authentification (serializers, vues, URLs) est dans l'application `authentification`, qui importe le modèle via `get_user_model()`.

### Configuration JWT

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```


## Structure du projet

```text
JOJ_events_Backend/
│
├── manage.py
├── requirements.txt
├── .env                            # Variables d'environnement (non versionné)
│
├── joj_events/                     # Configuration du projet
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── utilisateurs/                   # Modèle utilisateur (source unique)
│   ├── models.py                   # Personnel (AbstractUser + tel + role)
│   └── admin.py                    # Admin Django : Personnel, Admin, Superadmin
│
├── authentification/               # Logique d'authentification
│   ├── serializers.py              # CreerAdmin, CreerSuperAdmin, Profil, etc.
│   ├── views.py                    # Vues API
│   ├── urls.py                     # Routes /api/auth/
│   └── admin.py
│
├── evenements/                     # Disciplines, catégories, compétiteurs, événements
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── actualites/                     # Actualités / news
├── paiements/                      # Paiements
├── sites/                          # Sites / lieux des épreuves
└── notifications/                  # Notifications
```


## Endpoints de l'API

Préfixe commun : `/api/auth/`

### Endpoints publics (sans authentification)

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/connexion/` | Connexion — retourne access + refresh token |
| POST | `/api/auth/rafraichir-token/` | Obtenir un nouvel access token |
| POST | `/api/auth/verifier-token/` | Vérifier la validité d'un token |
| POST | `/api/auth/creer-superadmin/` | Créer le premier SuperAdmin (libre) ou un autre (SuperAdmin requis) |

### Endpoints authentifiés

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/auth/profil/` | Obtenir le profil de l'utilisateur connecté |
| PUT | `/api/auth/profil/` | Modifier le profil (username, email, prénom, nom, téléphone) |
| POST | `/api/auth/deconnexion/` | Invalider le refresh token |
| PUT | `/api/auth/changer-mot-de-passe/` | Changer le mot de passe |

### Endpoints SuperAdmin uniquement

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/creer-admin/` | Créer un nouvel administrateur |
| GET | `/api/auth/utilisateurs/` | Lister tous les utilisateurs |
| POST | `/api/auth/revoquer-acces/{id}/` | Désactiver le compte d'un admin |
| POST | `/api/auth/reactiver-acces/{id}/` | Réactiver le compte d'un admin |

### Corps des requêtes de création

**Créer un Admin ou SuperAdmin :**
```json
{
  "username": "admin1",
  "email": "admin1@exemple.com",
  "first_name": "Prénom",
  "last_name": "Nom",
  "tel": "771234567",
  "password": "Admin123456",
  "password2": "Admin123456"
}
```


## Gestion des tokens JWT

### Types de tokens

| Token | Durée | Usage |
|---|---|---|
| Access token | 60 minutes | Header `Authorization: Bearer <token>` |
| Refresh token | 7 jours | Body des requêtes de rafraîchissement |

### Flux d'authentification

```
1. Connexion
   POST /api/auth/connexion/  →  { access, refresh }

2. Appels API
   Header: Authorization: Bearer <access_token>

3. Token expiré (401)
   POST /api/auth/rafraichir-token/  body: { refresh }  →  nouveau { access, refresh }

4. Déconnexion
   POST /api/auth/deconnexion/  body: { refresh }  →  token blacklisté
```

### Exemples cURL

**Connexion**
```bash
curl -X POST http://localhost:8000/api/auth/connexion/ \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "Super123456"}'
```

**Accéder à un endpoint protégé**
```bash
curl -X GET http://localhost:8000/api/auth/profil/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Rafraîchir le token**
```bash
curl -X POST http://localhost:8000/api/auth/rafraichir-token/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}'
```

**Déconnexion**
```bash
curl -X POST http://localhost:8000/api/auth/deconnexion/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}'
```

**Créer un admin (SuperAdmin requis)**
```bash
curl -X POST http://localhost:8000/api/auth/creer-admin/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin1",
    "email": "admin1@exemple.com",
    "first_name": "Prénom",
    "last_name": "Nom",
    "tel": "771234567",
    "password": "Admin123456",
    "password2": "Admin123456"
  }'
```


## Système de rôles

### Rôles disponibles

| Rôle | Valeur | Permissions |
|---|---|---|
| SuperAdmin | `SUPERADMIN` | Accès total : créer admins, lister utilisateurs, révoquer/réactiver comptes |
| Admin | `ADMIN` | Connexion, gestion du profil, changement de mot de passe |

### Règles de gestion des rôles

- Le rôle est stocké dans le champ `role` du modèle `Personnel`
- Tout utilisateur avec `is_superuser=True` reçoit automatiquement `role=SUPERADMIN` via `save()`
- Les superusers créés via `createsuperuser` ou Django Admin sont donc automatiquement `SUPERADMIN`
- Un SuperAdmin ne peut pas être révoqué par un autre SuperAdmin
- L'endpoint `creer-superadmin` est libre uniquement si aucun SuperAdmin n'existe encore

### Vérification dans le code

```python
if not request.user.is_superuser:
    return Response({'erreur': 'Accès réservé aux superadmins'}, status=403)
```


## Documentation Swagger

- **Swagger UI :** http://localhost:8000/api/docs/
- **ReDoc :** http://localhost:8000/api/redoc/
- **Schéma OpenAPI :** http://localhost:8000/api/schema/

### Authentification dans Swagger

1. Ouvre http://localhost:8000/api/docs/
2. Utilise `POST /api/auth/connexion/` pour obtenir un access token
3. Clique sur le bouton **Authorize** (cadenas en haut à droite)
4. Colle le token dans le champ — format : `Bearer <ton_token>`
5. Clique sur **Authorize** — tous les endpoints protégés sont maintenant accessibles


## Tests

**Lister les utilisateurs (SuperAdmin)**
```bash
curl -X GET http://localhost:8000/api/auth/utilisateurs/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Changer le mot de passe**
```bash
curl -X PUT http://localhost:8000/api/auth/changer-mot-de-passe/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "ancien_mot_de_passe": "Ancien123",
    "nouveau_mot_de_passe": "Nouveau123",
    "confirmation_nouveau_mot_de_passe": "Nouveau123"
  }'
```

**Révoquer l'accès d'un admin**
```bash
curl -X POST http://localhost:8000/api/auth/revoquer-acces/2/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Réactiver l'accès d'un admin**
```bash
curl -X POST http://localhost:8000/api/auth/reactiver-acces/2/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```


## FAQ

**"Authentication credentials were not provided"**
Tu n'as pas envoyé le token. Utilise le header : `Authorization: Bearer <ACCESS_TOKEN>`

**"Token has wrong type"**
Tu utilises un refresh token à la place d'un access token dans le header Authorization.

**"Refresh token requis" lors de la déconnexion**
Envoie le refresh token dans le body : `{"refresh": "<REFRESH_TOKEN>"}`

**L'accès reste possible après déconnexion**
Normal. L'access token reste valide jusqu'à expiration (60 min). Seul le refresh token est blacklisté.

**Le superuser créé via Django Admin a le rôle ADMIN**
Cela concerne les comptes créés avant la mise en place de la synchronisation automatique. Corrige en base :
```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
get_user_model().objects.filter(is_superuser=True).update(role='SUPERADMIN', is_staff=True)
"
```

**Comment voir les tokens blacklistés ?**
Dans l'admin Django → section **Token Blacklist**.

**Comment changer la durée de vie des tokens ?**
Dans `settings.py` :
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
```


## Maintenance

```bash
# Mettre à jour les dépendances
pip install --upgrade -r requirements.txt

# Sauvegarder la base de données
python manage.py dumpdata > backup.json

# Restaurer la base de données
python manage.py loaddata backup.json
```


## Sécurité

- Ne jamais commiter le fichier `.env` ni la `SECRET_KEY`
- Utiliser HTTPS en production
- Restreindre `CORS_ALLOWED_ORIGINS` aux domaines autorisés en production
- Désactiver `DEBUG=False` en production
- Utiliser des mots de passe forts (minimum 8 caractères, majuscule, chiffre)


## Licence

Ce projet est sous licence MIT.
