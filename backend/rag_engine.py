import os
import json
import re

class LocalRAGEngine:
    def __init__(self):
        self.dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
        self.knowledge_base = []
        self.load_data()
        
    def load_data(self):
        # 1. Load Standards (Markdown)
        standards_dir = os.path.join(self.dataset_dir, "standards")
        if os.path.exists(standards_dir):
            for file in os.listdir(standards_dir):
                if file.endswith(".md"):
                    with open(os.path.join(standards_dir, file), "r", encoding="utf-8") as f:
                        content = f.read()
                        self.knowledge_base.append({
                            "source": f"standards/{file}",
                            "title": file.replace(".md", "").replace("_", " ").title(),
                            "content": content,
                            "type": "standard"
                        })
                        
        # 2. Load Process Templates (JSON)
        templates_dir = os.path.join(self.dataset_dir, "process_templates")
        if os.path.exists(templates_dir):
            for file in os.listdir(templates_dir):
                if file.endswith(".json"):
                    with open(os.path.join(templates_dir, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.knowledge_base.append({
                            "source": f"process_templates/{file}",
                            "title": f"{data.get('process_type')} Template",
                            "content": json.dumps(data, indent=2),
                            "type": "template"
                        })

        # 3. Load Tools (JSON)
        tools_dir = os.path.join(self.dataset_dir, "tools")
        if os.path.exists(tools_dir):
            for file in os.listdir(tools_dir):
                if file.endswith(".json"):
                    with open(os.path.join(tools_dir, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.knowledge_base.append({
                            "source": f"tools/{file}",
                            "title": f"{data.get('tool_type')} Documentation",
                            "content": json.dumps(data, indent=2),
                            "type": "tool"
                        })

        # 4. Load Materials (JSON)
        materials_dir = os.path.join(self.dataset_dir, "materials")
        if os.path.exists(materials_dir):
            for file in os.listdir(materials_dir):
                if file.endswith(".json"):
                    with open(os.path.join(materials_dir, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.knowledge_base.append({
                            "source": f"materials/{file}",
                            "title": f"{data.get('material_name')} Material Properties",
                            "content": json.dumps(data, indent=2),
                            "type": "material"
                        })

    def search(self, query: str, limit: int = 3):
        results = []
        query_words = re.findall(r'\w+', query.lower())
        
        for item in self.knowledge_base:
            score = 0
            content_lower = item["content"].lower()
            title_lower = item["title"].lower()
            
            for word in query_words:
                # Add score if word matches in title or content
                if word in title_lower:
                    score += 10
                if word in content_lower:
                    score += content_lower.count(word)
                    
            if score > 0:
                results.append({
                    "score": score,
                    "title": item["title"],
                    "source": item["source"],
                    "type": item["type"],
                    "content": item["content"]
                })
                
        # Sort by relevance score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

# Global instance of RAG search engine
rag_engine = LocalRAGEngine()
