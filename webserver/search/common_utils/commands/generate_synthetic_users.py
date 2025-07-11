import os
import django
from typing import List, Dict
from faker import Faker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "search.settings.local")
django.setup()

from django.core.management.base import BaseCommand
from user.models import SyntheticUser, UserPreference

fake = Faker()


class Command(BaseCommand):
    help = "Generate synthetic users with preferences"

    # Define preference mappings for each persona
    PERSONA_PREFERENCES = {
        "developer": {
            "titles": [
                "Python",
                "JavaScript",
                "Docker",
                "Git",
                "AWS",
                "MongoDB",
                "ElasticSearch",
                "React",
                "Node.js",
                "Kubernetes",
                "Redis",
                "PostgreSQL",
                "GraphQL",
            ],
            "content_keywords": [
                "API",
                "debugging",
                "performance",
                "security",
                "deployment",
                "testing",
                "architecture",
                "microservices",
                "CI/CD",
                "async",
                "caching",
                "scalability",
            ],
            "categories": [
                "Programming Languages",
                "Software Development",
                "Web Development",
                "Database Management",
                "Cloud Computing",
                "DevOps",
            ],
            "name": "developer",
        },
        "data_scientist": {
            "titles": [
                "pandas",
                "scikit-learn",
                "TensorFlow",
                "R",
                "SQL",
                "Spark",
                "NumPy",
                "Matplotlib",
                "Keras",
                "PyTorch",
                "Jupyter",
            ],
            "content_keywords": [
                "machine learning",
                "statistics",
                "data visualization",
                "algorithms",
                "preprocessing",
                "neural networks",
                "deep learning",
                "feature engineering",
                "cross-validation",
                "regression",
                "classification",
                "clustering",
            ],
            "categories": [
                "Data Science",
                "Machine Learning",
                "Artificial Intelligence",
                "Statistics",
                "Big Data",
                "Data Analysis",
            ],
            "name": "data_scientist",
        },
        "business_analyst": {
            "titles": [
                "Excel",
                "Tableau",
                "PowerBI",
                "SQL",
                "Google Analytics",
                "Salesforce",
                "SAP",
                "Jira",
                "Confluence",
            ],
            "content_keywords": [
                "metrics",
                "KPIs",
                "reporting",
                "dashboards",
                "ROI",
                "analytics",
                "business intelligence",
                "data driven",
                "insights",
                "forecasting",
                "stakeholder",
                "requirements",
            ],
            "categories": [
                "Business Intelligence",
                "Data Analytics",
                "Business Analysis",
                "Project Management",
                "Enterprise Software",
            ],
            "name": "business_analyst",
        },
        "researcher": {
            "titles": [
                "SPSS",
                "LaTeX",
                "Mendeley",
                "Python",
                "R",
                "MATLAB",
                "EndNote",
                "Zotero",
                "Google Scholar",
                "PubMed",
            ],
            "content_keywords": [
                "methodology",
                "literature review",
                "experiments",
                "analysis",
                "publications",
                "peer review",
                "hypothesis",
                "quantitative",
                "qualitative",
                "meta-analysis",
                "systematic review",
                "citation",
            ],
            "categories": [
                "Research Methods",
                "Academic Writing",
                "Scientific Computing",
                "Data Analysis",
                "Publishing",
            ],
            "name": "researcher",
        },
        "student": {
            "titles": [
                "Khan Academy",
                "Coursera",
                "edX",
                "Udemy",
                "Wikipedia",
                "Stack Overflow",
                "GitHub",
                "Google Docs",
            ],
            "content_keywords": [
                "tutorials",
                "basics",
                "homework",
                "projects",
                "learning paths",
                "beginner friendly",
                "study guide",
                "examples",
                "exercises",
                "free resources",
                "online courses",
                "video tutorials",
            ],
            "categories": [
                "Education",
                "Online Learning",
                "Tutorials",
                "Study Resources",
                "MOOCs",
                "Educational Technology",
            ],
            "name": "student",
        },
        "historian": {
            "titles": [
                "Ancient Rome",
                "World War II",
                "Medieval Europe",
                "Renaissance",
                "American Civil War",
                "Ancient Egypt",
                "Cold War",
                "French Revolution",
            ],
            "content_keywords": [
                "historical events",
                "primary sources",
                "archaeology",
                "archives",
                "chronology",
                "historical figures",
                "civilizations",
                "empires",
                "revolutions",
                "wars",
                "cultural history",
                "social history",
            ],
            "categories": [
                "History",
                "Military History",
                "Ancient History",
                "Modern History",
                "Historical Analysis",
                "Archaeological Studies",
            ],
            "name": "historian",
        },
        "hr": {
            "titles": [
                "LinkedIn",
                "Workday",
                "BambooHR",
                "ADP",
                "Indeed",
                "Glassdoor",
                "SHRM",
                "Performance Management",
            ],
            "content_keywords": [
                "recruitment",
                "employee engagement",
                "onboarding",
                "benefits",
                "compensation",
                "talent management",
                "HR policies",
                "compliance",
                "diversity",
                "inclusion",
                "retention",
                "training",
            ],
            "categories": [
                "Human Resources",
                "Talent Management",
                "Recruitment",
                "Employee Relations",
                "HR Technology",
                "Organizational Development",
            ],
            "name": "hr",
        },
    }

    def handle(self, *args, **kwargs):
        # Clear existing data
        SyntheticUser.objects.all().delete()

        users_created = 0

        for _ in range(100):
            # Each user can have 1-3 personas with decreasing importance
            primary_persona = random.choice(list(self.PERSONA_PREFERENCES.keys()))
            personas = [primary_persona]

            # 30% chance of having a secondary interest
            if random.random() < 0.3:
                secondary = random.choice(
                    [p for p in self.PERSONA_PREFERENCES.keys() if p != primary_persona]
                )
                personas.append(secondary)

            importance = 1.0

            for _, persona in enumerate(personas):
                expertise = self._get_expertise_for_persona(persona)

                user = SyntheticUser.objects.create(
                    name=f"{fake.name()} ({persona})",
                    persona=persona,
                    importance=importance,
                    expertise_level=expertise,
                )

                self._add_user_preferences(user, persona, expertise)
                users_created += 1

                # Decrease importance for secondary interests
                importance *= 0.5

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {users_created} synthetic users")
        )

    def _get_expertise_for_persona(self, persona: str) -> str:
        """Get expertise level based on persona"""
        if persona == "student":
            return random.choices(
                ["beginner", "intermediate", "expert"], weights=[0.6, 0.3, 0.1]
            )[0]
        elif persona in ["developer", "data_scientist"]:
            return random.choices(
                ["beginner", "intermediate", "expert"], weights=[0.2, 0.4, 0.4]
            )[0]
        else:
            return random.choices(
                ["beginner", "intermediate", "expert"], weights=[0.3, 0.5, 0.2]
            )[0]

    def _add_user_preferences(self, user: SyntheticUser, persona: str, expertise: str):
        """Add preferences for a user based on their persona"""
        prefs = self.PERSONA_PREFERENCES[persona]

        # Title preferences (1-3 titles)
        num_titles = random.randint(1, 3)
        selected_titles = random.sample(
            prefs["titles"], min(num_titles, len(prefs["titles"]))
        )

        for title in selected_titles:
            UserPreference.objects.create(
                user=user,
                preference_type="title",
                preference_value=title,
                weight=random.uniform(0.7, 1.0) * user.importance,
            )

        # Category preferences (2-4 categories)
        num_categories = random.randint(2, 4)
        selected_categories = random.sample(
            prefs["categories"], min(num_categories, len(prefs["categories"]))
        )

        for category in selected_categories:
            UserPreference.objects.create(
                user=user,
                preference_type="categories",
                preference_value=category,
                weight=random.uniform(0.5, 0.8) * user.importance,
            )

        # Content keyword preferences (3-5 keywords)
        num_keywords = random.randint(3, 5)
        selected_keywords = random.sample(
            prefs["content_keywords"], min(num_keywords, len(prefs["content_keywords"]))
        )

        for keyword in selected_keywords:
            UserPreference.objects.create(
                user=user,
                preference_type="content_keywords",
                preference_value=keyword,
                weight=random.uniform(0.4, 0.7) * user.importance,
            )


