"""
Syllabus seed data and service.

Seeds the database with CBSE / ICSE / State-board subjects and chapters
for classes 8–12, with stream filtering for 11–12.
Also seeds competitive exam metadata (JEE, NEET).

Called once during app startup (idempotent — skips if data already exists).
"""

from __future__ import annotations

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subject, Chapter, CompetitiveExam

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Curriculum definitions
# ──────────────────────────────────────────────

# Common subjects for classes 8-10 (CBSE and State boards).
_COMMON_8_10 = [
    ("Mathematics", "calculate"),
    ("Science", "science"),
    ("Social Science", "public"),
    ("English", "menu_book"),
    ("Hindi", "translate"),
]

# ICSE subjects for classes 8-10 (separate sciences from class 9)
_ICSE_8 = [
    ("Mathematics", "calculate"),
    ("Science", "science"),
    ("Social Studies", "public"),
    ("English", "menu_book"),
    ("Hindi", "translate"),
]

_ICSE_9_10 = [
    ("Mathematics", "calculate"),
    ("Physics", "bolt"),
    ("Chemistry", "science"),
    ("Biology", "biotech"),
    ("History & Civics", "history_edu"),
    ("Geography", "public"),
    ("English", "menu_book"),
    ("Hindi", "translate"),
]

# Class 11-12 streams
_SCIENCE_11_12 = [
    ("Physics", "bolt"),
    ("Chemistry", "science"),
    ("Mathematics", "calculate"),
    ("Biology", "biotech"),
    ("English", "menu_book"),
]

_COMMERCE_11_12 = [
    ("Accountancy", "account_balance"),
    ("Business Studies", "business"),
    ("Economics", "trending_up"),
    ("Mathematics", "calculate"),
    ("English", "menu_book"),
]

_ARTS_11_12 = [
    ("History", "history_edu"),
    ("Political Science", "gavel"),
    ("Geography", "public"),
    ("Economics", "trending_up"),
    ("English", "menu_book"),
]


