"""
Industry knowledge base for AI agent consultancy.
Used by the lead generator to tailor emails, demos, and opportunity assessments.
"""

INDUSTRIES = {
    "local_councils": {
        "name": "Local Councils & Public Services",
        "regions": ["UK", "UAE", "Saudi Arabia", "Oman"],
        "pain_points": [
            "High volume of resident inquiries across phone, email, and web",
            "Slow response times for permits, complaints, and service requests",
            "Staff overloaded with routine FAQ-style questions",
            "Language barriers in multicultural areas (especially GCC)",
            "Paper-based workflows and data silos between departments",
            "Difficulty measuring citizen satisfaction at scale",
        ],
        "use_cases": [
            {
                "title": "Resident Support Agent",
                "description": "24/7 multilingual chatbot handling FAQs about bin collection, council tax, planning, housing, parking fines, and benefits.",
                "impact": "60-80% deflection of L1 tickets; ~£15 saved per contact.",
            },
            {
                "title": "Permit & License Processor",
                "description": "Automates intake and pre-validation of planning, trading, and event permit applications with document checking.",
                "impact": "Processing time cut from weeks to days.",
            },
            {
                "title": "Complaints Triage Agent",
                "description": "Classifies incoming complaints, routes to the right department, and drafts initial acknowledgements.",
                "impact": "Fewer missed SLAs, caseworkers freed for complex cases.",
            },
            {
                "title": "Council Meeting Summarizer",
                "description": "Generates accessible summaries of full council and planning committee meetings.",
                "impact": "Improved transparency and citizen engagement.",
            },
        ],
        "decision_makers": [
            "Head of Digital",
            "CIO / IT Director",
            "Director of Customer Services",
            "Transformation Lead",
        ],
        "talking_points": [
            "Aligned with UK Government Digital Service design standards",
            "GDPR / data residency compliant deployment (on-prem or UK/EU cloud)",
            "Cost per interaction savings modelled and measurable",
            "Human-in-the-loop for sensitive cases",
        ],
    },

    "youth_programs": {
        "name": "Youth Programs & Community Services",
        "regions": ["UK", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Limited budgets and small teams for program delivery",
            "Manual case management for young people",
            "Engagement barriers with digitally-native youth",
            "Parents and guardians seek info outside office hours",
            "Reporting and funding applications drain staff time",
        ],
        "use_cases": [
            {
                "title": "Youth Support Chat",
                "description": "Safe, moderated chat agent that answers questions, signposts services, and flags safeguarding concerns to human staff.",
                "impact": "24/7 first-line support; higher engagement with hard-to-reach youth.",
            },
            {
                "title": "Program Coordinator Assistant",
                "description": "Scheduling, reminders, attendance tracking, and parental communications handled end-to-end.",
                "impact": "~10 hours per week saved per coordinator.",
            },
            {
                "title": "Funding Application Agent",
                "description": "Drafts grant and funding applications from program data, aligned to funder criteria.",
                "impact": "More applications submitted, higher success rate.",
            },
            {
                "title": "Impact Report Generator",
                "description": "Turns raw program data into funder-ready reports with narrative and metrics.",
                "impact": "Reduces reporting cycle from days to hours.",
            },
        ],
        "decision_makers": ["Program Manager", "CEO (charity/NGO)", "Operations Lead"],
        "talking_points": [
            "Safeguarding-first design with clear escalation",
            "Human-in-loop on all sensitive interactions",
            "Grant-friendly pricing and pilot models",
            "Outcome reporting built in",
        ],
    },

    "healthcare": {
        "name": "Healthcare (Clinics, Practices, Private Providers)",
        "regions": ["UK", "UAE", "Saudi Arabia", "Oman"],
        "pain_points": [
            "No-shows and last-minute cancellations eroding revenue",
            "Receptionist overload during peak times",
            "Manual appointment booking and rescheduling",
            "Gaps in patient follow-up and continuity of care",
            "Insurance and billing administrative burden",
            "Multilingual patient populations (English/Arabic/Urdu in GCC)",
        ],
        "use_cases": [
            {
                "title": "Appointment & Triage Agent",
                "description": "Books, reschedules, and reminds patients; triages symptoms to the right specialist; fully multilingual.",
                "impact": "~30% fewer no-shows; 50% less reception admin.",
            },
            {
                "title": "Patient Intake Agent",
                "description": "Pre-visit forms, medical history collection, and consent handling before the patient walks in.",
                "impact": "Shorter waiting room times; higher data quality in EMR.",
            },
            {
                "title": "Post-Visit Care Agent",
                "description": "Medication reminders, follow-up check-ins, and outcome surveys at scale.",
                "impact": "Better medication adherence and patient outcomes.",
            },
            {
                "title": "Insurance Pre-Authorisation Assistant",
                "description": "Drafts and submits insurance pre-authorization requests with supporting clinical notes.",
                "impact": "Shorter billing cycle; fewer denials.",
            },
        ],
        "decision_makers": [
            "Practice Manager",
            "Clinical Director",
            "Medical Director",
            "CIO / IT lead",
        ],
        "talking_points": [
            "HIPAA / GDPR / NHS DSPT compliant deployment",
            "Native Arabic language support",
            "Integration with major EMRs (Epic, Cerner, EMIS, SystmOne, InterSystems)",
            "Measurable reduction in admin hours and no-show rates",
        ],
    },

    "ai_training": {
        "name": "AI Training Providers & Bootcamps",
        "regions": ["UK", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Student support doesn't scale with cohort size",
            "Lead response times lose prospective students to competitors",
            "Manual curriculum updates as AI evolves weekly",
            "Corporate clients want custom modules on tight timelines",
        ],
        "use_cases": [
            {
                "title": "Student Learning Assistant",
                "description": "24/7 tutor agent that answers course questions, grades exercises, and gives feedback personalized to each student.",
                "impact": "Lower instructor load; higher course completion rates.",
            },
            {
                "title": "Enrollment Agent",
                "description": "Qualifies inbound leads, books discovery calls, answers course questions, handles payment links.",
                "impact": "Reduces lead-to-enrollment time from days to minutes.",
            },
            {
                "title": "Curriculum Research Agent",
                "description": "Monitors AI research, tools, and frameworks; suggests curriculum updates with drafted content.",
                "impact": "Always-current courses without pulling instructor time.",
            },
        ],
        "decision_makers": ["Founder / CEO", "Head of Product", "Head of Delivery"],
        "talking_points": [
            "Show don't tell: we build AI agents, of course our own school should run on them",
            "Scalable student support without more staff",
            "Positions you as genuinely AI-native",
        ],
    },

    "online_education": {
        "name": "Online Education & EdTech",
        "regions": ["UK", "USA", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Low completion rates on self-paced courses",
            "Support tickets scale linearly with student count",
            "Hard to personalize learning at scale",
            "Content creation bottlenecks",
        ],
        "use_cases": [
            {
                "title": "Personalized Tutor Agent",
                "description": "1-on-1 AI tutor per student that adapts explanations, gives hints, generates practice problems.",
                "impact": "2-3x completion rates; significantly higher NPS.",
            },
            {
                "title": "Student Success Agent",
                "description": "Detects at-risk students from behavior signals, intervenes with nudges and resources.",
                "impact": "Higher retention; better outcomes.",
            },
            {
                "title": "Content Generation Agent",
                "description": "Generates quizzes, lesson variants, summaries, and translations from existing course material.",
                "impact": "Faster course production; multi-market launches.",
            },
        ],
        "decision_makers": ["Head of Product", "Head of Learning", "CTO", "CEO"],
        "talking_points": [
            "Retention and completion metrics drive unit economics",
            "White-labeled agent fits existing LMS",
            "Instructors shift from support to high-value teaching",
        ],
    },

    "schools": {
        "name": "Schools (Primary & Secondary)",
        "regions": ["UK", "UAE", "Saudi Arabia", "Oman"],
        "pain_points": [
            "Teacher workload: lesson planning, marking, reports",
            "Parent communications consuming teacher evenings",
            "SEN and pastoral case tracking manual",
            "Admissions and inquiries handled ad-hoc",
        ],
        "use_cases": [
            {
                "title": "Teacher Assistant Agent",
                "description": "Drafts lesson plans, marks work with rubrics, writes report comments, generates differentiated resources.",
                "impact": "5-10 hours per teacher per week returned.",
            },
            {
                "title": "Parent Communications Agent",
                "description": "Handles routine parent questions (uniform, trips, absences, homework) with school-approved answers.",
                "impact": "Office admin hours cut by half.",
            },
            {
                "title": "Admissions Agent",
                "description": "Answers prospective parent questions, books open-day visits, collects application details.",
                "impact": "Higher conversion from inquiry to enrollment.",
            },
        ],
        "decision_makers": ["Head Teacher", "Business Manager", "MAT CEO", "Director of Digital"],
        "talking_points": [
            "DfE-aligned safeguarding posture",
            "Teacher-approved tone and content library",
            "Deployable at MAT level with per-school customization",
        ],
    },

    "universities": {
        "name": "Universities & Higher Education",
        "regions": ["UK", "UAE", "Saudi Arabia", "USA"],
        "pain_points": [
            "Student services overwhelmed at key cycles (clearing, exam time)",
            "International student inquiries outside office hours and timezones",
            "Research admin burden: grants, ethics, publications",
            "Alumni engagement drops off post-graduation",
        ],
        "use_cases": [
            {
                "title": "Student Services Agent",
                "description": "24/7 agent for course, campus, accommodation, finance, and visa questions; multilingual.",
                "impact": "Deflects 70% of tier-1 queries; better student satisfaction.",
            },
            {
                "title": "Applications & Clearing Agent",
                "description": "Handles inquiries during peak recruitment cycles, answers course-specific questions, pre-screens applicants.",
                "impact": "More applications processed without hiring seasonal staff.",
            },
            {
                "title": "Research Admin Agent",
                "description": "Drafts grant applications, helps with ethics submissions, summarizes literature.",
                "impact": "Hours back to researchers.",
            },
        ],
        "decision_makers": [
            "Director of Student Services",
            "Director of Admissions",
            "CIO",
            "Dean",
        ],
        "talking_points": [
            "Multilingual for international student bodies",
            "Integration with existing systems (Salesforce Edu, SITS, Banner)",
            "Pilot-friendly with measurable KPIs",
        ],
    },

    "government": {
        "name": "Central Government & Public Sector",
        "regions": ["UK", "UAE", "Saudi Arabia", "Oman"],
        "pain_points": [
            "Citizen services at national scale",
            "Policy documents long and inaccessible to public",
            "Inter-department data and workflow silos",
            "Procurement cycles slow",
        ],
        "use_cases": [
            {
                "title": "Citizen Services Agent",
                "description": "National-scale assistant for benefits, taxes, licenses, and public programs; multilingual.",
                "impact": "Millions of interactions deflected; better accessibility.",
            },
            {
                "title": "Policy Explainer Agent",
                "description": "Turns dense policy documents into plain-language answers for citizens and journalists.",
                "impact": "Higher public understanding and trust.",
            },
            {
                "title": "Internal Workflow Agent",
                "description": "Automates FOI responses, briefing preparation, and document drafting inside departments.",
                "impact": "Hours returned to civil servants.",
            },
        ],
        "decision_makers": [
            "Director of Digital Services",
            "Permanent Secretary",
            "CTO of Ministry",
            "Head of Innovation",
        ],
        "talking_points": [
            "Sovereign deployment (on-prem or national cloud)",
            "Full audit trail and explainability",
            "Aligned with UAE AI Strategy 2031 / Saudi Vision 2030",
        ],
    },

    "clothing_manufacturing": {
        "name": "Clothing & Textile Manufacturing",
        "regions": ["UK", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Sample-to-order cycles too long",
            "Manual sourcing and supplier communication",
            "Production planning across factories",
            "Quality control inspection and reporting",
            "Customer service for B2B orders",
        ],
        "use_cases": [
            {
                "title": "Sourcing & Supplier Agent",
                "description": "Finds fabric/trim suppliers, requests quotes, compares options, tracks samples.",
                "impact": "Sourcing time cut by 60-70%.",
            },
            {
                "title": "Order Processing Agent",
                "description": "Handles B2B order intake, status queries, and change requests across channels.",
                "impact": "Frees sales team for growth work.",
            },
            {
                "title": "QC & Compliance Agent",
                "description": "Reads inspection reports and supplier certifications; flags non-compliance automatically.",
                "impact": "Fewer defects escaping to shipment.",
            },
            {
                "title": "Design-to-Tech-Pack Agent",
                "description": "Drafts tech packs and BOMs from sketches and briefs.",
                "impact": "Shortens sample cycles dramatically.",
            },
        ],
        "decision_makers": ["COO", "Head of Production", "Head of Sourcing", "Founder"],
        "talking_points": [
            "Integration with ERP and PLM (Centric, Bluecherry, etc.)",
            "Arabic/English/Chinese communication with suppliers",
            "Measurable OTIF and margin impact",
        ],
    },

    "retail_ecommerce": {
        "name": "Retail & E-commerce",
        "regions": ["UK", "USA", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Customer service volume (returns, tracking, sizing)",
            "Cart abandonment",
            "Product discovery friction",
            "Manual marketing content creation",
        ],
        "use_cases": [
            {
                "title": "Customer Service Agent",
                "description": "Handles returns, tracking, sizing, product Q&A across web, WhatsApp, and email.",
                "impact": "70-90% ticket deflection.",
            },
            {
                "title": "Shopping Assistant Agent",
                "description": "Conversational product discovery and outfit recommendations.",
                "impact": "Higher conversion and AOV.",
            },
            {
                "title": "Merchandising Agent",
                "description": "Generates product copy, alt text, translations, and A/B variants at scale.",
                "impact": "Faster catalogue rollout, more tests running.",
            },
        ],
        "decision_makers": ["Head of E-commerce", "CX Director", "CMO"],
        "talking_points": [
            "WhatsApp Business native (critical in GCC)",
            "Arabic-first for GCC markets",
            "Integration with Shopify, Magento, Salesforce Commerce",
        ],
    },

    "legal": {
        "name": "Legal Services & Law Firms",
        "regions": ["UK", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Intake and qualification of new matters",
            "Document review is billable but low-margin",
            "Client communications consume partner time",
            "Research across case law",
        ],
        "use_cases": [
            {
                "title": "Client Intake Agent",
                "description": "Qualifies new matters, collects facts, runs conflict checks, books consultations.",
                "impact": "Partners only see qualified, prepared matters.",
            },
            {
                "title": "Document Review Agent",
                "description": "First-pass review of contracts, disclosure bundles, and due diligence packs.",
                "impact": "Paralegal hours cut; faster deals.",
            },
            {
                "title": "Legal Research Agent",
                "description": "Surfaces relevant case law, statutes, and precedents with citations.",
                "impact": "Hours to minutes on initial research.",
            },
        ],
        "decision_makers": ["Managing Partner", "Head of Innovation", "CIO", "COO"],
        "talking_points": [
            "Confidentiality and matter-level data isolation",
            "Integration with Clio, iManage, NetDocuments",
            "Ethics and professional-conduct aligned",
        ],
    },

    "real_estate": {
        "name": "Real Estate (Residential & Commercial)",
        "regions": ["UK", "UAE", "Saudi Arabia"],
        "pain_points": [
            "Lead response time is the #1 predictor of conversion",
            "Property viewings and paperwork burn agent hours",
            "Listings need constant rewriting",
            "Multi-lingual buyers in GCC",
        ],
        "use_cases": [
            {
                "title": "Lead Response Agent",
                "description": "Engages every inbound lead in under 1 minute, qualifies, books viewings.",
                "impact": "3-5x conversion vs typical response times.",
            },
            {
                "title": "Listings Agent",
                "description": "Generates property descriptions from photos and specs in multiple languages.",
                "impact": "Listing throughput up; more time for selling.",
            },
            {
                "title": "Tenant Services Agent",
                "description": "Handles maintenance requests, rent queries, and renewal conversations.",
                "impact": "Landlord operations scale without staff growth.",
            },
        ],
        "decision_makers": ["Agency Principal", "Sales Director", "Property Manager"],
        "talking_points": [
            "WhatsApp + web + phone channels",
            "Integration with Rex, Alto, JustImagine",
            "Arabic / Russian / English for Dubai market",
        ],
    },

    "hospitality": {
        "name": "Hospitality (Hotels, Restaurants, Tourism)",
        "regions": ["UK", "UAE", "Saudi Arabia", "Oman"],
        "pain_points": [
            "Guest requests at all hours across languages",
            "Booking management across channels",
            "Review and reputation management",
            "Table/room upsells left on the table",
        ],
        "use_cases": [
            {
                "title": "Guest Services Agent",
                "description": "Handles bookings, check-in info, restaurant recommendations, concierge requests 24/7 in any language.",
                "impact": "Higher guest satisfaction, lower front-desk load.",
            },
            {
                "title": "Review Response Agent",
                "description": "Drafts personalized review responses across TripAdvisor, Google, Booking.",
                "impact": "Consistent brand voice at scale.",
            },
            {
                "title": "Revenue & Upsell Agent",
                "description": "Proactively offers upgrades, F&B add-ons, and experiences to confirmed bookings.",
                "impact": "Measurable RevPAR lift.",
            },
        ],
        "decision_makers": ["GM", "Director of Revenue", "Head of Guest Experience"],
        "talking_points": [
            "Integrates with PMS (Opera, Mews, Cloudbeds)",
            "Arabic / English / Russian / Mandarin",
            "Built for GCC luxury service standards",
        ],
    },
}


def list_industries():
    return [(key, data["name"]) for key, data in INDUSTRIES.items()]


def get_industry(key):
    return INDUSTRIES.get(key)
