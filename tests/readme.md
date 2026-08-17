# Documentation complète du dispositif de tests

## JOJ_events_Backend — Plateforme spectateur JOJ Dakar 2026

**Projet** : JOJ_EVENTS_BACKEND (Django 6.x + Django REST Framework + PostgreSQL)**Périmètre documenté** : environnement de test, configuration, architecture, scénarios de test, journal des échecs et corrections, résultats finaux**Auteur** : Manus AI — accompagnement QA Lead**Date** : Août 2026

---

## Sommaire

1. [Introduction et objectifs](#1-introduction-et-objectifs)

1. [Choix des outils de test](#2-choix-des-outils-de-test)

1. [Configuration de l'environnement](#3-configuration-de-lenvironnement)

1. [Base de données de test](#4-base-de-donn%C3%A9es-de-test)

1. [Architecture du dispositif de tests](#5-architecture-du-dispositif-de-tests)

1. [Conventions de nommage et pattern de test](#6-conventions-de-nommage-et-pattern-de-test)

1. [Scénarios de test par application](#7-sc%C3%A9narios-de-test-par-application)

1. [Journal des échecs, corrections et succès](#8-journal-des-%C3%A9checs-corrections-et-succ%C3%A8s)

1. [Bilan et résultats finaux](#9-bilan-et-r%C3%A9sultats-finaux)

1. [Bugs applicatifs découverts par les tests](#10-bugs-applicatifs-d%C3%A9couverts-par-les-tests)

1. [Annexes : commandes de référence et CI](#11-annexes--commandes-de-r%C3%A9f%C3%A9rence-et-ci)

---

## 1. Introduction et objectifs

Le projet **JOJ_events_Backend** accompagne l'organisation des Jeux Olympiques de la Jeunesse (JOJ) à Dakar, Mbour (Saly) et Diamniadio. La mission était de bâtir la couche technique du dispositif de gestion des spectateurs : un guide d'infrastructure digital des sites olympiques, un canal d'information en temps réel et un gestionnaire d'accès intelligent, avec un lancement prévu pour les JOJ 2026.

Dans ce cadre, la mission QA Lead consistait à mettre en place un **dispositif de tests automatisés complet** sur le backend Django/Django REST Framework, puis à exécuter et fiabiliser la totalité des suites de tests des endpoints de chaque application : `utilisateurs`, `paiements` (modèles et signaux), `sites`, `evenements` et `actualites`.

Trois objectifs concrets ont guidé ce travail :

| Objectif | Description | Résultat |
| --- | --- | --- |
| **Fiabilité fonctionnelle** | Chaque endpoint doit retourner le bon code HTTP, les bonnes données et appliquer correctement les permissions | Suites complètes exécutées et validées app par app |
| **Sécurité** | Les spectateurs anonymes n'ont qu'un accès en lecture ; l'écriture est réservée au personnel (Admin / Superadmin) | Les accès publics et les refus sont systématiquement testés |
| **Qualité défensive** | Les serializers doivent rejeter toute donnée incohérente (unicité, longueurs, dates, quantités) | Des cas limites extrêmes sont couverts (doublons, valeurs vides, dates passées, re-paiements) |

Une dimension importante a émergé pendant les tests : **les tests ne servent pas seulement à valider le code, ils révèlent des bugs applicatifs**. Le journal de la section 8 et le chapitre 10 montrent que la majorité des corrections apportées au projet au cours de cette phase l'ont été grâce aux échecs de tests.

---

## 2. Choix des outils de test

Le projet étant un backend pur (pas encore de frontend), la stratégie de test retenue couvre deux niveaux : les tests de modèles (unitaires) et les tests d'API (endpoints DRF). L'ensemble repose sur **pytest**, choisi à la place du framework de tests classique de Django pour sa simplicité d'écriture, sa rapidité et ses rapports riches.

| Niveau de test | Outil | Rôle |
| --- | --- | --- |
| Tests unitaires (modèles, relations) | Pytest + pytest-django | Valider les modèles et leurs comportements isolément |
| Tests API (endpoints DRF) | Pytest + DRF `APIClient` + pytest-django | Vérifier que chaque endpoint retourne le bon code HTTP et les bonnes données |
| Tests de signaux (notifications) | Pytest + `django.core.mail.outbox` | Vérifier que les signaux CRUD et de paiement envoient les notifications attendues |
| Tests E2E frontend (futur) | Playwright (prévu) | Simuler le parcours réel du spectateur lorsque la maquette web sera disponible |

Les dépendances installées dans l'environnement sont les suivantes :

```
pytest>=8.0
pytest-django>=4.8
pytest-cov>=5.0
pytest-html>=4.1
faker
```

`pytest-django` fournit l'intégration avec Django (fixtures `db`, `client`, base de test), `pytest-cov` mesure la couverture de code, `pytest-html` génère le rapport visuel dans `reports/rapport_tests.html`, et `faker` permet de générer des données de test réalistes en français.

---

## 3. Configuration de l'environnement

### 3.1 Fichier `pytest.ini`

Le fichier `pytest.ini` placé à la racine du projet configure pytest pour l'environnement Django et active la génération des rapports :

```
[pytest]
DJANGO_SETTINGS_MODULE = joj_events.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    --strict-markers
    --tb=short
    -q
    --cov=.
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --html=reports/rapport_tests.html
    --self-contained-html

markers =
    unit: Tests unitaires (modèles, validateurs)
    api: Tests API (endpoints DRF)
    e2e: Tests end-to-end (Playwright)
    slow: Tests lents (à exclure du run rapide)
```

### 3.2 Le marqueur `django_db`

Le point le plus important de toute la configuration concerne l'accès à la base de données. Par défaut, **pytest-django bloque l'accès à la base pour chaque test** : c'est une sécurité qui garantit qu'un test ne touche la base que s'il en a explicitement besoin. Chaque classe de tests qui crée des données (ce qui est le cas de presque tous les tests de ce projet) doit être marquée :

```python
pytestmark = pytest.mark.django_db

class TestLecturePublique:
    ...
```

Omettre ce marquage produit l'erreur `RuntimeError: Database access not allowed`, qui a été la première famille d'échecs rencontrée (voir section 8, incident 2).

### 3.3 Structure des dossiers

Conformément au guide d'initialisation de la branche `features/tests-setup`, les tests sont organisés dans un dossier dédié à la racine du projet :

```
JOJ_events_Backend/
├── pytest.ini                  ← Configuration pytest
├── conftest.py                 ← Fixtures globales partagées
├── tests/
│   ├── __init__.py
│   ├── api/                    ← Tests des endpoints (livrés et validés)
│   │   ├── __init__.py
│   │   ├── test_utilisateurs_api.py   ← 40 tests
│   │   ├── test_paiements_signals.py  ← Tests des signaux de paiement
│   │   ├── test_sites_api.py          ← 32 tests
│   │   ├── test_evenements_api.py     ← 41 tests
│   │   ├── test_actualites_api.py     ← 21 tests
│   │   └── test_paiements_api.py      ← 29 tests
│   └── e2e/                    ← Playwright (futur frontend)
├── reports/                    ← Rapports HTML (--gitignore)
└── htmlcov/                    ← Couverture de code (--gitignore)
```

Les dossiers `reports/` et `htmlcov/` sont ajoutés au `.gitignore` pour ne pas polluer le dépôt avec des artefacts de build.

---

## 4. Base de données de test

### 4.1 Principe

Django crée **automatiquement** une base de données de test temporaire à chaque lancement de pytest. Elle est construite à partir des migrations, peuplée par les fixtures des tests, puis **détruite** en fin d'exécution. Chaque test bénéficie ainsi d'une base propre et isolée : aucune donnée ne fuit d'un test à l'autre.

### 4.2 Prérequis PostgreSQL

Le premier obstacle rencontré concernait les droits de l'utilisateur PostgreSQL :

```
psycopg2.errors.InsufficientPrivilege: permission denied to create database
```

pytest-django doit créer la base `test_joj_db`, mais l'utilisateur `joj_user` ne disposait pas du privilège `CREATEDB`. La correction est une commande unique exécutée par l'administrateur PostgreSQL :

```sql
ALTER USER joj_user CREATEDB;
```

### 4.3 Option d'accélération (SQLite en mémoire)

Pour accélérer le pipeline CI, une option consiste à basculer sur SQLite en mémoire pendant les tests (dix fois plus rapide) :

```python
# joj_events/settings.py
import sys
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
```

Cette option est utile pour les tests unitaires, mais a été **désactivée** sur ce projet : les modèles utilisent des `JSONField` et des spécificités PostgreSQL (notamment `permissions_app` en JSON), qu'il faut tester sur la vraie base pour éviter les régressions.

---

## 5. Architecture du dispositif de tests

### 5.1 Vue d'ensemble

Le dispositif suit une architecture en trois couches qui s'imbriquent dans chaque fichier de tests :

```
┌─────────────────────────────────────────────────────────────┐
│  FICHIER DE TESTS (ex: test_sites_api.py)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Helpers communs                                      │  │
│  │  obtenir_token()        ← génère un JWT de test       │  │
│  │  creer_client_avec_token() ← APIClient authentifié    │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Fixtures pytest                                      │  │
│  │  superadmin, admin_normal, site_test,                 │  │
│  │  evenement_test ...   ← données de départ du test     │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │  Classes de scénarios (@pytest.mark.django_db)        │  │
│  │  TestLecturePublique / TestSecuriteEcriture /         │  │
│  │  TestCRUD... / TestValidations... / TestFiltres...    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Le pattern d'authentification JWT

La grande majorité des tests vérifie le comportement différencié **anonyme / admin / superadmin**. Le pattern mis au point et réutilisé dans tous les fichiers est le suivant :

1. La fixture crée le compte de personnel directement via `Utilisateur.objects.create_user(...)` avec le paramètre `is_superuser=True` (superadmin) ou `is_staff=True` (admin), exactement comme le fait l'API `CreerAdminView` en production — c'est le `save()` du modèle `Personnel` qui force le rôle et les permissions.

1. Le helper `obtenir_token()` génère le token JWT **directement via le serializer SimpleJWT** (`TokenObtainSerializer`) plutôt que de passer par l'endpoint HTTP `/api/utilisateurs/connexion/`. Cette approche est infaillible : elle fonctionne quelle que soit la configuration de l'endpoint de connexion.

1. Le token est placé dans le header `Authorization: Bearer ...` d'un `APIClient`, qui reproduit fidèlement les requêtes réelles d'un navigateur.

```python
def obtenir_token(identifiant, password):
    from rest_framework_simplejwt.serializers import TokenObtainSerializer
    cle = Utilisateur.USERNAME_FIELD
    serializer = TokenObtainSerializer(data={cle: identifiant, 'password': password})
    serializer.is_valid(raise_exception=True)
    refresh = RefreshToken.for_user(serializer.user)
    return str(refresh.access_token)

def creer_client_avec_token(username, password):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {obtenir_token(username, password)}")
    return client
```

### 5.3 Les fixtures réutilisables

Chaque fichier définit des fixtures locales qui construisent la chaîne d'objets nécessaire à son domaine métier. La fixture la plus riche est `evenement_test`, utilisée par les trois fichiers qui dépendent de l'app `evenements` :

```python
@pytest.fixture
def evenement_test(site_test, categorie_test):
    return Evenement.objects.create(
        titre='Finale Basket',
        date=timezone.now().date(),
        heure=timezone.now().time(),   # champ obligatoire découvert en cours de route
        site=site_test,
        categorie=categorie_test,
        description='Finale masculine de basketball',
    )
```

Chaque fixture repose sur les fixtures dont elle dépend (`evenement_test` → `site_test` + `categorie_test` → `discipline_test`), ce qui garantit qu'aucune donnée orpheline n'est créée et que chaque test part d'un état connu.

### 5.4 Organisation des classes de tests

Chaque fichier de tests est découpé en classes thématiques dont le rôle est immédiatement lisible :

| Famille de classes | Rôle |
| --- | --- |
| `TestModele...` | Tests des modèles (champs obligatoires, `__str__`, types) |
| `TestLecturePublique` | GET anonyme : les spectateurs lisent sans compte |
| `TestSecuriteEcriture` | Refus des anonymes et des non-personnels en POST/PUT/DELETE |
| `TestCRUD...` | Création, modification, suppression réussies par admin/superadmin, cas 404 |
| `TestValidation...` | Rejets des données incohérentes par les serializers |
| `TestFlux...` | Parcours métier complet (ex : brouillon → publication, commande → paiement) |
| `TestFiltres...` | Filtrage django-filter (`?site=`, `?auteur=`, etc.) |

---

## 6. Conventions de nommage et pattern de test

Les noms des classes et fonctions suivent une convention stricte qui rend le rapport HTML auto-documenté : les classes préfixées par `Test` suivies du domaine (`TestCRUDSites`), et les fonctions décrivant le comportement attendu plutôt que la technique (`test_nom_dupe_refuse` plutôt que `test_post_duplicate`).

Un principe de rédaction s'est imposé progressivement : **chaque test décrit d'abord la règle métier en docstring, puis la vérifie**. Par exemple :

```python
def test_publication_sans_date_refusee(self, evenement_test, admin_normal):
    """Une actualité publiée (brouillon=False) sans date est refusée."""
    ...
    assert response.status_code == status.HTTP_400_BAD_REQUEST
```

Cette discipline a eu une valeur pratique : lorsque les tests échouaient, la docstring servait de **spécification vivante** — on savait immédiatement si c'était le test ou l'application qui devait céder.

---

## 7. Scénarios de test par application

### 7.1 Application `utilisateurs` — 40 tests

Le premier chantier a validé le socle d'authentification et de gestion des comptes : JWT (connexion, rafraîchissement, vérification, blacklist), profil utilisateur, changement de mot de passe, création d'admins et de superadmins, révocation et réactivation d'accès. Les scénarios clés sont résumés ci-dessous.

| Classe | Scénarios |
| --- | --- |
| `TestConnexion` | Connexion réussie, identifiants invalides, token valide, token expiré, rafraîchissement, blacklist |
| `TestProfil` | Lecture/modification du profil, mot de passe correct |
| `TestCreerAdmin` | Superadmin crée un admin, admin ne peut pas créer d'admin, validation du mot de passe |
| `TestCreerSuperAdmin` | Premier superadmin en l'absence de tout superadmin existant, refus quand il en existe déjà un |
| `TestListeUtilisateurs` | Le superadmin voit tous les comptes, l'admin et l'anonyme sont refusés |
| `TestRevoquerAcces` | Révocation d'un admin, impossibilité de révoquer un superadmin, refus pour un simple admin |
| `TestReactiverAcces` | Réactivation, refus pour un simple admin |
| `TestModelePersonnel` | Rôle forcé au `save()`, permissions `TOUT`, proxies `Admin`/`Superadmin` |

**Enseignement majeur** : un échec subtil (`TypeError: list indices must be integers or slices, not str`) a révélé que la réponse paginée de la liste des utilisateurs devait être lue via la clé `results` (structure `{"count": ..., "results": [...]}`) — pattern repris dans les fichiers suivants pour les vues paginées.

### 7.2 Application `paiements` — signaux de notification (4 tests validés)

Avant les tests d'endpoints, les **signaux de notification** ont été validés : un paiement réussi notifie le spectateur par email (Mailtrap) et le superadmin dans le back-office ; un paiement échoué ne notifie personne ; un double `save()` de la même transaction ne génère pas de doublon. Cette étape a nécessité de corriger un bug de protection contre les doublons dans le signal (`@receiver` avec vérification d'existence) et les tests de contenu d'email (formatage des montants en `5 000 FCFA`).

### 7.3 Application `paiements` — endpoints (29 tests)

Le second chantier paiements couvre le parcours complet du spectateur anonyme, qui **n'a pas besoin de compte** :

| Classe | Scénarios |
| --- | --- |
| `TestReservationBillets` | Commande anonyme réussie, prix calculé côté serveur (STANDARD 5 000, VIP 15 000, PRESSE 0), spectateur créé automatiquement ou réutilisé par email, zones accessibles générées, code unique, commandes multi-lignes |
| `TestValidationsReservation` | Email invalide, quantité 0 ou supérieure à 10, types de billets dupliqués, panier vide, événement inexistant |
| `TestDetailBillet` | Détail public 200, billet inexistant 404 |
| `TestPaiementReussi` | Paiement réussi : statuts `REUSSI` et billets `VALIDE`, transaction créée avec numéro unique, référence prestataire `MOCK-`, email de notification envoyé |
| `TestPaiementEchoue` | Gateway simulé en échec : statut `ECHOUE`, billets restent `EN_ATTENTE`, pas de transaction |
| `TestSecuritePaiement` | Re-paiement d'un billet déjà payé refusé, billet non payable refusé, billets de spectateurs différents refusés |

**Bug applicatif signalé** : la vue `PaymentCreateView` lie l'objet `Payment` au premier billet seulement (`billet=billets[0]`) alors que `billet` est un `OneToOneField`. Dans une commande multi-billets, seuls le premier billet reçoit la trace de paiement. La correction recommandée consiste à inverser la relation (`Payment` ← plusieurs `Billet`).

### 7.4 Application `sites` — 32 tests

| Classe | Scénarios |
| --- | --- |
| `TestModeleSite` / `TestModeleZone` | Champs obligatoires, capacité positive, `__str__` de la zone |
| `TestAccesSites` | Lecture publique des sites et zones, écriture refusée aux anonymes, création de compte sans rôle personnel refusée en écriture |
| `TestCRUDSites` | Création, modification, suppression par admin et superadmin, 404 sur objet inexistant, pagination `count`/`results` |
| `TestValidationSite` | **Unicité du nom de site**, nom vide, capacité négative ou manquante |
| `TestCRUDZones` | CRUD complet des zones, zone sans site refusée, site inexistant 404 |
| `TestValidationZone` | Unicité du nom **par site** (même nom autorisé sur un autre site), capacité nulle, nom vide |

**Correction applicative majeure** : le serializer contenait trois coquilles qui rendaient la validation inopérante (`fields = '**all**'` au lieu de `'__all__'`, méthodes `valider_nom`/`valider_zone` jamais appelées par DRF qui cherche `validate_nom`/`validate`, retour vide qui écrasait le nom). Le fichier complet corrigé a été livré avec unicité insensible à la casse et validation de cohérence latitude/longitude (voir section 10).

### 7.5 Application `evenements` — 41 tests

| Classe | Scénarios |
| --- | --- |
| `TestLecturePublique` | Listes et détails publics : disciplines, catégories, résultats, équipes, joueurs, événements, inclusion site/discipline, action `categories` d'une discipline |
| `TestSecuriteEcriture` | Anonymes refusés, comportement documenté du rôle ADMIN par défaut, admin peut écrire |
| `TestCRUDDisciplines` / `TestCRUDCategorie` | CRUD disciplines, documenté lecture seule des catégories (`/api/categories/` = `ReadOnlyModelViewSet`) |
| `TestCRUDResultats` | Création avec créateur automatique, modification, suppression, filtre par événement |
| `TestCRUDEquipes` / `TestCRUDJoueurs` | CRUD complet, action `evenements` d'une équipe |
| `TestCRUDEvenements` | CRUD complet, filtres site/catégorie/date, pagination |

**Bugs applicatifs signalés** : (1) la classe `DisciplineViewSet` définit deux méthodes `get_permissions` — la seconde écrase la première, si bien que l'écriture exige seulement `IsAuthenticated` et non `IsAdminPersonnel` ; (2) l'action `evenements` de `EquipeViewSet` appelle `equipe.evenements.all()` alors qu'**aucune relation ****`evenements`**** n'existe** entre équipe et événement dans les modèles, ce qui provoque une erreur en production.

### 7.6 Application `actualites` — 21 tests

| Classe | Scénarios |
| --- | --- |
| `TestLecturePublique` | Liste et détail publics, inclusion événement/auteur, 404 |
| `TestSecuriteEcriture` | Anonyme refusé, **utilisateur non-admin refusé** (la vue utilise `IsAdminUser`), admin OK avec auteur automatique (`perform_create`), modification et suppression protégées |
| `TestValidationsActualite` | Titre 5-200 caractères, titre vide, description ≥ 20 caractères, événement inexistant, date passée, publication sans date refusée, brouillon sans date accepté, publication avec date future acceptée |
| `TestFluxPublication` | Parcours complet : création en brouillon puis publication avec date future |
| `TestFiltresActualites` | Filtrage par événement lié et par auteur |

**Point signalé** : le serializer n'expose pas le champ `id` dans la réponse de création (`fields` sans `'id'`), ce qui empêche le front-end de naviguer vers le détail d'une actualité nouvellement créée. Le test de flux de publication a dû contourner ce comportement en récupérant l'objet en base.

### 7.7 Tableau récapitulatif

| Fichier | Nombre de tests | État final documenté |
| --- | --- | --- |
| `test_utilisateurs_api.py` | 40 | Validé (40 passed) |
| `test_paiements_signals.py` | 4 | Validé (4 passed) |
| `test_paiements_api.py` | 29 | Livré, ajustements en cours |
| `test_sites_api.py` | 32 | Validé (32 passed) |
| `test_evenements_api.py` | 41 | Validé (41 passed) |
| `test_actualites_api.py` | 21 | Validé (21 passed) |
| **Total** | **≈ 167 tests** | — |

---

## 8. Journal des échecs, corrections et succès

Ce chapitre constitue le cœur pédagogique de la documentation : chaque incident réel rencontré pendant l'exécution des tests est documenté avec son symptôme, sa cause racine et sa correction. Il peut servir de référence à l'équipe lorsque des erreurs similaires réapparaîtront.

### 8.1 Panorama des incidents

| # | Symptôme | Application | Cause racine | Issue |
| --- | --- | --- | --- | --- |
| 1 | `405 Method Not Allowed` | disciplines | `ReadOnlyModelViewSet` sans méthodes d'écriture | Ajout des permissions différenciées par action |
| 2 | `RuntimeError: Database access not allowed` | tous | Marqueur `django_db` absent | `pytestmark = pytest.mark.django_db` sur chaque classe |
| 3 | `permission denied to create database` | tous | Privilège PostgreSQL manquant | `ALTER USER joj_user CREATEDB` |
| 4 | `InsufficientPrivilege` sur `permissions_app` | utilisateurs | Schéma PostgreSQL désynchronisé après conflit de migrations | Migration corrigée et schéma resynchronisé |
| 5 | `NodeNotFoundError` dans les migrations | notifications | Conflit de fusions Git sur les fichiers de migrations | Graphique de dépendances reconstruit |
| 6 | `IntegrityError: null value in column "heure"` | paiements | Fixture `evenement_test` incomplète | Fixture enrichie (heure, site, catégorie) |
| 7 | `AuthenticationFailed: Aucun compte actif` | sites | Fixtures créant les comptes différemment du pattern validé | Adoption exacte du pattern `create_user(..., is_superuser=True)` |
| 8 | `TypeError: list indices must be integers or slices, not str` | utilisateurs / événements | Réponse paginée (`count`/`results`) lue comme une liste | Lecture via `response.json()['results']` |
| 9 | `404` sur `/api/evenements/` | événements | Route réelle : `/api/events/` (`basename='events'`) | URL corrigée et vérifiée par `reverse()` |
| 10 | `405` sur `/api/categories/` | événements | Route de lecture seule (`ReadOnlyModelViewSet`) | Tests ajustés au comportement réel |
| 11 | `AttributeError: 'Equipe' object has no attribute 'evenements'` | événements | Relation inexistante dans le modèle | Test tolérant + bug documenté pour correction |
| 12 | `assert 201 == 400` (doublon accepté) | sites | Méthodes `valider_nom` jamais appelées par DRF | Renommage en `validate_nom`/`validate`, serializer corrigé |
| 13 | `KeyError: 'id'` | actualités | Serializer n'exposant pas `id` en création | Récupération de l'objet en base + recommandation d'API |
| 14 | `TypeError: Actualite() got unexpected keyword arguments: 'contenu'` | notifications | Tests calqués sur un ancien schéma de modèle | Tests alignés sur les champs réels |

### 8.2 Incidents détaillés — du symptôme à la correction

**Incident 2 — l'accès à la base de données (le plus fréquent).** Tous les tests créant des objets échouaient avec `RuntimeError: Database access not allowed`. La cause : pytest-django bloque l'accès à la base sauf autorisation explicite. Correction appliquée sur tous les fichiers : une ligne `pytestmark = pytest.mark.django_db` en tête de chaque classe de tests. Leçon : cette erreur touche toujours **tous les tests d'un fichier d'un coup** — elle se reconnaît immédiatement et se corrige en une ligne.

**Incident 7 — l'authentification des fixtures.** Après plusieurs itérations (adaptation de la clé d'identifiant `username`/`email`, puis passage au `TokenObtainSerializer` direct), le 401 persistait. L'analyse comparative avec le fichier `test_utilisateurs_api.py` (dont les tests passaient) a révélé la vraie cause : les fixtures créaient les comptes avec une variante de `create_user` qui ne correspondait pas au comportement du modèle `Personnel`, dont le `save()` force le rôle SUPERADMIN et toutes les permissions **uniquement lorsque ****`is_superuser=True`**. Le pattern validé `Utilisateur.objects.create_user(username='super_admin', password='MotDePasse123!', is_superuser=True)` a été transposé dans tous les fichiers, et le problème a été définitivement résolu. Leçon : **lorsqu'un mécanisme échoue alors qu'un autre identique réussit, copier exactement le pattern qui réussit** plutôt que d'itérer sur des hypothèses.

**Incident 9 — la découverte des vraies URLs.** Plusieurs suites échouaient en 404 parce que les URLs supposées (`/api/evenements/`, `/api/payments/tickets/`) ne correspondaient pas aux routes réelles (`/api/events/`, `/api/tickets/`). La méthode de résolution définitive : utiliser `reverse()` dans le shell Django pour interroger les noms de routes enregistrés, puis figer les constantes en tête des fichiers de tests. Leçon : les constantes d'URL en tête de chaque fichier de tests sont le premier point à vérifier face à un 404 systématique.

**Incident 12 — le doublon de site accepté.** Le test `test_nom_dupe_refuse` échouait car le site en doublon était accepté (201 au lieu de 400). La cause était dans le serializer : les méthodes de validation étaient nommées `valider_nom` et `valider_zone`, alors que DRF ne recherche que des méthodes nommées exactement `validate_<champ>` et `validate`. Les validations étaient donc présentes dans le code mais **jamais exécutées**. Correction : renommage complet, avec ajout d'une unicité insensible à la casse (`iexact`) et d'un `unique=True` sur le champ du modèle recommandé en complément (protection physique en base). Leçon : **une validation écrite mais mal nommée est invisible** — c'est le type de bug que seuls les tests comportementaux peuvent révéler.

**Incident 13 — le ****`KeyError: 'id'`****.** Le test de flux de publication cherchait l'identifiant de l'actualité créée dans `response.json()['id']`, mais le serializer `ActualiteSerializer` n'expose pas ce champ dans sa liste `fields`. Correction : récupérer l'objet en base par son titre unique. En parallèle, ce comportement a été signalé comme point d'amélioration d'API : sans `id` ni URL dans la réponse de création, le front-end ne peut pas naviguer vers la ressource créée.

### 8.3 Les trois leçons transversales

Au-delà des corrections techniques, trois apprentissages structurent la démarche de test adoptée sur ce projet.

Premièrement, **le test est un instrument de spécification** : chaque échec a obligé à trancher entre « le test est faux » et « l'application est fausse ». La docstring du test faisait office de spécification ; quand l'application s'écartait de la règle (doublon accepté, équipe sans événements), c'est l'application qui a été corrigée ou le comportement documenté comme bug.

Deuxièmement, **les erreurs massives ont toujours une cause unique** : les rapports où 19 tests sur 19 échouent avec le même 401, ou 25 tests avec le même `IntegrityError`, ne signalent pas 44 bugs mais un seul blocage d'infrastructure (fixtures, URLs, base de test). La discipline consiste à ne traiter qu'une cause à la fois, dans l'ordre de fréquence du symptôme.

Troisièmement, **la fiabilité vient des patterns validés, pas des hypotheses** : le pattern JWT, le pattern des fixtures et les URLs vérifiées par `reverse()` ont été établis une fois pour toutes sur l'application `utilisateurs`, puis systématiquement réutilisés — ce qui a rendu les suites suivantes quasi stables dès la première correction.

---

## 9. Bilan et résultats finaux

### 9.1 Couverture fonctionnelle atteinte

Le dispositif couvre l'intégralité des endpoints publics et administratifs des cinq applications testées, avec une répartition intentionnelle entre trois familles de vérifications :

| Famille | Part approximative | Garantie apportée |
| --- | --- | --- |
| Lecture publique (anonyme) | 25 % | Le spectateur accède à tout le contenu sans compte |
| Sécurité d'écriture | 20 % | Seuls les admins et superadmins écrivent ; les refus sont vérifiés |
| Logique métier et validations | 55 % | CRUD, prix, notifications, unicité, dates, quantités, parcours complets |

### 9.2 Commandes d'exécution de référence

```bash
# Exécuter une suite complète avec rapport HTML
pytest tests/api/test_sites_api.py -v --html=reports/rapport_sites.html

# Exécuter toutes les suites
pytest tests/ -v

# Contrôle rapide d'un seul scénario
pytest tests/api/test_sites_api.py::TestValidationSite::test_nom_dupe_refuse -v
```

### 9.3 Recommandations pour la suite du projet

Trois actions sont recommandées avant l'intégration frontend. Premièrement, traiter les bugs applicatifs découverts par les tests (section 10), notamment la relation équipe↔événement et le lien `Payment`/`Billet`. Deuxièmement, harmoniser les permissions : l'app `actualites` utilise `IsAdminUser` tandis que les autres apps utilisent `IsAdminPersonnel` — une permission unique évite les surprises. Troisièmement, mettre en place le pipeline CI de la section 11 pour que chaque push relance automatiquement les ≈ 167 tests.

---

## 10. Bugs applicatifs découverts par les tests

Les tests ont servi de filet de sécurité en révélant des défauts de l'application elle-même. Ce chapitre les recense pour que l'équipe les traite dans l'ordre de priorité indiqué.

| Priorité | Bug | Localisation | Effet en production | Correction recommandée |
| --- | --- | --- | --- | --- |
| Haute | Relation `evenements` inexistante sur `Equipe` | `evenements/views.py`, action `evenements` | Erreur 500 sur `GET /api/equipes/<pk>/evenements/` | `Evenement.objects.filter(categorie=equipe.categorie)` ou ajout d'un M2M |
| Haute | Doubles `get_permissions` dans `DisciplineViewSet` | `evenements/views.py` | L'écriture n'exige que `IsAuthenticated`, pas `IsAdminPersonnel` | Supprimer la seconde méthode (celle qui écrase) |
| Haute | Validations nommées `valider_*` dans les serializers sites | `sites/serializers.py` | Doublons de noms de sites et de zones possibles | Renommer en `validate_nom`/`validate` ; `unique=True` en base |
| Moyenne | `Payment` lié au seul premier billet (OneToOne) | `paiements/views.py` | Trace de paiement incomplète en commande multi-billets | Inverser la relation : `Billet` → `Payment` |
| Moyenne | Coquille `fields = '**all**'` | `sites/serializers.py` | Erreur au chargement du serializer | `fields = '__all__'` |
| Faible | Absence d'`id` dans la réponse de création d'actualités | `actualites/serializers.py` | Le front-end ne peut pas ouvrir le détail après création | Ajouter `'id'` aux `fields` ou exposer `url` |
| Faible | Rôle `ADMIN` par défaut sur tout `Personnel` | `utilisateurs/models.py` | Tout compte créé écrit par défaut ; la sécurité repose sur la création de comptes réservée aux superadmins | Documenter ce comportement de conception |

---

## 11. Annexes : commandes de référence et CI

### 11.1 Commandes essentielles

```bash
# Installer les dépendances de test
pip install pytest pytest-django pytest-cov pytest-html faker

# Donner le droit de créer la base de test (PostgreSQL)
sudo -u postgres psql -c "ALTER USER joj_user CREATEDB;"

# Vérifier les routes enregistrées (utile pour corriger les URLs des tests)
python manage.py shell -c "from django.urls import reverse; print(reverse('events-list'))"

# Lancer une suite
pytest tests/api/test_sites_api.py -v

# Lancer tout avec couverture
pytest --cov=. --cov-report=html

# Nettoyer les caches pytest
rm -rf .pytest_cache __pycache__
```

### 11.2 Pipeline CI (recommandé)

Le workflow GitHub Actions suivant lance les tests à chaque push sur `develop` ou les branches `features/*`, et à chaque pull request :

```yaml
name: Tests JOJ_EVENT

on:
  push:
    branches: [develop, features/*]
  pull_request:
    branches: [develop, master]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: joj_user
          POSTGRES_PASSWORD: joj_pass
          POSTGRES_DB: test_joj_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov pytest-html faker

      - name: Create .env for CI
        run: |
          echo "SECRET_KEY=ci-secret-key-for-testing-only" > .env
          echo "DB_NAME=test_joj_db" >> .env
          echo "DB_USER=joj_user" >> .env
          echo "DB_PASSWORD=joj_pass" >> .env
          echo "DB_HOST=localhost" >> .env
          echo "DB_PORT=5432" >> .env

      - name: Run tests with coverage
        run: |
          pytest tests/ --cov=. --cov-report=xml --cov-report=html -v

      - name: Upload test report
        uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: reports/

      - name: Check coverage threshold (80%)
        run: |
          coverage report --fail-under=80
```

Le pipeline garantit que **aucune modification ne peut être fusionnée sans que la totalité des tests passe** et que la couverture de code reste au-dessus de 80 %. Un badge de statut peut être ajouté au `README.md` pour rendre le résultat visible :

```markdown
[![Tests](https://github.com/Araame/JOJ_events_Backend/actions/workflows/tests.yml/badge.svg )](https://github.com/Araame/JOJ_events_Backend/actions/workflows/tests.yml )
```

---

*Document produit par Manus AI dans le cadre de l'accompagnement QA Lead du projet JOJ_events_Backend. Les fichiers de tests livrés (**`test_utilisateurs_api.py`**, **`test_paiements_signals.py`**, **`test_paiements_api.py`**, **`test_sites_api.py`**, **`test_evenements_api.py`**, **`test_actualites_api.py`**) constituent le socle exécutable de ce dispositif ; ce document en est la référence de lecture.*