# NCERT-style chapter lists keyed by (subject, grade)
# Keeping it representative; full NCERT 2024-25 chapters.
_CHAPTERS: dict[tuple[str, int], list[str]] = {
    # ── Mathematics 8–10 (CBSE/State) ──
    ("Mathematics", 8): [
        "Rational Numbers", "Linear Equations in One Variable",
        "Understanding Quadrilaterals", "Practical Geometry",
        "Data Handling", "Squares and Square Roots",
        "Cubes and Cube Roots", "Comparing Quantities",
        "Algebraic Expressions and Identities", "Visualising Solid Shapes",
        "Mensuration", "Exponents and Powers",
        "Direct and Inverse Proportions", "Factorisation",
        "Introduction to Graphs", "Playing with Numbers",
    ],
    ("Mathematics", 9): [
        "Number Systems", "Polynomials", "Coordinate Geometry",
        "Linear Equations in Two Variables", "Introduction to Euclid's Geometry",
        "Lines and Angles", "Triangles", "Quadrilaterals",
        "Areas of Parallelograms and Triangles", "Circles",
        "Constructions", "Heron's Formula",
        "Surface Areas and Volumes", "Statistics", "Probability",
    ],
    ("Mathematics", 10): [
        "Real Numbers", "Polynomials", "Pair of Linear Equations in Two Variables",
        "Quadratic Equations", "Arithmetic Progressions",
        "Triangles", "Coordinate Geometry", "Introduction to Trigonometry",
        "Some Applications of Trigonometry", "Circles", "Constructions",
        "Areas Related to Circles", "Surface Areas and Volumes",
        "Statistics", "Probability",
    ],

    # ── Science 8–10 (CBSE/State — combined science) ──
    ("Science", 8): [
        "Crop Production and Management", "Microorganisms: Friend and Foe",
        "Synthetic Fibres and Plastics", "Materials: Metals and Non-Metals",
        "Coal and Petroleum", "Combustion and Flame",
        "Conservation of Plants and Animals", "Cell — Structure and Functions",
        "Reproduction in Animals", "Reaching the Age of Adolescence",
        "Force and Pressure", "Friction", "Sound",
        "Chemical Effects of Electric Current",
        "Some Natural Phenomena", "Light", "Stars and the Solar System",
        "Pollution of Air and Water",
    ],
    ("Science", 9): [
        "Matter in Our Surroundings", "Is Matter Around Us Pure",
        "Atoms and Molecules", "Structure of the Atom",
        "The Fundamental Unit of Life", "Tissues",
        "Diversity in Living Organisms", "Motion",
        "Force and Laws of Motion", "Gravitation",
        "Work and Energy", "Sound",
        "Why Do We Fall Ill", "Natural Resources",
        "Improvement in Food Resources",
    ],
    ("Science", 10): [
        "Chemical Reactions and Equations", "Acids, Bases and Salts",
        "Metals and Non-metals", "Carbon and its Compounds",
        "Periodic Classification of Elements",
        "Life Processes", "Control and Coordination",
        "How do Organisms Reproduce?",
        "Heredity and Evolution", "Light – Reflection and Refraction",
        "Human Eye and Colourful World", "Electricity",
        "Magnetic Effects of Electric Current", "Sources of Energy",
        "Our Environment", "Management of Natural Resources",
    ],

    # ── Social Science 8-10 (CBSE/State) ──
    ("Social Science", 8): [
        "How, When and Where", "From Trade to Territory",
        "Ruling the Countryside", "Tribals, Dikus and the Vision of a Golden Age",
        "The Indian Constitution", "Understanding Secularism",
        "Resources", "Land, Soil, Water, Natural Vegetation and Wildlife Resources",
    ],
    ("Social Science", 9): [
        "The French Revolution", "Socialism in Europe and the Russian Revolution",
        "Nazism and the Rise of Hitler", "Forest Society and Colonialism",
        "What is Democracy? Why Democracy?", "Constitutional Design",
        "Electoral Politics", "Working of Institutions",
        "The Story of Village Palampur", "People as Resource",
        "India — Size and Location", "Physical Features of India",
        "Drainage", "Climate", "Natural Vegetation and Wild Life",
    ],
    ("Social Science", 10): [
        "The Rise of Nationalism in Europe", "Nationalism in India",
        "The Making of a Global World", "The Age of Industrialisation",
        "Power Sharing", "Federalism", "Democracy and Diversity",
        "Gender, Religion and Caste", "Development",
        "Sectors of the Indian Economy", "Money and Credit",
        "Globalisation and the Indian Economy",
        "Resources and Development", "Forest and Wildlife Resources",
        "Water Resources", "Agriculture", "Minerals and Energy Resources",
        "Manufacturing Industries",
    ],

    # ── English 8–10 ──
    ("English", 8): ["The Best Christmas Present in the World", "The Tsunami", "Glimpses of the Past", "Bepin Choudhury's Lapse of Memory", "The Summit Within", "This is Jody's Fawn", "A Visit to Cambridge", "A Short Monsoon Diary"],
    ("English", 9): ["The Fun They Had", "The Sound of Music", "The Little Girl", "A Truly Beautiful Mind", "The Snake and the Mirror", "My Childhood", "Packing", "Reach for the Top", "The Bond of Love"],
    ("English", 10): ["A Letter to God", "Nelson Mandela: Long Walk to Freedom", "Two Stories about Flying", "From the Diary of Anne Frank", "The Hundred Dresses – I", "The Hundred Dresses – II", "Glimpses of India", "Mijbil the Otter", "Madam Rides the Bus", "The Sermon at Benares", "The Proposal"],

    # ── Hindi 8–10 ──
    ("Hindi", 8): ["ध्वनि", "लाख की चूड़ियाँ", "बस की यात्रा", "दीवानों की हस्ती", "चिट्ठियों की अनूठी दुनिया", "भगवान के डाकिये", "क्या निराश हुआ जाए", "यह सबसे कठिन समय नहीं"],
    ("Hindi", 9): ["दो बैलों की कथा", "ल्हासा की ओर", "उपभोक्तावाद की संस्कृति", "साँवले सपनों की याद", "नाना साहब की पुत्री देवी मैना को भस्म कर दिया गया", "प्रेमचंद के फटे जूते", "मेरे बचपन के दिन", "एक कुत्ता और एक मैना"],
    ("Hindi", 10): ["सूरदास के पद", "राम-लक्ष्मण-परशुराम संवाद", "आत्मकथ्य", "उत्साह और अट नहीं रही", "बालगोबिन भगत", "नेताजी का चश्मा", "बालगोबिन भगत", "एक कहानी यह भी"],

    # ── Physics 11-12 ──
    ("Physics", 11): [
        "Physical World", "Units and Measurements",
        "Motion in a Straight Line", "Motion in a Plane",
        "Laws of Motion", "Work, Energy and Power",
        "System of Particles and Rotational Motion", "Gravitation",
        "Mechanical Properties of Solids", "Mechanical Properties of Fluids",
        "Thermal Properties of Matter", "Thermodynamics",
        "Kinetic Theory", "Oscillations", "Waves",
    ],
    ("Physics", 12): [
        "Electric Charges and Fields", "Electrostatic Potential and Capacitance",
        "Current Electricity", "Moving Charges and Magnetism",
        "Magnetism and Matter", "Electromagnetic Induction",
        "Alternating Current", "Electromagnetic Waves",
        "Ray Optics and Optical Instruments", "Wave Optics",
        "Dual Nature of Radiation and Matter", "Atoms",
        "Nuclei", "Semiconductor Electronics",
    ],

    # ── Chemistry 11-12 ──
    ("Chemistry", 11): [
        "Some Basic Concepts of Chemistry", "Structure of Atom",
        "Classification of Elements and Periodicity in Properties",
        "Chemical Bonding and Molecular Structure",
        "States of Matter", "Thermodynamics",
        "Equilibrium", "Redox Reactions",
        "Hydrogen", "The s-Block Elements",
        "The p-Block Elements", "Organic Chemistry — Some Basic Principles",
        "Hydrocarbons", "Environmental Chemistry",
    ],
    ("Chemistry", 12): [
        "The Solid State", "Solutions",
        "Electrochemistry", "Chemical Kinetics",
        "Surface Chemistry", "General Principles and Processes of Isolation of Elements",
        "The p-Block Elements", "The d- and f-Block Elements",
        "Coordination Compounds", "Haloalkanes and Haloarenes",
        "Alcohols, Phenols and Ethers", "Aldehydes, Ketones and Carboxylic Acids",
        "Amines", "Biomolecules", "Polymers",
        "Chemistry in Everyday Life",
    ],

    # ── Biology 11-12 ──
    ("Biology", 11): [
        "The Living World", "Biological Classification",
        "Plant Kingdom", "Animal Kingdom",
        "Morphology of Flowering Plants", "Anatomy of Flowering Plants",
        "Structural Organisation in Animals", "Cell: The Unit of Life",
        "Biomolecules", "Cell Cycle and Cell Division",
        "Transport in Plants", "Mineral Nutrition",
        "Photosynthesis in Higher Plants", "Respiration in Plants",
        "Plant Growth and Development", "Digestion and Absorption",
        "Breathing and Exchange of Gases", "Body Fluids and Circulation",
        "Excretory Products and their Elimination",
        "Locomotion and Movement", "Neural Control and Coordination",
        "Chemical Coordination and Integration",
    ],
    ("Biology", 12): [
        "Reproduction in Organisms", "Sexual Reproduction in Flowering Plants",
        "Human Reproduction", "Reproductive Health",
        "Principles of Inheritance and Variation",
        "Molecular Basis of Inheritance", "Evolution",
        "Human Health and Disease", "Strategies for Enhancement in Food Production",
        "Microbes in Human Welfare",
        "Biotechnology: Principles and Processes",
        "Biotechnology and its Applications",
        "Organisms and Populations", "Ecosystem",
        "Biodiversity and Conservation",
        "Environmental Issues",
    ],

    # ── Mathematics 11-12 ──
    ("Mathematics", 11): [
        "Sets", "Relations and Functions", "Trigonometric Functions",
        "Principle of Mathematical Induction", "Complex Numbers and Quadratic Equations",
        "Linear Inequalities", "Permutations and Combinations",
        "Binomial Theorem", "Sequences and Series",
        "Straight Lines", "Conic Sections",
        "Introduction to Three Dimensional Geometry",
        "Limits and Derivatives", "Mathematical Reasoning",
        "Statistics", "Probability",
    ],
    ("Mathematics", 12): [
        "Relations and Functions", "Inverse Trigonometric Functions",
        "Matrices", "Determinants",
        "Continuity and Differentiability", "Application of Derivatives",
        "Integrals", "Application of Integrals",
        "Differential Equations", "Vector Algebra",
        "Three Dimensional Geometry", "Linear Programming",
        "Probability",
    ],

    # ── Accountancy 11-12 ──
    ("Accountancy", 11): [
        "Introduction to Accounting", "Theory Base of Accounting",
        "Recording of Transactions I", "Recording of Transactions II",
        "Bank Reconciliation Statement", "Trial Balance and Rectification of Errors",
        "Depreciation, Provisions and Reserves",
        "Bill of Exchange", "Financial Statements – I", "Financial Statements – II",
    ],
    ("Accountancy", 12): [
        "Accounting for Not-for-Profit Organisation",
        "Accounting for Partnership — Basic Concepts",
        "Reconstitution of a Partnership Firm — Admission of a Partner",
        "Reconstitution of a Partnership Firm — Retirement/Death of a Partner",
        "Dissolution of Partnership Firm",
        "Accounting for Share Capital", "Issue and Redemption of Debentures",
        "Financial Statements of a Company",
        "Analysis of Financial Statements",
        "Accounting Ratios", "Cash Flow Statement",
    ],

    # ── Business Studies 11-12 ──
    ("Business Studies", 11): [
        "Business, Trade and Commerce", "Forms of Business Organisation",
        "Private, Public and Global Enterprises", "Business Services",
        "Emerging Modes of Business", "Social Responsibility of Business",
        "Formation of a Company", "Sources of Business Finance",
        "Small Business", "Internal Trade", "International Business",
    ],
    ("Business Studies", 12): [
        "Nature and Significance of Management", "Principles of Management",
        "Business Environment", "Planning", "Organising",
        "Staffing", "Directing", "Controlling",
        "Financial Management", "Financial Markets",
        "Marketing Management", "Consumer Protection",
    ],

    # ── Economics 11-12 ──
    ("Economics", 11): [
        "Indian Economy on the Eve of Independence",
        "Indian Economy 1950–1990", "Liberalisation, Privatisation and Globalisation",
        "Poverty", "Human Capital Formation in India",
        "Rural Development", "Employment",
        "Infrastructure", "Environment and Sustainable Development",
        "Statistics for Economics", "Collection of Data",
        "Organisation of Data", "Presentation of Data",
        "Measures of Central Tendency", "Measures of Dispersion",
    ],
    ("Economics", 12): [
        "Introduction to Microeconomics", "Theory of Consumer Behaviour",
        "Production and Costs", "The Theory of the Firm under Perfect Competition",
        "Market Equilibrium",
        "Introduction to Macroeconomics", "National Income Accounting",
        "Money and Banking", "Determination of Income and Employment",
        "Government Budget and the Economy",
        "Open Economy Macroeconomics",
    ],

    # ── English 11-12 ──
    ("English", 11): ["The Portrait of a Lady", "We're Not Afraid to Die", "Discovering Tut", "Landscape of the Soul", "The Ailing Planet", "The Browning Version", "The Adventure", "Silk Road"],
    ("English", 12): ["The Last Lesson", "Lost Spring", "Deep Water", "The Rattrap", "Indigo", "Poets and Pancakes", "The Interview", "Going Places", "My Mother at Sixty-Six", "An Elementary School Classroom in a Slum", "Keeping Quiet", "A Thing of Beauty", "Aunt Jennifer's Tigers"],

    # ── History (Arts 11-12) ──
    ("History", 11): [
        "From the Beginning of Time", "Writing and City Life",
        "An Empire Across Three Continents", "The Central Islamic Lands",
        "Nomadic Empires", "The Three Orders",
        "Changing Cultural Traditions", "Confrontation of Cultures",
        "The Industrial Revolution", "Displacing Indigenous Peoples",
        "Paths to Modernisation",
    ],
    ("History", 12): [
        "Bricks, Beads and Bones", "Kings, Farmers and Towns",
        "Kinship, Caste and Class", "Thinkers, Beliefs and Buildings",
        "Through the Eyes of Travellers", "Bhakti-Sufi Traditions",
        "An Imperial Capital: Vijayanagara", "Peasants, Zamindars and the State",
        "Kings, Farmers and Towns", "Colonialism and the Countryside",
        "Rebels and the Raj", "Colonial Cities",
        "Mahatma Gandhi and the Nationalist Movement",
        "Understanding Partition", "Framing the Constitution",
    ],

    # ── Political Science (Arts 11-12) ──
    ("Political Science", 11): [
        "Political Theory: An Introduction", "Freedom",
        "Equality", "Social Justice", "Rights",
        "Citizenship", "Nationalism", "Secularism", "Peace",
        "Constitution: Why and How?", "Rights in the Indian Constitution",
        "Election and Representation", "Executive",
        "Legislature", "Judiciary", "Federalism",
        "Local Governments",
    ],
    ("Political Science", 12): [
        "The Cold War Era", "The End of Bipolarity",
        "US Hegemony in World Politics", "Alternative Centres of Power",
        "Contemporary South Asia", "International Organisations",
        "Security in the Contemporary World",
        "Environment and Natural Resources", "Globalisation",
        "Era of One-Party Dominance",
        "Nation Building and Its Problems",
        "Politics of Planned Development",
        "India's External Relations",
        "Challenges to and Restoration of the Congress System",
        "Rise of Popular Movements", "Regional Aspirations",
    ],

    # ── Geography (Arts 11-12) ──
    ("Geography", 11): [
        "Geography as a Discipline", "The Origin and Evolution of the Earth",
        "Interior of the Earth", "Distribution of Oceans and Continents",
        "Minerals and Rocks", "Geomorphic Processes",
        "Landforms and their Evolution",
        "Composition and Structure of Atmosphere",
        "Solar Radiation, Heat Balance and Temperature",
        "Atmospheric Circulation and Weather Systems",
        "Water in the Atmosphere", "World Climate and Climate Change",
        "Water (Oceans)", "Movements of Ocean Water",
        "Life on the Earth",
    ],
    ("Geography", 12): [
        "Human Geography: Nature and Scope", "The World Population",
        "Population Composition", "Human Development",
        "Primary Activities", "Secondary Activities",
        "Tertiary and Quaternary Activities",
        "Transport and Communication", "International Trade",
        "Human Settlements",
    ],
}

