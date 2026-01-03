import os
from core.config import DOCS_DIR

class KnowledgeManager:
    def __init__(self):
        self.docs_path = DOCS_DIR

    def _read_all_docs(self):
        """
        Recorre todas las carpetas en data/docs y carga los archivos .md
        Devuelve una lista de diccionarios: [{'tema': 'BitBread', 'archivo': 'bot.md', 'contenido': '...'}]
        """
        knowledge_base = []
        
        if not os.path.exists(self.docs_path):
            return knowledge_base

        # Recorrer carpetas recursivamente (os.walk)
        for root, dirs, files in os.walk(self.docs_path):
            for file in files:
                if file.endswith(".md") or file.endswith(".txt"):
                    try:
                        # El nombre de la carpeta padre sirve como "Categoría" o "Tema"
                        folder_name = os.path.basename(root)
                        file_path = os.path.join(root, file)
                        
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        knowledge_base.append({
                            "category": folder_name,
                            "filename": file,
                            "content": content
                        })
                    except Exception as e:
                        print(f"Error leyendo {file}: {e}")
        
        return knowledge_base

    def get_relevant_context(self, query):
        """
        Busca en los documentos fragmentos relevantes basados en la query del usuario.
        Sistema simple de coincidencia de palabras (Keyword Matching).
        """
        query_words = set(query.lower().split())
        docs = self._read_all_docs()
        relevant_chunks = []

        for doc in docs:
            # Puntuación simple: ¿Cuántas palabras de la pregunta están en el documento?
            score = 0
            doc_content_lower = doc["content"].lower()
            
            # Buscar coincidencia exacta de frases o palabras clave
            for word in query_words:
                if len(word) > 3 and word in doc_content_lower: # Ignorar palabras cortas (de, la, el)
                    score += 1
            
            # Si hay coincidencia relevante, agregamos el documento
            if score > 0:
                relevant_chunks.append((score, doc))

        # Ordenar por relevancia (mayor score primero) y tomar los top 3
        relevant_chunks.sort(key=lambda x: x[0], reverse=True)
        top_docs = relevant_chunks[:3]

        if not top_docs:
            return ""

        # Formatear el texto para enviarlo a la IA
        context_text = "\n--- INFORMACIÓN DE BASE DE CONOCIMIENTO ---\n"
        for score, doc in top_docs:
            context_text += (
                f"📂 Tema: {doc['category']} | Archivo: {doc['filename']}\n"
                f"{doc['content']}\n"
                f"---------------------------------------------\n"
            )
        
        return context_text

# Instancia global
knowledge_base = KnowledgeManager()