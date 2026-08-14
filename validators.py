# actualites/validators.py
import re
from rest_framework import serializers

# ==========================================
# 1. CONFIGURATION DES SEUILS
# ==========================================

MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 200
MIN_DESCRIPTION_LENGTH = 20

# --- Seuils anti-spam / contenu de faible qualité ---
MAX_CHARS_REPETES = 3           # ex: "aaaaa" (4x consécutifs) -> rejeté
MIN_CHAR_UNIQUE_AUTORISE = 0.3         # au moins 30% de caractères uniques exigés
MAX_CONSECUTIVE_CONSONNES= 3      # Pas plus de 3 consonnes successives
MAX_CONSECUTIVE_VOYELLES = 3          # Pas plus de 3 voyelles successives


# ==========================================
# 2. FONCTIONS DE VALIDATION (privées)
# ==========================================

def excessive_repetition(value: str) -> bool:
    """
    Détecte une répétition excessive d'un même caractère consécutif.
    Exemple: 'aaaaaaaaa' ou 'cccccccccc' -> True
    """
    return bool(re.search(r'(.)\1{' + str(MAX_CHARS_REPETES) + r',}', value))


def low_char_diversity(value: str) -> bool:
    """
    Détecte un texte à trop faible diversité de caractères.
    Exemple: 'abababababab' -> True (seulement 2 caractères uniques)
    """
    cleaned = re.sub(r'\s+', '', value)

    if len(cleaned) < 10:
        return False

    unique_ratio = len(set(cleaned.lower())) / len(cleaned)
    return unique_ratio < MIN_CHAR_UNIQUE_AUTORISE


def excessive_consonnes(value: str) -> bool:
    """
    Détecte une suite trop longue de consonnes successives.
    Exemple: 'ddffddygfts' ou 'bcdfghj' -> True
    
    Consonnes : toutes les lettres sauf a, e, i, o, u, y
    """
    # 4 consonnes ou plus d'affilée
    consonne_pattern = r'[bcdfghjklmnpqrstvwxz]{' + str(MAX_CONSECUTIVE_CONSONNES+ 1) + r',}'
    return bool(re.search(consonne_pattern, value.lower()))


def excessive_voyelles(value: str) -> bool:
    """
    Détecte une suite trop longue de voyelles successives.
    Exemple: 'eiouauy' ou 'aeiou' -> True
    
    Voyelles : a, e, i, o, u, y
    """
    # 4 voyelles ou plus d'affilée
    voyelle_pattern = r'[aeiouy]{' + str(MAX_CONSECUTIVE_VOYELLES + 1) + r',}'
    return bool(re.search(voyelle_pattern, value.lower()))


# ==========================================
# 3. FONCTION PRINCIPALE (à importer)
# ==========================================

def validate_text_quality(value: str, field_label: str):
    """
    Regroupe les vérifications anti-spam communes à un champ texte.
    
    Usage:
        from .validators import validate_text_quality
        
        def validate_titre(self, value):
            value = value.strip()
            validate_text_quality(value, "Le titre")
            return value
    """
    # 1. Vérifier les répétitions de caractères
    if excessive_repetition(value):
        raise serializers.ValidationError(
            f"{field_label} contient une répétition de caractères non valide."
        )
    
    # 2. Vérifier la diversité des caractères
    if low_char_diversity(value):
        raise serializers.ValidationError(
            f"{field_label} ne semble pas contenir de texte valide "
            f"(diversité de caractères trop faible)."
        )
    
    # 3. Vérifier les consonnes successives
    if excessive_consonnes(value):
        raise serializers.ValidationError(
            f"{field_label} contient trop de consonnes successives."
        )
    
    # 4. Vérifier les voyelles successives
    if excessive_voyelles(value):
        raise serializers.ValidationError(
            f"{field_label} contient trop de voyelles successives."
        )