# ──────────────────────────────────────────────
#  ICSE-specific chapters (separate sciences in 9-10)
# ──────────────────────────────────────────────
_ICSE_CHAPTERS: dict[tuple[str, int], list[str]] = {
    # ── ICSE Social Studies 8 ──
    ("Social Studies", 8): [
        "The Rise of Nationalism", "The French Revolution",
        "The American War of Independence", "The Industrial Revolution",
        "The Indian National Movement (1857–1917)",
        "The Indian Constitution", "The Union Government",
        "The State Government", "Resources",
    ],

    # ── ICSE Physics 9 ──
    ("Physics", 9): [
        "Measurements and Experimentation", "Motion in One Dimension",
        "Laws of Motion", "Fluids", "Heat and Energy",
        "Light", "Sound", "Electricity and Magnetism",
    ],
    # ── ICSE Physics 10 ──
    ("Physics", 10): [
        "Force", "Work, Energy and Power",
        "Machines", "Refraction of Light at Plane Surfaces",
        "Refraction through a Lens", "Spectrum",
        "Sound", "Current Electricity",
        "Household Circuits", "Electro-magnetism",
        "Calorimetry", "Radioactivity",
    ],

    # ── ICSE Chemistry 9 ──
    ("Chemistry", 9): [
        "The Language of Chemistry", "Chemical Changes and Reactions",
        "Water", "Atomic Structure and Chemical Bonding",
        "The Periodic Table", "Study of the First Element — Hydrogen",
        "Study of Gas Laws", "Atmospheric Pollution",
    ],
    # ── ICSE Chemistry 10 ──
    ("Chemistry", 10): [
        "Periodic Table, Periodic Properties and their Variations",
        "Chemical Bonding", "Acids, Bases and Salts",
        "Analytical Chemistry", "Mole Concept and Stoichiometry",
        "Electrolysis", "Metallurgy",
        "Study of Compounds — Hydrogen Chloride",
        "Study of Compounds — Ammonia",
        "Study of Compounds — Nitric Acid",
        "Study of Compounds — Sulphuric Acid",
        "Organic Chemistry",
    ],

    # ── ICSE Biology 9 ──
    ("Biology", 9): [
        "Introducing Biology", "Cell: The Unit of Life",
        "Tissues: Plant and Animal Tissues", "The Flower",
        "Pollination and Fertilization", "Seeds — Structure and Germination",
        "Respiration in Plants", "Five Kingdom Classification",
        "Nutrition", "Digestive System", "Skeleton — Movement and Locomotion",
        "The Respiratory System", "Hygiene — A Key to Healthy Life",
    ],
    # ── ICSE Biology 10 ──
    ("Biology", 10): [
        "Cell Cycle, Cell Division and Structure of Chromosomes",
        "Genetics — Some Basic Fundamentals",
        "Absorption by Roots", "Transpiration",
        "Photosynthesis", "Chemical Coordination in Plants",
        "The Circulatory System", "The Excretory System",
        "The Nervous System and Sense Organs",
        "The Endocrine System",
        "The Reproductive System",
        "Population — The Increasing Numbers and Rising Problems",
        "Pollution — A Rising Environmental Problem",
    ],

    # ── ICSE History & Civics 9 ──
    ("History & Civics", 9): [
        "The Harappan Civilization", "The Vedic Period",
        "Jainism and Buddhism", "The Mauryan Empire",
        "The Gupta Period", "The Medieval Period",
        "The Mughal Empire", "The Composite Culture",
        "Our Parliament", "The Union Executive", "The Judiciary",
    ],
    # ── ICSE History & Civics 10 ──
    ("History & Civics", 10): [
        "The First War of Independence 1857",
        "Growth of Nationalism", "First Phase of the Indian National Movement",
        "Second Phase of the Indian National Movement",
        "Quit India Movement", "Subhas Chandra Bose and the INA",
        "Independence and Partition of India",
        "The United Nations", "Major Agencies of the United Nations",
        "Universal Declaration of Human Rights",
        "The Non-Aligned Movement",
    ],

    # ── ICSE Geography 9 ──
    ("Geography", 9): [
        "Our Earth", "Location, Extent and Physical Features of India",
        "Climate of India", "Soil Resources of India",
        "Natural Vegetation of India", "Water Resources of India",
        "Mineral Resources of India", "Population of India",
        "Map Work",
    ],
    # ── ICSE Geography 10 ──
    ("Geography", 10): [
        "Map Reading and Interpretation",
        "Climate of India", "Soil Resources in India",
        "Natural Vegetation", "Water Resources",
        "Minerals in India", "Energy Resources",
        "Manufacturing Industries", "Transport",
        "Waste Management",
    ],
}


