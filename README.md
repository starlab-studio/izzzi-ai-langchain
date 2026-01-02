# Izzzi AI Analysis Service

Microservice d'analyse IA des retours élèves utilisant LangChain, OpenAI et pgvector pour fournir des analyses de sentiment, des insights, des alertes et des rapports automatisés.

## 📋 Table des matières

- [Description](#description)
- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API Endpoints](#api-endpoints)
- [Jobs Celery](#jobs-celery)
- [Migrations](#migrations)
- [Développement](#développement)
- [Docker](#docker)

## 🎯 Description

Le service Izzzi AI Analysis est un microservice FastAPI qui analyse les retours des élèves pour générer :

- **Analyses de sentiment** : Score global et distribution positive/neutre/négative
- **Insights complets** : Thèmes récurrents, points d'attention, recommandations
- **Alertes IA** : Détection automatique de problèmes nécessitant une action
- **Résumés de feedback** : Synthèses textuelles générées par LLM
- **Recherche sémantique** : Recherche vectorielle dans les réponses des élèves
- **Chatbot intelligent** : Agent LangChain pour répondre aux questions des enseignants
- **Rapports hebdomadaires** : Génération automatique de rapports pour chaque organisation

## 🏗️ Architecture

Le projet suit une architecture en couches (Clean Architecture) :

```
langchain/
├── src/
│   ├── application/          # Use cases et facades
│   │   ├── facades/
│   │   └── use_cases/
│   ├── domain/               # Entités et interfaces
│   │   ├── entities/
│   │   └── repositories/
│   ├── infrastructure/        # Implémentations concrètes
│   │   ├── database/         # Connexion DB
│   │   ├── models/           # Modèles SQLAlchemy
│   │   ├── repositories/     # Implémentations repositories
│   │   ├── frameworks/       # LangChain, embeddings, agents
│   │   ├── jobs/             # Jobs Celery
│   │   └── auth/             # Validation JWT
│   ├── interface/            # Controllers et DTOs
│   │   ├── controllers/
│   │   ├── dto/
│   │   └── middleware/
│   └── core/                 # Exceptions, logger
├── alembic/                  # Migrations de base de données
└── main.py                   # Point d'entrée FastAPI
```

### Stack technique

- **Framework** : FastAPI (Python 3.11+)
- **LLM** : LangChain + OpenAI GPT-4
- **Base de données** : PostgreSQL avec pgvector pour les embeddings
- **Jobs asynchrones** : Celery + Redis
- **Authentification** : JWT (compatible avec NestJS backend)
- **Migrations** : Alembic

## ✨ Fonctionnalités

### 1. Analyse de Sentiment

Analyse le sentiment global des retours élèves pour une matière donnée.

### 2. Insights Complets

Génère des insights structurés incluant :

- Thèmes identifiés
- Points positifs et négatifs
- Recommandations actionnables
- Prédictions de risques

### 3. Alertes IA

Détecte automatiquement les problèmes nécessitant une attention immédiate.

### 4. Résumés de Feedback

Génère des résumés textuels (court et détaillé) des retours élèves via LLM.

### 5. Recherche Sémantique

Recherche vectorielle dans les réponses des élèves basée sur la similarité sémantique.

### 6. Chatbot Intelligent

Agent LangChain capable de répondre aux questions des enseignants en utilisant :

- Analyse de sentiment
- Recherche sémantique
- Clustering des réponses

### 7. Rapports Hebdomadaires

Génération automatique de rapports hebdomadaires pour chaque organisation (tous les lundis à 8h).

## 📦 Prérequis

- Python 3.11+
- PostgreSQL 14+ avec l'extension pgvector
- Redis (pour Celery)
- OpenAI API Key

## 🚀 Installation

### 1. Cloner le projet

```bash
cd langchain
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer l'extension pgvector dans PostgreSQL

L'extension pgvector est automatiquement créée lors de l'exécution de la migration Alembic.

**Note** : Si vous utilisez Docker avec le `compose.yaml` du backend NestJS, l'image PostgreSQL (`pgvector/pgvector:pg18`) inclut déjà pgvector préinstallé. La migration créera automatiquement l'extension dans votre base de données.

Si vous utilisez PostgreSQL en local (sans Docker), vous devrez installer pgvector au niveau système :

- **macOS** : `brew install pgvector`
- **Ubuntu/Debian** : `sudo apt-get install postgresql-14-pgvector` (remplacez 14 par votre version)

## ⚙️ Configuration

Créer un fichier `.env` à la racine du projet :

```env
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/izzzi_ai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# JWT (doit correspondre au backend NestJS)
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000"]

# Service
SERVICE_NAME=izzzi-ai-service
SERVICE_PORT=8000

# Backend API (pour l'envoi des rapports)
BACKEND_URL=http://localhost:3000
```

## 🎮 Utilisation

### Démarrer le service

**Option 1 : Utiliser le script de démarrage (recommandé)**

```bash
./start.sh
```

**Option 2 : Lancer manuellement**

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Le service sera accessible sur `http://localhost:8000`

> **Note importante** : Assurez-vous toujours que l'environnement virtuel `.venv` est activé avant de lancer l'application, sinon vous obtiendrez une erreur `ModuleNotFoundError: No module named 'pydantic_settings'`.

### Documentation API

En mode développement, la documentation Swagger est disponible sur :

- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

### Démarrer Celery Worker

```bash
celery -A src.infrastructure.jobs.celery_app worker --loglevel=info
```

### Démarrer Celery Beat (pour les tâches planifiées)

```bash
celery -A src.infrastructure.jobs.celery_app beat --loglevel=info
```

## 📡 API Endpoints

### Analysis

- `POST /api/v1/analysis/sentiment` - Analyser le sentiment d'une matière
- `POST /api/v1/analysis/insights/generate` - Générer des insights complets
- `POST /api/v1/analysis/subjects/compare` - Comparer plusieurs matières
- `POST /api/v1/analysis/risks/predict` - Prédire les risques

### Feedback

- `GET /api/v1/feedback/subjects/{subject_id}/summary` - Obtenir le résumé IA
- `GET /api/v1/feedback/subjects/{subject_id}/alerts` - Obtenir les alertes IA
- `POST /api/v1/feedback/subjects/{subject_id}/analyze` - Déclencher une analyse complète

### Search

- `POST /api/v1/search/semantic` - Recherche sémantique dans les réponses

### Chatbot

- `POST /api/v1/chatbot/query` - Poser une question au chatbot intelligent

### Health Check

- `GET /health` - Vérifier l'état du service

**Note** : Tous les endpoints (sauf `/health` et `/`) nécessitent une authentification JWT via le header `Authorization: Bearer <token>`

## 🔄 Jobs Celery

### Tâches planifiées

1. **Indexation des réponses** (`index_new_responses_task`)

   - Fréquence : Toutes les heures
   - Description : Indexe les nouvelles réponses dans le vector store

2. **Analyse quotidienne** (`daily_analysis_task`)

   - Fréquence : Tous les jours à 6h
   - Description : Analyse quotidienne des matières actives

3. **Rapport hebdomadaire** (`weekly_report_task`)
   - Fréquence : Tous les lundis à 8h
   - Description : Génère et envoie les rapports hebdomadaires aux organisations

### Exécution manuelle

```python
from src.infrastructure.jobs.index_responses import index_new_responses_task
from src.infrastructure.jobs.weekly_report import weekly_report_task

# Exécuter une tâche
index_new_responses_task.delay()
weekly_report_task.delay()
```

## 🗄️ Migrations

### Créer une nouvelle migration

```bash
alembic revision --autogenerate -m "Description de la migration"
```

### Appliquer les migrations

```bash
alembic upgrade head
```

### Revenir en arrière

```bash
alembic downgrade -1
```

### Important : Extension pgvector

L'extension `pgvector` doit être activée avant d'appliquer les migrations. Ajoutez cette ligne dans votre première migration :

```python
def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    # ... reste de la migration
```

### Tables créées

Les migrations créent les tables suivantes :

- `response_embeddings` - Embeddings vectoriels des réponses (pgvector)
- `insights` - Insights générés par l'IA (avec colonne embedding optionnelle)
- `analysis_cache` - Cache des analyses
- `subject_analyses` - Analyses par matière
- `chatbot_conversations` - Historique des conversations chatbot

## 🧪 Développement

### Structure des tests

```bash
pytest tests/
```

### Linting

Le projet utilise les standards Python PEP 8.

### Formatage

```bash
black src/
```

## 🐳 Docker

### Build

```bash
docker build -t izzzi-ai-service .
```

### Run

```bash
docker run -p 8000:8000 --env-file .env izzzi-ai-service
```

### Docker Compose

Un fichier `compose.yml` est disponible pour orchestrer le service avec PostgreSQL et Redis.

## 🔐 Authentification

Le service utilise JWT pour l'authentification. Le token doit être fourni dans le header :

```
Authorization: Bearer <jwt_token>
```

Le format du JWT doit correspondre à celui généré par le backend NestJS :

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "organizationId": "org_id",
  "role": "admin",
  "iat": 1234567890,
  "exp": 1234571490
}
```

## 📊 Base de données

### Modèles principaux

- **ResponseEmbeddingModel** : Stocke les embeddings vectoriels des réponses
- **InsightModel** : Insights générés avec métadonnées
- **SubjectAnalysisModel** : Analyses par matière et période
- **AnalysisCacheModel** : Cache pour optimiser les performances
- **ChatbotConversationModel** : Historique des conversations

### Recherche vectorielle

Le service utilise pgvector pour la recherche de similarité. Les embeddings sont générés via OpenAI `text-embedding-3-small` (1536 dimensions).

## 🔗 Intégration avec le Backend

Le service communique avec le backend NestJS via :

1. **Réception des requêtes** : Le backend appelle les endpoints du service AI
2. **Envoi des rapports** : Le service envoie les rapports hebdomadaires au backend via `POST /v1/reports`

## 📝 Notes importantes

- Les embeddings sont générés automatiquement lors de l'indexation des réponses
- Le cache est utilisé pour éviter de régénérer les analyses identiques
- Les rapports hebdomadaires sont envoyés automatiquement au backend qui se charge de l'envoi d'emails et de notifications push
- L'extension pgvector doit être installée dans PostgreSQL avant d'exécuter les migrations

## 🐛 Dépannage

### Erreur "Extension vector does not exist"

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Erreur de connexion à la base de données

Vérifiez que :

- PostgreSQL est démarré
- L'URL de connexion dans `.env` est correcte
- L'utilisateur a les permissions nécessaires

### Erreur Celery

Vérifiez que Redis est démarré et accessible.

## 📄 Licence

Voir le fichier LICENSE pour plus d'informations.
