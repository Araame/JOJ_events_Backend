import pytest

@pytest.fixture
def sample_data():
    """Données de test basiques."""
    return {
        'nom': 'Test',
        'email': 'test@joj.sn',
    }