# All boards that share NCERT-like syllabi
ALL_CURRICULA = [
    "CBSE",
    "ICSE",
    # State Boards
    "AP Board", "Assam Board", "Bihar Board", "Chhattisgarh Board",
    "Goa Board", "Gujarat Board", "Haryana Board", "HP Board",
    "JAC (Jharkhand)", "Karnataka Board", "Kerala Board",
    "MP Board", "Maharashtra Board", "Manipur Board", "Meghalaya Board",
    "Mizoram Board", "Nagaland Board", "Odisha Board", "Punjab Board",
    "Rajasthan Board", "Sikkim Board", "Tamil Nadu Board",
    "Telangana Board", "Tripura Board", "UP Board",
    "Uttarakhand Board", "West Bengal Board",
]


# ──────────────────────────────────────────────
#  Competitive Exams
# ──────────────────────────────────────────────

COMPETITIVE_EXAMS = [
    # Classes 8-9: Final / Annual Exams
    {
        "name": "Final Exam Practice",
        "description": "Practice tests for your annual school final exams with questions from all chapters.",
        "subjects_json": ["Mathematics", "Science", "Social Science", "English", "Hindi"],
        "class_min": 8,
        "class_max": 9,
    },
    # Class 10: Board Exams
    {
        "name": "CBSE Board Exam",
        "description": "CBSE Class 10 Board Examination practice — covers the full syllabus with board-style questions.",
        "subjects_json": ["Mathematics", "Science", "Social Science", "English", "Hindi"],
        "class_min": 10,
        "class_max": 10,
    },
    {
        "name": "State Board Exam",
        "description": "State Board Class 10 practice exam covering all core subjects.",
        "subjects_json": ["Mathematics", "Science", "Social Science", "English"],
        "class_min": 10,
        "class_max": 10,
    },
    # Classes 11-12: Competitive Exams
    {
        "name": "JEE Mains",
        "description": "Joint Entrance Examination (Mains) for admission to NITs, IIITs, and other centrally funded technical institutions.",
        "subjects_json": ["Physics", "Chemistry", "Mathematics"],
        "class_min": 11,
        "class_max": 12,
    },
    {
        "name": "JEE Advanced",
        "description": "Joint Entrance Examination (Advanced) for admission to the Indian Institutes of Technology (IITs).",
        "subjects_json": ["Physics", "Chemistry", "Mathematics"],
        "class_min": 11,
        "class_max": 12,
    },
    {
        "name": "NEET",
        "description": "National Eligibility cum Entrance Test for admission to medical and dental colleges across India.",
        "subjects_json": ["Physics", "Chemistry", "Biology"],
        "class_min": 11,
        "class_max": 12,
    },
]


