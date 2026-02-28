"""
Tests para validar la migración del agente "haccp" a "iso17025".

Estos tests verifican:
- Que AGENTS tenga la clave "iso17025" (no "haccp")
- Que el agente tenga el nombre, descripción y carpeta correctos
- Que get_user_agent() maneje la migración de "haccp" antiguo a "iso17025"
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, mock_open

# Importar los módulos a testear
from handlers.agents import AGENTS


class TestAgentDefinition:
    """Tests para validar la definición de agentes en handlers/agents.py"""
    
    def test_agents_has_iso17025_key(self):
        """Verifica que AGENTS tenga la clave 'iso17025'"""
        assert "iso17025" in AGENTS, "AGENTS debe contener la clave 'iso17025'"
    
    def test_agents_does_not_have_haccp_key(self):
        """Verifica que AGENTS NO tenga la clave 'haccp' (el nombre antiguo)"""
        assert "haccp" not in AGENTS, "AGENTS no debe contener la clave 'haccp' obsoleta"
    
    def test_iso17025_agent_has_correct_name(self):
        """Verifica que el agente iso17025 tenga el nombre correcto"""
        expected_name = "🧪 Experto ISO 17025"
        assert AGENTS["iso17025"]["name"] == expected_name, \
            f"El nombre del agente debe ser '{expected_name}'"
    
    def test_iso17025_agent_has_correct_folder(self):
        """Verifica que el agente iso17025 apunte a la carpeta correcta"""
        expected_folder = "ISO17025"
        assert AGENTS["iso17025"]["folder"] == expected_folder, \
            f"La carpeta del agente debe ser '{expected_folder}'"
    
    def test_iso17025_agent_has_description_with_iso17025(self):
        """Verifica que la descripción del agente mencione ISO 17025"""
        description = AGENTS["iso17025"]["desc"]
        assert "ISO 17025" in description, \
            f"La descripción debe mencionar 'ISO 17025', pero es: '{description}'"
    
    def test_iso17025_agent_description_not_empty(self):
        """Verifica que el agente iso17025 tenga una descripción no vacía"""
        description = AGENTS["iso17025"]["desc"]
        assert description and len(description.strip()) > 0, \
            "El agente debe tener una descripción no vacía"


class TestAgentMigrationLogic:
    """Tests para validar la lógica de migración en get_user_agent()"""
    
    def test_get_user_agent_returns_iso17025_for_haccp_legacy(self, tmp_path):
        """Verifica que get_user_agent() devuelva 'iso17025' cuando el usuario tenía 'haccp'"""
        # Crear un archivo de settings temporal con agente 'haccp' antiguo
        settings_content = json.dumps({"12345": {"agent": "haccp"}})
        settings_file = tmp_path / "user_settings.json"
        settings_file.write_text(settings_content, encoding='utf-8')
        
        # Importar y parchear el módulo para usar el archivo temporal
        with patch('core.context_manager.SETTINGS_FILE', str(settings_file)):
            # Importar después del patch para que use la ruta correcta
            from core.context_manager import get_user_agent
            result = get_user_agent(12345)
            assert result == "iso17025", \
                f"get_user_agent() debe devolver 'iso17025' para usuarios con 'haccp' legacy, pero devolvió: '{result}'"
    
    def test_get_user_agent_returns_iso17025_for_new_user(self, tmp_path):
        """Verifica que get_user_agent() devuelva 'iso17025' cuando el usuario eligió 'iso17025'"""
        settings_content = json.dumps({"12345": {"agent": "iso17025"}})
        settings_file = tmp_path / "user_settings.json"
        settings_file.write_text(settings_content, encoding='utf-8')
        
        with patch('core.context_manager.SETTINGS_FILE', str(settings_file)):
            from core.context_manager import get_user_agent
            result = get_user_agent(12345)
            assert result == "iso17025", \
                f"get_user_agent() debe devolver 'iso17025' para usuarios que eligieron 'iso17025', pero devolvió: '{result}'"
    
    def test_get_user_agent_returns_general_by_default(self, tmp_path):
        """Verifica que get_user_agent() devuelva 'general' por defecto para usuarios nuevos"""
        settings_content = json.dumps({})  # Sin usuarios
        settings_file = tmp_path / "user_settings.json"
        settings_file.write_text(settings_content, encoding='utf-8')
        
        with patch('core.context_manager.SETTINGS_FILE', str(settings_file)):
            from core.context_manager import get_user_agent
            result = get_user_agent(99999)  # Usuario que no existe
            assert result == "general", \
                f"get_user_agent() debe devolver 'general' por defecto, pero devolvió: '{result}'"
    
    def test_get_user_agent_does_not_return_haccp(self, tmp_path):
        """Verifica que get_user_agent() NUNCA devuelva 'haccp'"""
        settings_content = json.dumps({"12345": {"agent": "haccp"}})
        settings_file = tmp_path / "user_settings.json"
        settings_file.write_text(settings_content, encoding='utf-8')
        
        with patch('core.context_manager.SETTINGS_FILE', str(settings_file)):
            from core.context_manager import get_user_agent
            result = get_user_agent(12345)
            assert result != "haccp", \
                f"get_user_agent() NUNCA debe devolver 'haccp', pero devolvió: '{result}'"


class TestAgentStructure:
    """Tests para validar la estructura de los agentes"""
    
    def test_all_agents_have_required_fields(self):
        """Verifica que todos los agentes tengan los campos requeridos"""
        required_fields = ["name", "desc", "folder"]
        for agent_id, agent_data in AGENTS.items():
            for field in required_fields:
                assert field in agent_data, \
                    f"El agente '{agent_id}' debe tener el campo '{field}'"
    
    def test_iso17025_agent_is_not_general(self):
        """Verifica que el agente iso17025 no sea el agente general"""
        assert AGENTS["iso17025"]["folder"] is not None, \
            "El agente iso17025 debe tener una carpeta asignada (no None)"
        assert AGENTS["iso17025"]["folder"] != "", \
            "El agente iso17025 debe tener una carpeta no vacía"
    
    def test_agents_count(self):
        """Verifica que haya exactamente 3 agentes definidos"""
        expected_agents = ["general", "bitbread", "iso17025"]
        assert len(AGENTS) == 3, \
            f"Debe haber exactamente 3 agentes: {expected_agents}"
        for agent in expected_agents:
            assert agent in AGENTS, \
                f"El agente '{agent}' debe estar definido en AGENTS"


class TestAgentBackwardCompatibility:
    """Tests para validar la compatibilidad hacia atrás"""
    
    def test_general_agent_unchanged(self):
        """Verifica que el agente general no haya cambiado"""
        assert AGENTS["general"]["name"] == "🌐 IA General"
        assert AGENTS["general"]["folder"] is None
    
    def test_bitbread_agent_unchanged(self):
        """Verifica que el agente bitbread no haya cambiado"""
        assert AGENTS["bitbread"]["name"] == "🛠️ Soporte BitBread"
        assert AGENTS["bitbread"]["folder"] == "BitBread"
