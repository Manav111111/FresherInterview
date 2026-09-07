"""
Fresher.AI Knowledge Base — Data Package Initialization
Exposes all sheet data providers and header definitions.
"""

from .roles import get_roles, get_roles_headers
from .foundation import get_foundation_skills, get_foundation_headers
from .skills import get_role_specific_skills, get_skills_headers
from .weekly_roadmaps import get_weekly_roadmaps, get_weekly_roadmaps_headers
from .projects import get_projects, get_projects_headers
from .resources import get_resources, get_resource_headers
from .youtube_channels import get_youtube_channels, get_youtube_headers, get_playlists, get_playlists_headers
from .interview_questions import get_interview_questions, get_interview_questions_headers
from .resume_keywords import get_resume_keywords, get_resume_keywords_headers
from .skill_matrix import get_skill_matrix, get_skill_matrix_headers
from .market_signals import get_market_signals, get_market_signals_headers
from .certifications import get_certifications, get_certifications_headers
from .tools_platforms import get_tools_platforms, get_tools_platforms_headers
from .common_mistakes import get_common_mistakes, get_common_mistakes_headers
from .day_in_the_life import get_day_in_the_life, get_day_in_the_life_headers
from .career_transitions import get_career_transitions, get_career_transitions_headers
from .metadata_schema import get_metadata_schema, get_metadata_schema_headers

SHEETS_REGISTRY = [
    {"name": "Roles", "data_fn": get_roles, "headers_fn": get_roles_headers},
    {"name": "Foundation", "data_fn": get_foundation_skills, "headers_fn": get_foundation_headers},
    {"name": "Skills", "data_fn": get_role_specific_skills, "headers_fn": get_skills_headers},
    {"name": "Weekly_Roadmaps", "data_fn": get_weekly_roadmaps, "headers_fn": get_weekly_roadmaps_headers},
    {"name": "Projects", "data_fn": get_projects, "headers_fn": get_projects_headers},
    {"name": "Resources", "data_fn": get_resources, "headers_fn": get_resource_headers},
    {"name": "YouTube_Channels", "data_fn": get_youtube_channels, "headers_fn": get_youtube_headers},
    {"name": "Interview_Questions", "data_fn": get_interview_questions, "headers_fn": get_interview_questions_headers},
    {"name": "Resume_Keywords", "data_fn": get_resume_keywords, "headers_fn": get_resume_keywords_headers},
    {"name": "Skill_Matrix", "data_fn": get_skill_matrix, "headers_fn": get_skill_matrix_headers},
    {"name": "Market_Signals", "data_fn": get_market_signals, "headers_fn": get_market_signals_headers},
    {"name": "Certifications", "data_fn": get_certifications, "headers_fn": get_certifications_headers},
    {"name": "Tools_Platforms", "data_fn": get_tools_platforms, "headers_fn": get_tools_platforms_headers},
    {"name": "Common_Mistakes", "data_fn": get_common_mistakes, "headers_fn": get_common_mistakes_headers},
    {"name": "Day_In_The_Life", "data_fn": get_day_in_the_life, "headers_fn": get_day_in_the_life_headers},
    {"name": "Career_Transitions", "data_fn": get_career_transitions, "headers_fn": get_career_transitions_headers},
    {"name": "Metadata_Schema", "data_fn": get_metadata_schema, "headers_fn": get_metadata_schema_headers},
]
