"""
Fresher.AI — JSON Exporter & Qdrant Payload Generator
Exports all 17 sheets into production JSON formats ready for Qdrant vector database ingestion.
"""

import os
import json
from data import SHEETS_REGISTRY

def export_all_json(output_dir: str):
    print("=" * 60)
    print("Fresher.AI — Exporting Knowledge Base to JSON & Qdrant Format")
    print("=" * 60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    collections_map = {
        "Roles": "roles",
        "Foundation": "skills",
        "Skills": "skills",
        "Weekly_Roadmaps": "roadmaps",
        "Projects": "projects",
        "Resources": "resources",
        "YouTube_Channels": "resources",
        "Interview_Questions": "interview_prep",
        "Resume_Keywords": "resume_intel",
        "Skill_Matrix": "skill_matrix",
        "Market_Signals": "market_intel",
        "Certifications": "career_growth",
        "Tools_Platforms": "tools",
        "Common_Mistakes": "interview_prep",
        "Day_In_The_Life": "career_growth",
        "Career_Transitions": "career_growth",
        "Metadata_Schema": "meta"
    }
    
    qdrant_points = []
    full_kb = {}
    
    for sheet in SHEETS_REGISTRY:
        sheet_name = sheet["name"]
        data = sheet["data_fn"]()
        collection_name = collections_map.get(sheet_name, "misc")
        
        # Save individual sheet JSON
        file_name = f"{sheet_name.lower()}.json"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        full_kb[sheet_name] = data
        print(f"Exported: {file_name:<25} ({len(data):>3} items)")
        
        # Transform into Qdrant point payloads
        for item in data:
            # Determine ID
            point_id = (
                item.get("role_id") or
                item.get("skill_id") or
                item.get("roadmap_id") or
                item.get("project_id") or
                item.get("resource_id") or
                item.get("channel_id") or
                item.get("question_id") or
                item.get("keyword_id") or
                item.get("matrix_id") or
                item.get("signal_id") or
                item.get("cert_id") or
                item.get("tool_id") or
                item.get("mistake_id") or
                item.get("transition_id") or
                item.get("schema_id")
            )
            
            embedding_text = item.get("embedding_text", "")
            
            # Clean payload copy
            payload = dict(item)
            if "embedding_text" in payload:
                del payload["embedding_text"]
            
            # Split semicolon-delimited lists into actual JSON arrays
            for k, v in list(payload.items()):
                if isinstance(v, str) and ";" in v and not v.startswith("http"):
                    payload[k] = [x.strip() for x in v.split(";") if x.strip()]
            
            qdrant_point = {
                "id": point_id,
                "collection": collection_name,
                "entity_type": sheet_name,
                "payload": payload,
                "embedding_text": embedding_text
            }
            qdrant_points.append(qdrant_point)
    
    # Also export Playlists
    from data import get_playlists
    playlists_data = get_playlists()
    playlists_file = os.path.join(output_dir, "playlists.json")
    with open(playlists_file, "w", encoding="utf-8") as f:
        json.dump(playlists_data, f, indent=2, ensure_ascii=False)
    full_kb["Playlists"] = playlists_data
    print(f"Exported: {'playlists.json':<25} ({len(playlists_data):>3} items)")

    for pl in playlists_data:
        qdrant_points.append({
            "id": pl["playlist_id"],
            "collection": "resources",
            "entity_type": "Playlist",
            "payload": pl,
            "embedding_text": f"Playlist: {pl['playlist_name']}\nChannel: {pl['channel_name']}\nSkill: {pl['skill_area']}\nRole: {pl['role_area']}"
        })

    # Save full consolidated KB
    full_kb_path = os.path.join(output_dir, "fresher_ai_complete_knowledge_graph.json")
    with open(full_kb_path, "w", encoding="utf-8") as f:
        json.dump(full_kb, f, indent=2, ensure_ascii=False)
    
    # Save Qdrant ingestion payloads
    qdrant_path = os.path.join(output_dir, "qdrant_ingestion_payloads.json")
    with open(qdrant_path, "w", encoding="utf-8") as f:
        json.dump(qdrant_points, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"SUCCESS: Exported {len(qdrant_points)} Qdrant points to:\n{qdrant_path}")
    print(f"Consolidated Knowledge Graph saved to:\n{full_kb_path}")
    print("=" * 60)

if __name__ == "__main__":
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json_export")
    export_all_json(output_directory)
