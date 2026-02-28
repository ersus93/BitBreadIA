import os
import re
import math
from collections import Counter
from core.config import DOCS_DIR
from unidecode import unidecode
from utils.logger import add_log_line

class KnowledgeManager:
    def __init__(self):
        self.docs_path = DOCS_DIR
        # Cargamos los documentos al iniciar
        self.docs_cache = self._read_all_docs() 
        print(f"📚 Base de Conocimiento cargada: {len(self.docs_cache)} fragmentos activos.")
        

    def _clean_text(self, text):
        """Limpia texto normalizando acentos y caracteres especiales."""
        text = unidecode(text).lower()
        return re.sub(r'[^\w\s]', '', text)
    
    def _read_all_docs(self):
        chunks_db = []
        if not os.path.exists(self.docs_path):
            print(f"⚠️ Alerta: No existe la carpeta {self.docs_path}")
            return chunks_db

        print(f"📚 Indexando base de conocimiento desde: {self.docs_path}")
        
        for root, dirs, files in os.walk(self.docs_path):
            # Detectar nombre de la carpeta actual
            # Si estamos en data/docs/ISO17025, folder_name será "ISO17025"
            # Si estamos en data/docs, folder_name será "docs" (o lo que sea el root)
            folder_name = os.path.basename(root)
            
            # Si la carpeta es la raíz de documentos, lo tratamos como 'general' o 'root'
            # (Opcional: ajusta esto según tu preferencia, aquí asumo que subcarpetas = categorias)
            is_root = os.path.abspath(root) == os.path.abspath(self.docs_path)
            category = "root" if is_root else folder_name

            for file in files:
                if file.lower().endswith((".md", ".txt")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Guardamos la categoría en el diccionario del chunk
                            chunks_db.append({
                                "content": self._clean_text(content), 
                                "original_content": content,
                                "filename": file,
                                "folder": category  # <--- NUEVO CAMPO IMPORTANTE
                            })
                    except Exception as e:
                        add_log_line(f"Error leyendo {file}: {e}")
        
        return chunks_db
    
    def _create_chunks(self, text, filename, chunk_size=800, category="general"):
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:                    
                    content_str = current_chunk.strip()
                    chunks.append({
                        'content': content_str,
                        'clean_content': self._clean_text(content_str),
                        'filename': filename,
                        'category': category 
                    })
                current_chunk = p + "\n\n"
        
        if current_chunk:
            content_str = current_chunk.strip()
            chunks.append({
                'content': content_str,
                'clean_content': self._clean_text(content_str),
                'filename': filename,
                'category': category
            })
            
        return chunks

    def get_relevant_context(self, query, filter_category=None):
        """
        Busca los fragmentos más relevantes.
        """
        query_clean = self._clean_text(query)
        #stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'y', 'o', 'que', 'en', 'por', 'para', 'con', 'se', 'su', 'es', 'al', 'lo', 'como', 'mas', 'pero', 'hola', 'buenos', 'dias'}
        
        query_words = self._clean_text(query).split()
        if not query_words:
            return ""

        scored_chunks = []

        for chunk in self.docs_cache:
            if filter_category and chunk.get('folder') != filter_category:
                continue
            score = 0
            chunk_content = chunk["clean_content"]
            chunk_filename = chunk["filename"].lower()
            
            # 1. Búsqueda exacta de frase (Prioridad Máxima)
            if query_clean in chunk_content:
                score += 60
            
            # 2. Coincidencia de palabras clave
            matches = 0
            for word in query_words:
                count = chunk_content.count(word)
                if count > 0:
                    matches += 1
                    score += (min(count, 5) * 4) # Ligero aumento de peso
            
            # 3. Bonificación por nombre de archivo
            for word in query_words:
                if word in chunk_filename:
                    score += 50 

            # 4. Penalización SUAVIZADA (Antes era muy agresiva)
            # Si el usuario busca "onie" y el archivo NO lo tiene en el nombre, 
            # pero SÍ en el contenido, no deberíamos matarlo tanto.
            if "onie" in query_words and "onie" not in chunk_filename:
                # Solo penalizamos si TAMPOCO aparece en el contenido frecuentemente
                if "onie" not in chunk_content:
                    score = score * 0.2 
            
            # 5. Densidad
            if len(query_words) > 0:
                match_percentage = matches / len(query_words)
                if match_percentage > 0.6: 
                    score = score * 1.5

            if score > 50:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Aumentamos a Top 4 para dar más contexto al LLM
        top_chunks = scored_chunks[:3]

        if not top_chunks:
            print(f"🔍 Búsqueda para '{query}': No se encontró contexto relevante.")
            return ""

        print(f"✅ Contexto encontrado ({len(top_chunks)} chunks). Scores: {[round(x[0],1) for x in top_chunks]}")
        # Debug para ver qué archivos está seleccionando
        print(f"   📂 Archivos seleccionados: {[x[1]['filename'] for x in top_chunks]}")

        MAX_CONTEXT_CHARS = 6000
        current_chars = 0
        context_text = "\n--- INFORMACIÓN OFICIAL DE LA BASE DE CONOCIMIENTO ---\n"
        
        for score, doc in top_chunks:
            # Si añadir este chunk supera el límite, paramos.
            if current_chars + len(doc['content']) > MAX_CONTEXT_CHARS:
                break
                
            context_text += f"📄 FUENTE: {doc['filename']}\n{doc['content']}\n\n"
            current_chars += len(doc['content'])
        
        return context_text

# Instancia global
knowledge_base = KnowledgeManager()