class EntityGenerator:
    """Generate realistic queries based on user profiles"""

    def generate_entities_for_user(
        self, user: SyntheticUser, num_queries: int = 10
    ) -> List[Dict[str, List[str]]]:
        """
        Generate queries that return the expected entity format for Elasticsearch
        Returns list of entity dictionaries like:
        {'title': 'Python', 'content_keywords': ['debugging', 'API'], 'categories': ['Programming Languages'], 'link_related': []}
        """
        entities = []

        # Get user preferences
        user_prefs = {
            "titles": list(
                user.preferences.filter(preference_type="title").values_list(
                    "preference_value", flat=True
                )
            ),
            "categories": list(
                user.preferences.filter(preference_type="categories").values_list(
                    "preference_value", flat=True
                )
            ),
            "content_keywords": list(
                user.preferences.filter(preference_type="content_keywords").values_list(
                    "preference_value", flat=True
                )
            ),
        }

        for _ in range(num_queries):
            # Generate query based on expertise level
            if user.expertise_level == "beginner":
                entity = self._generate_beginner_entity(user_prefs)
            elif user.expertise_level == "intermediate":
                entity = self._generate_intermediate_entity(user_prefs)
            else:
                entity = self._generate_expert_entity(user_prefs)

            entities.append(entity)

        return entities

    def _generate_beginner_entity(self, prefs: Dict) -> Dict:
        """Simple queries focusing on single concepts"""
        query_type = random.choice(["title_only", "keyword_focused", "category_browse"])

        if query_type == "title_only" and prefs["titles"]:
            return {
                "title": random.choice(prefs["titles"]),
                "content_keywords": [],
                "categories": [],
                "link_related": [],
            }
        elif query_type == "keyword_focused" and prefs["content_keywords"]:
            return {
                "title": "",
                "content_keywords": [random.choice(prefs["content_keywords"])],
                "categories": [],
                "link_related": [],
            }
        else:  # category browse
            return {
                "title": "",
                "content_keywords": [],
                "categories": (
                    [random.choice(prefs["categories"])] if prefs["categories"] else []
                ),
                "link_related": [],
            }

    def _generate_intermediate_entity(self, prefs: Dict) -> Dict:
        """Combine multiple search criteria"""
        entities = {
            "title": "",
            "content_keywords": [],
            "categories": [],
            "link_related": [],
        }

        # 60% chance to include title
        if random.random() < 0.6 and prefs["titles"]:
            entities["title"] = random.choice(prefs["titles"])

        # Add 1-2 keywords
        if prefs["content_keywords"]:
            num_keywords = random.randint(1, 2)
            entities["content_keywords"] = random.sample(
                prefs["content_keywords"],
                min(num_keywords, len(prefs["content_keywords"])),
            )

        # 40% chance to add category
        if random.random() < 0.4 and prefs["categories"]:
            entities["categories"] = [random.choice(prefs["categories"])]

        return entities

    def _generate_expert_entity(self, prefs: Dict) -> Dict:
        """Complex queries with multiple criteria"""
        entities = {
            "title": "",
            "content_keywords": [],
            "categories": [],
            "link_related": [],
        }

        # Experts often search for specific combinations
        if prefs["titles"] and random.random() < 0.3:
            entities["title"] = random.choice(prefs["titles"])

        # Add 2-3 keywords for precision
        if prefs["content_keywords"]:
            num_keywords = random.randint(2, 3)
            entities["content_keywords"] = random.sample(
                prefs["content_keywords"],
                min(num_keywords, len(prefs["content_keywords"])),
            )

        # Often use categories to filter
        if prefs["categories"]:
            num_categories = random.randint(1, 2)
            entities["categories"] = random.sample(
                prefs["categories"], min(num_categories, len(prefs["categories"]))
            )

        return entities