# ──────────────────────────────────────────────
#  Seeding functions
# ──────────────────────────────────────────────

async def seed_subjects_and_chapters(db: AsyncSession) -> None:
    """Insert subjects + chapters if the subjects table is empty."""
    count = (await db.execute(select(func.count(Subject.id)))).scalar() or 0
    if count > 0:
        logger.info("Subjects table already seeded (%d rows). Skipping.", count)
        return

    logger.info("Seeding subjects and chapters for all curricula …")

    for curriculum in ALL_CURRICULA:
        is_icse = (curriculum == "ICSE")

        # Classes 8-10: common or ICSE-specific subjects
        for grade in range(8, 11):
            if is_icse:
                subjects = _ICSE_9_10 if grade >= 9 else _ICSE_8
                chapter_source = _ICSE_CHAPTERS
            else:
                subjects = _COMMON_8_10
                chapter_source = _CHAPTERS

            for subj_name, icon in subjects:
                subj = Subject(
                    name=subj_name,
                    curriculum=curriculum,
                    class_grade=grade,
                    stream=None,
                    icon_name=icon,
                )
                db.add(subj)
                await db.flush()

                chapters = chapter_source.get((subj_name, grade), [])
                # Fallback: ICSE English/Hindi/Math share NCERT chapters
                if not chapters:
                    chapters = _CHAPTERS.get((subj_name, grade), [])
                for idx, ch_title in enumerate(chapters, 1):
                    db.add(Chapter(
                        subject_id=subj.id,
                        title=ch_title,
                        order=idx,
                    ))

        # Classes 11-12: stream-specific
        stream_map = {
            "science": _SCIENCE_11_12,
            "commerce": _COMMERCE_11_12,
            "arts": _ARTS_11_12,
        }
        for grade in (11, 12):
            for stream_name, subjects in stream_map.items():
                for subj_name, icon in subjects:
                    subj = Subject(
                        name=subj_name,
                        curriculum=curriculum,
                        class_grade=grade,
                        stream=stream_name,
                        icon_name=icon,
                    )
                    db.add(subj)
                    await db.flush()

                    chapters = _CHAPTERS.get((subj_name, grade), [])
                    for idx, ch_title in enumerate(chapters, 1):
                        db.add(Chapter(
                            subject_id=subj.id,
                            title=ch_title,
                            order=idx,
                        ))

    await db.commit()
    final = (await db.execute(select(func.count(Subject.id)))).scalar()
    logger.info("✅ Seeded %d subjects.", final)


async def seed_competitive_exams(db: AsyncSession) -> None:
    """Insert competitive exam metadata if empty."""
    count = (await db.execute(select(func.count(CompetitiveExam.id)))).scalar() or 0
    if count > 0:
        logger.info("Competitive exams already seeded. Skipping.")
        return

    for ex in COMPETITIVE_EXAMS:
        db.add(CompetitiveExam(**ex))
    await db.commit()
    logger.info("✅ Seeded %d competitive exams.", len(COMPETITIVE_EXAMS))


async def seed_all(db: AsyncSession) -> None:
    """Master seeder — call from app lifespan."""
    await seed_subjects_and_chapters(db)
    await seed_competitive_exams(db)
