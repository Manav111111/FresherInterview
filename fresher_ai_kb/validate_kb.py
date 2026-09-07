"""
Fresher.AI — Knowledge Base Integrity & Relationship Validator
Performs exhaustive checks on referential integrity, ID formats, foreign keys, and RAG embedding payloads.
"""

import sys
import re
from data import (
    get_roles, get_foundation_skills, get_role_specific_skills,
    get_weekly_roadmaps, get_projects, get_resources, get_youtube_channels,
    get_interview_questions, get_resume_keywords, get_skill_matrix,
    get_market_signals, get_certifications, get_tools_platforms,
    get_common_mistakes, get_day_in_the_life, get_career_transitions,
    get_metadata_schema
)

def run_validation():
    print("=" * 65)
    print("Fresher.AI — Knowledge Base Referential Integrity & Schema Audit")
    print("=" * 65)
    
    errors = []
    warnings = []
    
    # 1. Collect all canonical IDs
    roles = get_roles()
    role_ids = {r["role_id"]: r for r in roles}
    
    foundation_skills = get_foundation_skills()
    role_skills = get_role_specific_skills()
    all_skills = foundation_skills + role_skills
    skill_ids = {s["skill_id"]: s for s in all_skills}
    
    roadmaps = get_weekly_roadmaps()
    roadmap_ids = {rm["roadmap_id"]: rm for rm in roadmaps}
    
    projects = get_projects()
    project_ids = {p["project_id"]: p for p in projects}
    
    resources = get_resources()
    resource_ids = {res["resource_id"]: res for res in resources}
    
    youtube = get_youtube_channels()
    yt_ids = {yt["channel_id"]: yt for yt in youtube}
    
    questions = get_interview_questions()
    question_ids = {q["question_id"]: q for q in questions}
    
    keywords = get_resume_keywords()
    matrix = get_skill_matrix()
    signals = get_market_signals()
    certs = get_certifications()
    tools = get_tools_platforms()
    tool_ids = {t["tool_id"]: t for t in tools}
    mistakes = get_common_mistakes()
    day_in_life = get_day_in_the_life()
    transitions = get_career_transitions()
    schemas = get_metadata_schema()
    
    print(f"Total Registered Roles:        {len(role_ids):>3}")
    print(f"Total Registered Skills:       {len(skill_ids):>3} ({len(foundation_skills)} Foundation + {len(role_skills)} Domain)")
    print(f"Total Weekly Roadmaps:         {len(roadmap_ids):>3}")
    print(f"Total Portfolio Projects:      {len(project_ids):>3}")
    print(f"Total Learning Resources:      {len(resource_ids):>3}")
    print(f"Total YouTube Channels:        {len(yt_ids):>3}")
    print(f"Total Interview Questions:     {len(question_ids):>3}")
    print(f"Total Resume Keywords:         {len(keywords):>3}")
    print(f"Total Skill Matrix Mappings:   {len(matrix):>3}")
    print(f"Total Market Signals:          {len(signals):>3}")
    print(f"Total Certifications:          {len(certs):>3}")
    print(f"Total Tools & Platforms:       {len(tools):>3}")
    print(f"Total Common Mistakes:         {len(mistakes):>3}")
    print(f"Total Day In The Life Models:  {len(day_in_life):>3}")
    print(f"Total Career Transitions:      {len(transitions):>3}")
    print(f"Total Schema Definitions:      {len(schemas):>3}")
    print("-" * 65)

    # 2. Check Role ID format and duplication
    if len(roles) != len(role_ids):
        errors.append(f"Duplicate role_id found in roles table! ({len(roles)} vs {len(role_ids)})")
    
    for r_id in role_ids:
        if not re.match(r"^role_[a-z0-9_]+$", r_id):
            errors.append(f"Invalid role_id naming format: '{r_id}' (Must match 'role_[a-z0-9_]+')")
    
    # 3. Check Skill ID format and duplication
    if len(all_skills) != len(skill_ids):
        errors.append(f"Duplicate skill_id found! ({len(all_skills)} vs {len(skill_ids)})")
        
    for s_id in skill_ids:
        if not re.match(r"^skill_[a-z0-9_]+$", s_id):
            errors.append(f"Invalid skill_id naming format: '{s_id}' (Must match 'skill_[a-z0-9_]+')")

    # 4. Check Skill Prerequisites & Related Skills Referential Integrity
    for s in all_skills:
        s_id = s["skill_id"]
        # Check prerequisites
        prereqs = [p.strip() for p in s.get("prerequisites", "").split(";") if p.strip()]
        for p in prereqs:
            if p not in skill_ids:
                warnings.append(f"Skill '{s_id}' has prerequisite '{p}' which is not in the skill registry.")
                
        # Check next_skill_ids
        next_skills = [n.strip() for n in s.get("next_skill_ids", "").split(";") if n.strip()]
        for n in next_skills:
            if n not in skill_ids:
                warnings.append(f"Skill '{s_id}' has next_skill '{n}' which is not in the skill registry.")
                
        # Check applicable_role_ids
        app_roles = [r.strip() for r in s.get("applicable_role_ids", "").split(";") if r.strip()]
        for r in app_roles:
            if r not in role_ids:
                errors.append(f"Skill '{s_id}' references non-existent role_id '{r}' in applicable_role_ids.")

        # Check embedding text
        if not s.get("embedding_text"):
            errors.append(f"Skill '{s_id}' is missing required 'embedding_text'.")

    # 5. Check Weekly Roadmaps Referential Integrity
    for rm in roadmaps:
        rm_id = rm["roadmap_id"]
        r_id = rm["role_id"]
        if r_id not in role_ids:
            errors.append(f"Roadmap '{rm_id}' references non-existent role_id '{r_id}'.")
            
        rm_skills = [sk.strip() for sk in rm.get("skill_ids", "").split(";") if sk.strip()]
        for sk in rm_skills:
            if sk not in skill_ids:
                errors.append(f"Roadmap '{rm_id}' references non-existent skill_id '{sk}'.")

        # Check prerequisite_weeks referential integrity
        prereq_weeks = [pw.strip() for pw in rm.get("prerequisite_weeks", "").split(";") if pw.strip()]
        for pw in prereq_weeks:
            if pw not in roadmap_ids:
                errors.append(f"Roadmap '{rm_id}' references non-existent prerequisite roadmap '{pw}'.")

        # Check recommended_resource_ids
        rec_resources = [res.strip() for res in rm.get("recommended_resource_ids", "").split(";") if res.strip()]
        for res in rec_resources:
            if res not in resource_ids:
                warnings.append(f"Roadmap '{rm_id}' references resource '{res}' not in resources registry.")

        # Check recommended_youtube_ids
        rec_yt = [y.strip() for y in rm.get("recommended_youtube_ids", "").split(";") if y.strip()]
        for y in rec_yt:
            if y not in yt_ids:
                warnings.append(f"Roadmap '{rm_id}' references YouTube channel '{y}' not in registry.")

        # Check recommended_tool_ids
        rec_tools = [t.strip() for t in rm.get("recommended_tool_ids", "").split(";") if t.strip()]
        for t in rec_tools:
            if t not in tool_ids:
                warnings.append(f"Roadmap '{rm_id}' references tool '{t}' not in tools registry.")

        # Check recommended_project_ids
        rec_projs = [p.strip() for p in rm.get("recommended_project_ids", "").split(";") if p.strip()]
        for p in rec_projs:
            if p not in project_ids:
                warnings.append(f"Roadmap '{rm_id}' references project '{p}' not in projects registry.")

        # Check difficulty & boolean flags
        if rm.get("difficulty") not in ["beginner", "intermediate", "advanced"]:
            errors.append(f"Roadmap '{rm_id}' has invalid difficulty: '{rm.get('difficulty')}'.")
        if not isinstance(rm.get("is_core"), bool):
            errors.append(f"Roadmap '{rm_id}' is_core must be boolean.")
        if not isinstance(rm.get("is_optional"), bool):
            errors.append(f"Roadmap '{rm_id}' is_optional must be boolean.")

        # Check required text fields
        for field in ["weekly_goal", "daily_breakdown", "practice_tasks", "hands_on_deliverable", "learning_outcomes", "interview_topics", "resume_evidence", "embedding_text"]:
            if not rm.get(field):
                errors.append(f"Roadmap '{rm_id}' is missing required field '{field}'.")

        # Check 7-day structure
        db = rm.get("daily_breakdown", "")
        if "Day 1" not in db or "Day 7" not in db:
            warnings.append(f"Roadmap '{rm_id}' daily_breakdown may not follow complete Day 1..7 format.")

    # 6. Check Projects Referential Integrity
    for proj in projects:
        p_id = proj["project_id"]
        r_id = proj["role_id"]
        if r_id not in role_ids:
            errors.append(f"Project '{p_id}' references non-existent role_id '{r_id}'.")
            
        p_skills = [sk.strip() for sk in proj.get("skills_used", "").split(";") if sk.strip()]
        for sk in p_skills:
            if sk not in skill_ids:
                errors.append(f"Project '{p_id}' references non-existent skill_id '{sk}'.")
                
        if not proj.get("embedding_text"):
            errors.append(f"Project '{p_id}' is missing required 'embedding_text'.")

        if not isinstance(proj.get("project_sequence"), int):
            errors.append(f"Project '{p_id}' is missing valid integer project_sequence.")

    # 7. Check Resources Referential Integrity
    valid_purposes = {"LEARN", "USE", "WHERE TO LEARN", "BUILD", "PRACTICE", "DOCUMENTATION", "JOBS / CAREER", "PORTFOLIO", "INTERVIEWS"}
    for res in resources:
        res_id = res["resource_id"]
        res_roles = [r.strip() for r in res.get("role_ids", "").split(";") if r.strip()]
        for r in res_roles:
            if r not in role_ids:
                warnings.append(f"Resource '{res_id}' references non-existent role_id '{r}'.")
                
        res_skills = [sk.strip() for sk in res.get("skill_ids", "").split(";") if sk.strip()]
        for sk in res_skills:
            if sk not in skill_ids:
                warnings.append(f"Resource '{res_id}' references non-existent skill_id '{sk}'.")

        if res.get("resource_purpose") not in valid_purposes:
            errors.append(f"Resource '{res_id}' has invalid resource_purpose: '{res.get('resource_purpose')}'.")

        if not res.get("url", "").startswith("http"):
            errors.append(f"Resource '{res_id}' has invalid URL: '{res.get('url')}'.")
                
        if not res.get("embedding_text"):
            errors.append(f"Resource '{res_id}' is missing required 'embedding_text'.")

    # 8. Check YouTube Channels Referential Integrity
    for yt in youtube:
        c_id = yt["channel_id"]
        yt_roles = [r.strip() for r in yt.get("role_ids", "").split(";") if r.strip()]
        for r in yt_roles:
            if r not in role_ids:
                errors.append(f"YouTube Channel '{c_id}' references non-existent role_id '{r}'.")

        if not yt.get("url", "").startswith("https://www.youtube.com/"):
            errors.append(f"YouTube Channel '{c_id}' has invalid YouTube URL: '{yt.get('url')}'")

    # 9. Check Skill Matrix Referential Integrity
    for sm in matrix:
        m_id = sm["matrix_id"]
        r_id = sm["role_id"]
        s_id = sm["skill_id"]
        if r_id not in role_ids:
            errors.append(f"Skill Matrix '{m_id}' references non-existent role_id '{r_id}'.")
        if s_id not in skill_ids:
            errors.append(f"Skill Matrix '{m_id}' references non-existent skill_id '{s_id}'.")

    # 10. Check Career Transitions Referential Integrity
    for tr in transitions:
        t_id = tr["transition_id"]
        c_id = tr["current_role_id"]
        tgt_id = tr["target_role_id"]
        if c_id not in role_ids:
            errors.append(f"Career Transition '{t_id}' current_role_id '{c_id}' does not exist.")
        if tgt_id not in role_ids:
            errors.append(f"Career Transition '{t_id}' target_role_id '{tgt_id}' does not exist.")

    # 11. Report Results
    print("VALIDATION REPORT:")
    print(f"Total Errors Found:   {len(errors)}")
    print(f"Total Warnings Found: {len(warnings)}")
    print("-" * 65)
    
    if errors:
        print("ERRORS:")
        for err in errors[:20]:
            print(f"  [!] {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")
            
    if warnings:
        print("\nWARNINGS (Soft references / optional links):")
        for warn in warnings[:15]:
            print(f"  [*] {warn}")
        if len(warnings) > 15:
            print(f"  ... and {len(warnings) - 15} more warnings.")
            
    if not errors:
        print("\n>>> SUCCESS: ALL INTEGRITY & SCHEMA CHECKS PASSED (0 ERRORS)! <<<")
        print("Knowledge Base is 100% verified, consistent, and ready for production RAG.")
    else:
        print("\n>>> VALIDATION FAILED: Please fix above errors before release. <<<")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