import random
from typing import Dict, List


class QueryFromEntityGenerator:
    """Generate natural language queries from entity structures"""

    QUERY_TEMPLATES = {
        "title_only": [
            "{title}",
            "{title} tutorial",
            "how to use {title}",
            "getting started with {title}",
            "{title} documentation",
            "learn {title}",
            "{title} examples",
            "what is {title}",
        ],
        "keywords_only": [
            "{keywords}",
            "guide to {keywords}",
            "{keywords} tutorial",
            "understanding {keywords}",
            "{keywords} best practices",
            "how to {keywords}",
            "{keywords} examples",
        ],
        "category_only": [
            "{category} resources",
            "best {category}",
            "{category} guide",
            "introduction to {category}",
            "{category} tutorials",
            "learn {category}",
        ],
        "title_keywords": [
            "{title} {keywords}",
            "{title} for {keywords}",
            "{keywords} with {title}",
            "{title} {keywords} tutorial",
            "using {title} for {keywords}",
            "{keywords} in {title}",
        ],
        "title_category": [
            "{title} {category}",
            "{title} in {category}",
            "{category} with {title}",
            "best {title} for {category}",
        ],
        "keywords_category": [
            "{keywords} {category}",
            "{category} {keywords}",
            "{keywords} for {category}",
            "{category} {keywords} guide",
        ],
        "all": [
            "{title} {keywords} {category}",
            "{category} {title} {keywords}",
            "{keywords} using {title} in {category}",
            "{title} for {keywords} {category}",
        ],
    }

    # Expertise level modifiers
    EXPERTISE_MODIFIERS = {
        "beginner": {
            "prefixes": ["simple", "basic", "beginner", "introduction to", "easy"],
            "suffixes": [
                "for beginners",
                "tutorial",
                "getting started",
                "basics",
                "simple example",
            ],
        },
        "intermediate": {
            "prefixes": ["practical", "advanced", "professional", "comprehensive"],
            "suffixes": [
                "best practices",
                "guide",
                "techniques",
                "implementation",
                "examples",
            ],
        },
        "expert": {
            "prefixes": [
                "advanced",
                "expert",
                "professional",
                "enterprise",
                "scalable",
            ],
            "suffixes": [
                "architecture",
                "optimization",
                "patterns",
                "at scale",
                "performance",
            ],
        },
    }

    def generate_query_from_entity(
        self, entity: Dict, user: "SyntheticUser" = None
    ) -> str:
        """
        Generate a natural language query from an entity structure

        Args:
            entity: Dict with keys 'title', 'content_keywords', 'categories', 'link_related'
            user: Optional SyntheticUser object to customize query based on expertise

        Returns:
            Natural language query string
        """
        # Determine what type of query to generate based on entity content
        query_type = self._determine_query_type(entity)

        # Select appropriate template
        templates = self.QUERY_TEMPLATES.get(
            query_type, self.QUERY_TEMPLATES["keywords_only"]
        )
        template = random.choice(templates)

        # Fill in the template
        query = self._fill_template(template, entity)

        # Add expertise modifiers if user is provided
        if user:
            query = self._add_expertise_modifiers(query, user.expertise_level)

        # Add random variations
        if random.random() < 0.2:
            query = self._add_variations(query)

        return query.strip()

    def _determine_query_type(self, entity: Dict) -> str:
        """Determine query type based on which fields are populated"""
        has_title = bool(entity.get("title"))
        has_keywords = bool(entity.get("content_keywords"))
        has_category = bool(entity.get("categories"))

        if has_title and has_keywords and has_category:
            return "all"
        elif has_title and has_keywords:
            return "title_keywords"
        elif has_title and has_category:
            return "title_category"
        elif has_keywords and has_category:
            return "keywords_category"
        elif has_title:
            return "title_only"
        elif has_keywords:
            return "keywords_only"
        elif has_category:
            return "category_only"
        else:
            return "keywords_only"  # fallback

    def _fill_template(self, template: str, entity: Dict) -> str:
        """Fill in template placeholders with entity data"""
        query = template

        # Replace title
        if "{title}" in query:
            title = entity.get("title", "")
            query = query.replace("{title}", title)

        # Replace keywords
        if "{keywords}" in query:
            keywords = entity.get("content_keywords", [])
            if keywords:
                # Join keywords naturally
                if len(keywords) == 1:
                    keywords_str = keywords[0]
                elif len(keywords) == 2:
                    keywords_str = f"{keywords[0]} and {keywords[1]}"
                else:
                    keywords_str = random.choice(
                        [
                            " ".join(keywords),
                            f"{keywords[0]} {keywords[1]}",
                            f"{' and '.join(keywords[:2])}",
                        ]
                    )
            else:
                keywords_str = ""
            query = query.replace("{keywords}", keywords_str)

        # Replace category
        if "{category}" in query:
            categories = entity.get("categories", [])
            category = categories[0] if categories else ""
            query = query.replace("{category}", category)

        return query

    def _add_expertise_modifiers(self, query: str, expertise_level: str) -> str:
        """Add expertise-appropriate modifiers to the query"""
        modifiers = self.EXPERTISE_MODIFIERS.get(expertise_level, {})

        # 30% chance to add prefix
        if random.random() < 0.3 and modifiers.get("prefixes"):
            prefix = random.choice(modifiers["prefixes"])
            query = f"{prefix} {query}"

        # 30% chance to add suffix
        if random.random() < 0.3 and modifiers.get("suffixes"):
            suffix = random.choice(modifiers["suffixes"])
            query = f"{query} {suffix}"

        return query

    def _add_variations(self, query: str) -> str:
        """Add realistic variations to queries"""
        variations = [
            lambda q: q + "?",  # Add question mark
            lambda q: f"how to {q}" if not q.startswith("how") else q,
            lambda q: f"best {q}" if not q.startswith("best") else q,
            lambda q: q.lower(),  # Make lowercase
            lambda q: q.replace(" and ", " "),  # Remove 'and'
        ]

        variation = random.choice(variations)
        return variation(query)
