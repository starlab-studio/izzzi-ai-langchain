#!/bin/bash

# Script de démarrage pour le service LangChain
# Active automatiquement l'environnement virtuel et lance uvicorn

# Aller dans le répertoire du projet
cd "$(dirname "$0")"

# Activer l'environnement virtuel
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Environnement virtuel activé"
else
    echo "Erreur: .venv introuvable. Veuillez créer l'environnement virtuel d'abord."
    exit 1
fi

# Vérifier que pydantic-settings est installé
python -c "import pydantic_settings" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Erreur: pydantic-settings n'est pas installé. Installation en cours..."
    pip install pydantic-settings
fi

# Lancer uvicorn
echo "Démarrage du service..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

