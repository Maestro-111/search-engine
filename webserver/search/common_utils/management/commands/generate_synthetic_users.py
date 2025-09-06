from typing import List, Dict
from faker import Faker

from django.core.management.base import BaseCommand
from user.models import SyntheticUser, UserPreference

import random

fake = Faker()

NUM_USERS = 100


class Command(BaseCommand):
    help = "Generate synthetic users with preferences"

    # Define preference mappings for each persona
    PERSONA_PREFERENCES = {
        "developer": {
            "titles": [
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "C++",
                "C#",
                "Go",
                "Rust",
                "Docker",
                "Kubernetes",
                "Git",
                "GitLab",
                "GitHub",
                "AWS",
                "Azure",
                "GCP",
                "MongoDB",
                "PostgreSQL",
                "MySQL",
                "Redis",
                "ElasticSearch",
                "Cassandra",
                "React",
                "Vue.js",
                "Angular",
                "Node.js",
                "Express",
                "Django",
                "Flask",
                "Spring Boot",
                "FastAPI",
                "GraphQL",
                "REST API",
                "gRPC",
                "WebSocket",
                "Jenkins",
                "CircleCI",
                "Terraform",
                "Ansible",
                "Prometheus",
                "Grafana",
                "Nginx",
                "Apache",
                "Linux",
                "Ubuntu",
                "CentOS",
                "VS Code",
                "IntelliJ",
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
                "refactoring",
                "code review",
                "version control",
                "containerization",
                "orchestration",
                "monitoring",
                "logging",
                "authentication",
                "authorization",
                "load balancing",
                "database optimization",
                "memory management",
                "concurrency",
                "multithreading",
                "design patterns",
                "clean code",
                "technical debt",
                "automated testing",
                "integration testing",
                "TDD",
                "agile",
                "scrum",
                "kanban",
                "DevOps",
                "infrastructure as code",
            ],
            "categories": [
                "Programming Languages",
                "Software Development",
                "Web Development",
                "Database Management",
                "Cloud Computing",
                "DevOps",
                "Mobile Development",
                "Backend Development",
                "Frontend Development",
                "Full Stack Development",
                "System Architecture",
                "Software Engineering",
                "API Development",
            ],
            "name": "developer",
        },
        "data_scientist": {
            "titles": [
                "pandas",
                "NumPy",
                "scikit-learn",
                "TensorFlow",
                "PyTorch",
                "Keras",
                "R",
                "SQL",
                "Spark",
                "Hadoop",
                "Matplotlib",
                "Seaborn",
                "Plotly",
                "Jupyter",
                "Anaconda",
                "Tableau",
                "Power BI",
                "Apache Airflow",
                "MLflow",
                "Kubeflow",
                "H2O.ai",
                "XGBoost",
                "LightGBM",
                "NLTK",
                "spaCy",
                "OpenCV",
                "statsmodels",
                "SciPy",
                "Dask",
                "CatBoost",
                "prophet",
                "ARIMA",
                "Apache Kafka",
                "Snowflake",
                "Databricks",
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
                "dimensionality reduction",
                "time series",
                "NLP",
                "computer vision",
                "ensemble methods",
                "hyperparameter tuning",
                "model evaluation",
                "overfitting",
                "underfitting",
                "bias-variance tradeoff",
                "A/B testing",
                "hypothesis testing",
                "correlation",
                "causation",
                "data mining",
                "predictive modeling",
                "anomaly detection",
                "recommendation systems",
                "reinforcement learning",
                "transfer learning",
                "ETL",
                "data pipeline",
                "big data",
                "real-time analytics",
                "model deployment",
                "MLOps",
            ],
            "categories": [
                "Data Science",
                "Machine Learning",
                "Artificial Intelligence",
                "Statistics",
                "Big Data",
                "Data Analysis",
                "Deep Learning",
                "Natural Language Processing",
                "Computer Vision",
                "Data Engineering",
                "Business Intelligence",
                "Predictive Analytics",
                "Data Visualization",
                "Statistical Analysis",
                "MLOps",
                "Data Mining",
            ],
            "name": "data_scientist",
        },
        "business_analyst": {
            "titles": [
                "Excel",
                "Tableau",
                "Power BI",
                "SQL",
                "Google Analytics",
                "Salesforce",
                "SAP",
                "Jira",
                "Confluence",
                "Monday.com",
                "Asana",
                "Trello",
                "Looker",
                "Qlik",
                "SAS",
                "SPSS",
                "R",
                "Python",
                "Alteryx",
                "Palantir",
                "Sisense",
                "Domo",
                "Microsoft Project",
                "Visio",
                "Lucidchart",
                "Miro",
                "Figma",
                "Adobe Analytics",
                "Mixpanel",
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
                "process improvement",
                "workflow",
                "business case",
                "cost-benefit analysis",
                "market research",
                "competitive analysis",
                "user stories",
                "acceptance criteria",
                "gap analysis",
                "root cause analysis",
                "SWOT analysis",
                "trend analysis",
                "performance metrics",
                "conversion rates",
                "customer segmentation",
                "churn analysis",
                "cohort analysis",
                "funnel analysis",
                "benchmarking",
                "business process modeling",
                "requirements gathering",
                "documentation",
                "project management",
                "change management",
                "risk assessment",
            ],
            "categories": [
                "Business Intelligence",
                "Data Analytics",
                "Business Analysis",
                "Project Management",
                "Enterprise Software",
                "Process Improvement",
                "Requirements Analysis",
                "Performance Management",
                "Financial Analysis",
                "Market Research",
                "Strategic Planning",
                "Operations Analysis",
                "Customer Analytics",
                "Digital Analytics",
                "Business Process Management",
            ],
            "name": "business_analyst",
        },
        "researcher": {
            "titles": [
                "SPSS",
                "R",
                "Python",
                "MATLAB",
                "SAS",
                "Stata",
                "LaTeX",
                "Mendeley",
                "Zotero",
                "EndNote",
                "RefWorks",
                "Google Scholar",
                "PubMed",
                "Scopus",
                "Web of Science",
                "JSTOR",
                "ResearchGate",
                "Academia.edu",
                "arXiv",
                "bioRxiv",
                "Overleaf",
                "NVivo",
                "ATLAS.ti",
                "MaxQDA",
                "Qualtrics",
                "Survey Monkey",
                "REDCap",
                "OpenRefine",
                "Gephi",
                "Cytoscape",
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
                "research design",
                "sampling",
                "data collection",
                "survey design",
                "interview protocols",
                "ethnography",
                "case study",
                "grounded theory",
                "content analysis",
                "statistical significance",
                "p-values",
                "confidence intervals",
                "effect size",
                "power analysis",
                "randomized controlled trial",
                "observational study",
                "longitudinal study",
                "cross-sectional",
                "validity",
                "reliability",
                "generalizability",
                "ethics",
                "IRB",
                "informed consent",
                "replication",
                "reproducibility",
                "open science",
            ],
            "categories": [
                "Research Methods",
                "Academic Writing",
                "Scientific Computing",
                "Data Analysis",
                "Publishing",
                "Quantitative Research",
                "Qualitative Research",
                "Mixed Methods",
                "Statistical Analysis",
                "Literature Review",
                "Grant Writing",
                "Research Ethics",
                "Peer Review",
                "Academic Career",
                "Open Science",
                "Reproducibility",
            ],
            "name": "researcher",
        },
        "student": {
            "titles": [
                "Khan Academy",
                "Coursera",
                "edX",
                "Udemy",
                "Udacity",
                "Pluralsight",
                "LinkedIn Learning",
                "Skillshare",
                "MasterClass",
                "YouTube",
                "Wikipedia",
                "Stack Overflow",
                "GitHub",
                "CodePen",
                "Replit",
                "Google Docs",
                "Notion",
                "Obsidian",
                "Anki",
                "Quizlet",
                "Duolingo",
                "Grammarly",
                "Chegg",
                "Course Hero",
                "Wolfram Alpha",
                "Desmos",
                "GeoGebra",
                "Zoom",
                "Discord",
                "Slack",
                "Microsoft Teams",
                "Google Classroom",
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
                "practice problems",
                "flashcards",
                "note-taking",
                "study tips",
                "exam preparation",
                "assignment help",
                "group study",
                "peer learning",
                "mentorship",
                "internships",
                "scholarships",
                "career guidance",
                "skill development",
                "certification",
                "degree programs",
                "bootcamps",
                "workshops",
                "webinars",
                "office hours",
                "study groups",
                "academic support",
                "time management",
                "productivity",
                "learning strategies",
                "motivation",
            ],
            "categories": [
                "Education",
                "Online Learning",
                "Tutorials",
                "Study Resources",
                "MOOCs",
                "Educational Technology",
                "Academic Support",
                "Skill Development",
                "Career Preparation",
                "Certification Programs",
                "Study Techniques",
                "Learning Management",
                "Peer Learning",
                "Academic Writing",
                "Test Preparation",
                "Language Learning",
                "STEM Education",
            ],
            "name": "student",
        },
        "historian": {
            "titles": [
                "Ancient Rome",
                "Ancient Greece",
                "Ancient Egypt",
                "Medieval Europe",
                "Renaissance",
                "Reformation",
                "Enlightenment",
                "Industrial Revolution",
                "American Civil War",
                "World War I",
                "World War II",
                "Cold War",
                "French Revolution",
                "Russian Revolution",
                "Chinese History",
                "Japanese History",
                "Islamic History",
                "African History",
                "Latin American History",
                "Byzantine Empire",
                "Ottoman Empire",
                "British Empire",
                "Mongol Empire",
                "Vikings",
                "Crusades",
                "Black Death",
                "Age of Exploration",
                "Colonial America",
                "American Revolution",
                "Napoleonic Wars",
                "Victorian Era",
                "Roaring Twenties",
            ],
            "content_keywords": [
                "historical events",
                "primary sources",
                "secondary sources",
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
                "political history",
                "economic history",
                "military history",
                "diplomatic history",
                "intellectual history",
                "gender history",
                "labor history",
                "environmental history",
                "oral history",
                "historiography",
                "historical methodology",
                "periodization",
                "causation",
                "continuity",
                "change",
                "historical interpretation",
                "bias",
                "perspective",
                "historical context",
                "anachronism",
                "historical significance",
                "evidence",
                "historical thinking",
                "comparative history",
                "microhistory",
                "public history",
            ],
            "categories": [
                "History",
                "Military History",
                "Ancient History",
                "Medieval History",
                "Modern History",
                "Contemporary History",
                "Historical Analysis",
                "Archaeological Studies",
                "Cultural Studies",
                "Political History",
                "Social History",
                "Economic History",
                "Intellectual History",
                "Gender Studies",
                "Historical Methodology",
                "Public History",
                "Comparative History",
                "World History",
                "Regional History",
            ],
            "name": "historian",
        },
        "hr": {
            "titles": [
                "LinkedIn",
                "Indeed",
                "Glassdoor",
                "ZipRecruiter",
                "Monster",
                "CareerBuilder",
                "Workday",
                "BambooHR",
                "ADP",
                "Paychex",
                "UltiPro",
                "SuccessFactors",
                "Cornerstone OnDemand",
                "Greenhouse",
                "Lever",
                "JazzHR",
                "Taleo",
                "iCIMS",
                "SmartRecruiters",
                "SHRM",
                "PHR",
                "SPHR",
                "CIPD",
                "PeopleSoft",
                "Oracle HCM",
                "SAP SuccessFactors",
                "Kronos",
                "15Five",
                "Culture Amp",
                "Officevibe",
                "TINYpulse",
                "Bonusly",
                "Lattice",
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
                "performance management",
                "succession planning",
                "workforce planning",
                "employee relations",
                "conflict resolution",
                "disciplinary actions",
                "termination",
                "exit interviews",
                "HRIS",
                "payroll",
                "time tracking",
                "leave management",
                "wellness programs",
                "employee recognition",
                "career development",
                "leadership development",
                "organizational culture",
                "change management",
                "labor relations",
                "employment law",
                "FMLA",
                "ADA",
                "EEOC",
                "harassment prevention",
                "background checks",
                "reference checks",
                "job analysis",
                "competency mapping",
            ],
            "categories": [
                "Human Resources",
                "Talent Management",
                "Recruitment",
                "Employee Relations",
                "HR Technology",
                "Organizational Development",
                "Compensation and Benefits",
                "Performance Management",
                "Training and Development",
                "Employment Law",
                "Diversity and Inclusion",
                "Employee Engagement",
                "HR Analytics",
                "Workforce Planning",
                "Organizational Psychology",
                "Labor Relations",
                "HR Information Systems",
                "Talent Acquisition",
                "Learning and Development",
            ],
            "name": "hr",
        },
        "marketing": {
            "titles": [
                "Google Ads",
                "Facebook Ads",
                "Instagram",
                "TikTok",
                "LinkedIn Ads",
                "Twitter",
                "YouTube",
                "Snapchat",
                "Pinterest",
                "Google Analytics",
                "HubSpot",
                "Mailchimp",
                "Constant Contact",
                "ConvertKit",
                "Klaviyo",
                "Hootsuite",
                "Buffer",
                "Sprout Social",
                "Later",
                "Canva",
                "Adobe Creative Suite",
                "Figma",
                "Sketch",
                "WordPress",
                "Squarespace",
                "Wix",
                "Shopify",
                "Salesforce",
                "Pardot",
                "Marketo",
                "Unbounce",
                "Leadpages",
                "Optimizely",
                "Hotjar",
                "Mixpanel",
                "Amplitude",
                "SEMrush",
                "Ahrefs",
                "Moz",
            ],
            "content_keywords": [
                "brand awareness",
                "lead generation",
                "conversion rate",
                "customer acquisition",
                "retention",
                "segmentation",
                "targeting",
                "personalization",
                "A/B testing",
                "content marketing",
                "SEO",
                "SEM",
                "social media marketing",
                "email marketing",
                "influencer marketing",
                "affiliate marketing",
                "video marketing",
                "podcast marketing",
                "webinar marketing",
                "event marketing",
                "PR",
                "brand positioning",
                "value proposition",
                "customer journey",
                "sales funnel",
                "marketing automation",
                "CRM",
                "attribution modeling",
                "ROI",
                "ROAS",
                "CTR",
                "CPC",
                "CPM",
                "lifetime value",
                "churn rate",
                "engagement rate",
                "organic reach",
                "paid media",
                "earned media",
                "owned media",
                "omnichannel",
                "growth hacking",
            ],
            "categories": [
                "Digital Marketing",
                "Content Marketing",
                "Social Media Marketing",
                "Email Marketing",
                "Search Engine Marketing",
                "Brand Management",
                "Marketing Analytics",
                "Growth Marketing",
                "Product Marketing",
                "Performance Marketing",
                "Marketing Automation",
                "Customer Experience",
                "Advertising",
                "Public Relations",
                "Event Marketing",
                "Influencer Marketing",
                "Marketing Strategy",
                "Marketing Technology",
                "Conversion Optimization",
            ],
            "name": "marketing",
        },
        "finance": {
            "titles": [
                "Excel",
                "Bloomberg Terminal",
                "Reuters Eikon",
                "QuickBooks",
                "SAP",
                "Oracle Financial",
                "Sage",
                "Xero",
                "FreshBooks",
                "Wave",
                "Mint",
                "YNAB",
                "Personal Capital",
                "Tableau",
                "Power BI",
                "R",
                "Python",
                "MATLAB",
                "SAS",
                "SQL",
                "Access",
                "Alteryx",
                "Palantir",
                "FactSet",
                "Morningstar",
                "Yahoo Finance",
                "Google Finance",
                "TradingView",
                "MetaTrader",
                "Thinkorswim",
                "E*TRADE",
                "Robinhood",
                "Fidelity",
                "Charles Schwab",
                "Interactive Brokers",
                "Vanguard",
            ],
            "content_keywords": [
                "financial analysis",
                "budgeting",
                "forecasting",
                "valuation",
                "DCF",
                "NPV",
                "IRR",
                "WACC",
                "beta",
                "alpha",
                "portfolio management",
                "risk management",
                "asset allocation",
                "diversification",
                "hedging",
                "derivatives",
                "options",
                "futures",
                "bonds",
                "stocks",
                "ETFs",
                "mutual funds",
                "REITs",
                "commodities",
                "forex",
                "cryptocurrency",
                "financial modeling",
                "scenario analysis",
                "sensitivity analysis",
                "Monte Carlo simulation",
                "VaR",
                "stress testing",
                "compliance",
                "audit",
                "internal controls",
                "GAAP",
                "IFRS",
                "SOX",
                "Basel III",
                "liquidity",
                "solvency",
                "profitability",
                "efficiency ratios",
                "credit analysis",
                "due diligence",
                "M&A",
                "IPO",
                "capital markets",
            ],
            "categories": [
                "Finance",
                "Investment Banking",
                "Corporate Finance",
                "Financial Analysis",
                "Portfolio Management",
                "Risk Management",
                "Financial Planning",
                "Accounting",
                "Tax Planning",
                "Insurance",
                "Real Estate Finance",
                "Quantitative Finance",
                "Behavioral Finance",
                "Financial Technology",
                "Regulatory Compliance",
                "Financial Markets",
                "Banking",
                "Private Equity",
                "Venture Capital",
                "Wealth Management",
                "Financial Modeling",
            ],
            "name": "finance",
        },
        "designer": {
            "titles": [
                "Figma",
                "Sketch",
                "Adobe XD",
                "InVision",
                "Principle",
                "Framer",
                "Zeplin",
                "Marvel",
                "Axure",
                "Balsamiq",
                "Miro",
                "Whimsical",
                "Adobe Creative Suite",
                "Photoshop",
                "Illustrator",
                "InDesign",
                "After Effects",
                "Premiere Pro",
                "Lightroom",
                "Canva",
                "Procreate",
                "Blender",
                "Cinema 4D",
                "Maya",
                "3ds Max",
                "Unity",
                "Unreal Engine",
                "Webflow",
                "WordPress",
                "Squarespace",
                "Wix",
                "Shopify",
                "Dribbble",
                "Behance",
                "Awwwards",
                "Muzli",
                "Pinterest",
                "Unsplash",
                "Pexels",
            ],
            "content_keywords": [
                "user experience",
                "user interface",
                "usability",
                "accessibility",
                "user research",
                "personas",
                "user journey",
                "wireframes",
                "prototypes",
                "mockups",
                "design system",
                "style guide",
                "brand identity",
                "logo design",
                "typography",
                "color theory",
                "layout",
                "composition",
                "visual hierarchy",
                "white space",
                "grid system",
                "responsive design",
                "mobile first",
                "interaction design",
                "animation",
                "microinteractions",
                "motion graphics",
                "information architecture",
                "navigation",
                "user testing",
                "A/B testing",
                "conversion optimization",
                "design thinking",
                "human-centered design",
                "inclusive design",
                "universal design",
                "design sprint",
                "agile design",
                "design ops",
                "design tokens",
                "component library",
                "atomic design",
                "design handoff",
                "design collaboration",
                "design feedback",
                "iteration",
            ],
            "categories": [
                "User Experience Design",
                "User Interface Design",
                "Graphic Design",
                "Web Design",
                "Mobile Design",
                "Product Design",
                "Brand Design",
                "Motion Graphics",
                "3D Design",
                "Design Systems",
                "Design Research",
                "Interaction Design",
                "Visual Design",
                "Service Design",
                "Design Strategy",
                "Design Thinking",
                "Accessibility Design",
                "Design Operations",
                "Print Design",
                "Digital Design",
                "Creative Direction",
            ],
            "name": "designer",
        },
        "healthcare": {
            "titles": [
                "Epic",
                "Cerner",
                "Allscripts",
                "athenahealth",
                "eClinicalWorks",
                "NextGen",
                "Practice Fusion",
                "DrChrono",
                "Kareo",
                "SimplePractice",
                "TherapyNotes",
                "TheraNest",
                "WebPT",
                "Therabill",
                "MEDITECH",
                "McKesson",
                "GE Healthcare",
                "Philips Healthcare",
                "Siemens Healthineers",
                "PubMed",
                "UpToDate",
                "Medscape",
                "WebMD",
                "Mayo Clinic",
                "Cleveland Clinic",
                "Johns Hopkins",
                "FDA",
                "CDC",
                "WHO",
                "NIH",
                "CMS",
                "HIPAA",
                "HL7",
                "FHIR",
                "ICD-10",
                "CPT",
                "SNOMED",
                "LOINC",
            ],
            "content_keywords": [
                "patient care",
                "clinical documentation",
                "medical records",
                "diagnosis",
                "treatment plans",
                "medication management",
                "patient safety",
                "quality improvement",
                "evidence-based medicine",
                "clinical guidelines",
                "best practices",
                "healthcare quality",
                "patient outcomes",
                "clinical research",
                "clinical trials",
                "pharmacology",
                "pathophysiology",
                "anatomy",
                "physiology",
                "medical imaging",
                "laboratory results",
                "vital signs",
                "patient monitoring",
                "infection control",
                "healthcare technology",
                "telemedicine",
                "electronic health records",
                "health information systems",
                "clinical decision support",
                "population health",
                "public health",
                "epidemiology",
                "biostatistics",
                "healthcare analytics",
                "medical coding",
                "billing",
                "insurance",
                "compliance",
                "accreditation",
                "patient privacy",
                "medical ethics",
                "informed consent",
                "healthcare policy",
            ],
            "categories": [
                "Healthcare",
                "Medicine",
                "Nursing",
                "Clinical Research",
                "Healthcare Technology",
                "Medical Informatics",
                "Public Health",
                "Healthcare Administration",
                "Healthcare Quality",
                "Patient Safety",
                "Medical Education",
                "Telemedicine",
                "Healthcare Analytics",
                "Healthcare Policy",
                "Medical Ethics",
                "Pharmacy",
                "Medical Devices",
                "Healthcare Innovation",
                "Digital Health",
                "Precision Medicine",
            ],
            "name": "healthcare",
        },
        "educator": {
            "titles": [
                "Canvas",
                "Blackboard",
                "Moodle",
                "Google Classroom",
                "Schoology",
                "Edmodo",
                "Seesaw",
                "ClassDojo",
                "Remind",
                "Kahoot",
                "Quizizz",
                "Padlet",
                "Flipgrid",
                "Nearpod",
                "Pear Deck",
                "Mentimeter",
                "Zoom",
                "Microsoft Teams",
                "Google Meet",
                "Turnitin",
                "Grammarly",
                "Prezi",
                "Canva",
                "Adobe Creative Suite",
                "Screencastify",
                "Loom",
                "Camtasia",
                "OBS Studio",
                "Audacity",
                "GarageBand",
                "Scratch",
                "Code.org",
                "Khan Academy",
                "Coursera",
                "edX",
                "Udemy",
                "TED-Ed",
                "YouTube",
                "Common Core",
                "IEP",
                "504 Plan",
                "PBIS",
                "RTI",
                "UDL",
            ],
            "content_keywords": [
                "curriculum development",
                "lesson planning",
                "assessment",
                "differentiation",
                "scaffolding",
                "bloom's taxonomy",
                "learning objectives",
                "rubrics",
                "formative assessment",
                "summative assessment",
                "authentic assessment",
                "peer assessment",
                "self-assessment",
                "feedback",
                "grading",
                "standards",
                "learning outcomes",
                "pedagogical approaches",
                "teaching strategies",
                "classroom management",
                "behavior management",
                "engagement",
                "motivation",
                "inclusive education",
                "special needs",
                "gifted education",
                "ESL",
                "multilingual learners",
                "cultural responsiveness",
                "equity",
                "diversity",
                "collaboration",
                "critical thinking",
                "problem solving",
                "creativity",
                "digital literacy",
                "media literacy",
                "21st century skills",
                "STEM",
                "STEAM",
                "project-based learning",
                "inquiry-based learning",
                "flipped classroom",
            ],
            "categories": [
                "Education",
                "Curriculum Development",
                "Educational Technology",
                "Assessment",
                "Classroom Management",
                "Special Education",
                "Educational Leadership",
                "Professional Development",
                "Educational Research",
                "Online Learning",
                "Blended Learning",
                "Distance Education",
                "Educational Psychology",
                "Learning Sciences",
                "Instructional Design",
                "Academic Administration",
                "Higher Education",
                "K-12 Education",
                "Adult Education",
                "Continuing Education",
            ],
            "name": "educator",
        },
    }

    def handle(self, *args, **kwargs):

        SyntheticUser.objects.all().delete()
        users_created = 0

        for _ in range(NUM_USERS):

            primary_persona = random.choice(list(self.PERSONA_PREFERENCES.keys()))

            persona_name = fake.name()
            personas = [primary_persona]

            if random.random() < 0.3:
                secondary = random.choice(
                    [p for p in self.PERSONA_PREFERENCES.keys() if p != primary_persona]
                )

                personas.append(secondary)

                if random.random() < 0.3:

                    third = random.choice(
                        [
                            p
                            for p in self.PERSONA_PREFERENCES.keys()
                            if p != primary_persona and p != secondary
                        ]
                    )
                    personas.append(third)

            importance = 1.0

            for _, persona in enumerate(personas):
                expertise = self._get_expertise_for_persona(persona)

                user = SyntheticUser.objects.create(
                    name=persona_name,
                    persona=persona,
                    importance=importance,
                    expertise_level=expertise,
                )

                self._add_user_preferences(user, persona, expertise)

                users_created += 1
                importance *= 0.5

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {users_created} synthetic users")
        )

    def _get_expertise_for_persona(self, persona: str) -> str:
        """Get expertise level based on persona"""

        if persona in ["student", "marketing", "designer"]:
            return random.choices(
                ["beginner", "intermediate", "expert"], weights=[0.6, 0.3, 0.1]
            )[0]
        elif persona in ["developer", "data_scientist", "finance", "educator"]:
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
        self, user: SyntheticUser, num_entities: int = 10
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

        for _ in range(num_entities):
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
            "explaining {title}",
            "how to {title}",
            "{title} guide",
            "{title} basics",
            "{title} fundamentals",
            "{title} introduction",
            "{title} overview",
            "{title} walkthrough",
            "{title} step by step",
            "{title} beginner guide",
            "{title} advanced",
            "{title} tips and tricks",
            "{title} best practices",
            "{title} crash course",
            "{title} quick start",
            "{title} deep dive",
            "{title} masterclass",
            "{title} complete guide",
            "{title} handbook",
            "{title} reference",
            "{title} cheat sheet",
            "{title} workshop",
            "{title} training",
            "{title} course",
            "{title} lessons",
            "{title} how-to",
            "{title} setup",
        ],
        "keywords_only": [
            "{keywords}",
            "guide to {keywords}",
            "{keywords} tutorial",
            "understanding {keywords}",
            "{keywords} best practices",
            "how to {keywords}",
            "{keywords} examples",
            "samples of {keywords}",
            "{keywords} examinations",
            "{keywords} basics",
            "{keywords} fundamentals",
            "{keywords} introduction",
            "{keywords} overview",
            "{keywords} walkthrough",
            "{keywords} step by step",
            "{keywords} beginner guide",
            "{keywords} advanced",
            "{keywords} tips and tricks",
            "{keywords} crash course",
            "{keywords} quick start",
            "{keywords} deep dive",
            "{keywords} masterclass",
            "{keywords} complete guide",
            "{keywords} handbook",
            "{keywords} reference",
            "{keywords} cheat sheet",
            "{keywords} workshop",
            "{keywords} training",
            "{keywords} course",
            "{keywords} lessons",
            "{keywords} how-to",
            "{keywords} strategies",
            "{keywords} techniques",
            "{keywords} methods",
        ],
        "category_only": [
            "{category} resources",
            "best {category}",
            "{category} guide",
            "introduction to {category}",
            "{category} tutorials",
            "learn {category}",
            "{category} basics",
            "{category} fundamentals",
            "{category} overview",
            "{category} essentials",
            "{category} principles",
            "{category} concepts",
            "{category} theory",
            "{category} practice",
            "{category} applications",
            "{category} examples",
            "{category} case studies",
            "{category} use cases",
            "{category} scenarios",
            "{category} strategies",
            "{category} techniques",
            "{category} methods",
            "{category} approaches",
            "{category} frameworks",
            "{category} models",
            "{category} patterns",
            "{category} solutions",
            "{category} tools",
            "{category} software",
            "{category} platforms",
            "{category} systems",
        ],
        "title_keywords": [
            "{title} {keywords}",
            "{title} for {keywords}",
            "{keywords} with {title}",
            "{title} {keywords} tutorial",
            "using {title} for {keywords}",
            "{keywords} in {title}",
            "{title} {keywords} guide",
            "{title} {keywords} examples",
            "{title} {keywords} best practices",
            "{title} {keywords} tips",
            "{title} {keywords} techniques",
            "{title} {keywords} strategies",
            "{title} {keywords} methods",
            "{title} {keywords} approaches",
            "{title} {keywords} solutions",
            "{title} {keywords} implementation",
            "{title} {keywords} setup",
            "{title} {keywords} configuration",
            "{title} {keywords} optimization",
            "{title} {keywords} troubleshooting",
            "{title} {keywords} debugging",
            "{title} {keywords} performance",
            "{title} {keywords} security",
            "{title} {keywords} integration",
            "{title} {keywords} workflow",
            "{title} {keywords} automation",
            "{title} {keywords} advanced",
            "{title} {keywords} master",
            "{title} {keywords} expert",
            "{title} {keywords} professional",
            "{title} {keywords} complete",
        ],
        "title_category": [
            "{title} {category}",
            "{title} in {category}",
            "{category} with {title}",
            "best {title} for {category}",
            "{title} for {category}",
            "{category} using {title}",
            "{title} {category} guide",
            "{title} {category} tutorial",
            "{title} {category} examples",
            "{title} {category} best practices",
            "{title} {category} tips",
            "{title} {category} techniques",
            "{title} {category} strategies",
            "{title} {category} methods",
            "{title} {category} approaches",
            "{title} {category} solutions",
            "{title} {category} implementation",
            "{title} {category} setup",
            "{title} {category} configuration",
            "{title} {category} optimization",
            "{title} {category} troubleshooting",
            "{title} {category} debugging",
            "{title} {category} performance",
            "{title} {category} security",
            "{title} {category} integration",
            "{title} {category} workflow",
            "{title} {category} automation",
            "{title} {category} advanced",
            "{title} {category} master",
        ],
        "keywords_category": [
            "{keywords} {category}",
            "{category} {keywords}",
            "{keywords} for {category}",
            "{category} {keywords} guide",
            "{keywords} in {category}",
            "{category} with {keywords}",
            "{keywords} {category} tutorial",
            "{keywords} {category} examples",
            "{keywords} {category} best practices",
            "{keywords} {category} tips",
            "{keywords} {category} techniques",
            "{keywords} {category} strategies",
            "{keywords} {category} methods",
            "{keywords} {category} approaches",
            "{keywords} {category} solutions",
            "{keywords} {category} implementation",
            "{keywords} {category} setup",
            "{keywords} {category} configuration",
            "{keywords} {category} optimization",
            "{keywords} {category} troubleshooting",
            "{keywords} {category} debugging",
            "{keywords} {category} performance",
            "{keywords} {category} security",
            "{keywords} {category} integration",
            "{keywords} {category} workflow",
            "{keywords} {category} automation",
            "{keywords} {category} advanced",
            "{keywords} {category} master",
            "{keywords} {category} expert",
            "{keywords} {category} professional",
        ],
        "all": [
            "{title} {keywords} {category}",
            "{category} {title} {keywords}",
            "{keywords} using {title} in {category}",
            "{title} for {keywords} {category}",
            "{title} {keywords} {category} guide",
            "{title} {keywords} {category} tutorial",
            "{title} {keywords} {category} examples",
            "{title} {keywords} {category} best practices",
            "{title} {keywords} {category} tips",
            "{title} {keywords} {category} techniques",
            "{title} {keywords} {category} strategies",
            "{title} {keywords} {category} methods",
            "{title} {keywords} {category} approaches",
            "{title} {keywords} {category} solutions",
            "{title} {keywords} {category} implementation",
            "{title} {keywords} {category} setup",
            "{title} {keywords} {category} configuration",
            "{title} {keywords} {category} optimization",
            "{title} {keywords} {category} troubleshooting",
            "{title} {keywords} {category} debugging",
            "{title} {keywords} {category} performance",
            "{title} {keywords} {category} security",
            "{title} {keywords} {category} integration",
            "{title} {keywords} {category} workflow",
            "{title} {keywords} {category} automation",
            "{title} {keywords} {category} advanced",
            "{title} {keywords} {category} master",
            "{title} {keywords} {category} expert",
            "{title} {keywords} {category} professional",
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
