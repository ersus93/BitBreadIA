import pytest
import sys
import os

# Agregar el directorio raíz al path para importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_settings_file(tmp_path):
    """Fixture que proporciona un archivo de settings temporal."""
    return tmp_path / "user_settings.json"

@pytest.fixture
def mock_context_file(tmp_path):
    """Fixture que proporciona un archivo de contexto temporal."""
    return tmp_path / "user_context.json"
