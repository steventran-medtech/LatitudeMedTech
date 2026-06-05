"""
Latitude MedTech — Learning Source Registry
=============================================
Dependency-free single source of truth for each agent's curated learning feeds.
Lives apart from agent_learning.py so lightweight tools (skills_profile.py,
dashboards) can import the registry without pulling in feedparser/requests.

Every agent gets:
  - Domain-specific sources (their primary expertise)
  - Consulting/business sources (Big 4 mindset) via "_shared"
  - AI/technology sources where relevant
Sources are RSS feeds where available; web pages otherwise.
"""

AGENT_SOURCES = {

    "content": [
        {"name": "HBR Ideas",           "url": "https://hbr.org/feed",                                       "domain": "Business Strategy",    "type": "rss"},
        {"name": "McKinsey Insights",   "url": "https://www.mckinsey.com/feeds/rss/insights",                 "domain": "Management Consulting", "type": "rss"},
        {"name": "MedTech Dive",        "url": "https://www.medtechdive.com/feeds/news/",                     "domain": "MedTech Industry",      "type": "rss"},
        {"name": "RAPS News",           "url": "https://www.raps.org/raps/media/news/rss.ashx",               "domain": "Regulatory Affairs",    "type": "rss"},
        {"name": "Substack Writing",    "url": "https://on.substack.com/feed",                                "domain": "Content Strategy",      "type": "rss"},
    ],

    "briefing": [
        {"name": "FDA Medical Devices", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml", "domain": "FDA Regulatory", "type": "rss"},
        {"name": "FDA CDRH Guidance",   "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/guidance/rss.xml",       "domain": "FDA Regulatory", "type": "rss"},
        {"name": "IMDRF",               "url": "https://www.imdrf.org/rss.xml",                                                             "domain": "Global Regulatory","type":"rss"},
        {"name": "Fierce Biotech",      "url": "https://www.fiercebiotech.com/rss/xml",                                                     "domain": "Biotech Industry", "type": "rss"},
        {"name": "Biocom California",   "url": "https://www.biocom.org/feed/",                                                              "domain": "SoCal MedTech",    "type": "rss"},
        {"name": "MedCity News",        "url": "https://medcitynews.com/feed/",                                                             "domain": "MedTech Industry", "type": "rss"},
    ],

    "iso": [
        {"name": "ASQ Quality Progress","url": "https://asq.org/quality-progress/rss",                        "domain": "Quality Systems",      "type": "rss"},
        {"name": "ISO News",            "url": "https://www.iso.org/cms/render/live/en/sites/isoorg/home/news/releases.html", "domain":"ISO Standards","type":"web"},
        {"name": "FDA Quality Systems", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",        "domain": "FDA QMS",          "type": "rss"},
        {"name": "Six Sigma Daily",     "url": "https://www.sixsigmadaily.com/feed/",                         "domain": "Six Sigma / Lean",     "type": "rss"},
        {"name": "Quality Digest",      "url": "https://www.qualitydigest.com/rss.xml",                       "domain": "Quality Management",   "type": "rss"},
        {"name": "HBR Operations",      "url": "https://hbr.org/topic/operations-management/feed",            "domain": "Operations Strategy",  "type": "rss"},
    ],

    "coaching": [
        {"name": "HBR Leadership",      "url": "https://hbr.org/topic/leadership/feed",                       "domain": "Leadership",           "type": "rss"},
        {"name": "HBR Career",          "url": "https://hbr.org/topic/career-planning/feed",                  "domain": "Career Development",   "type": "rss"},
        {"name": "McKinsey People",     "url": "https://www.mckinsey.com/feeds/rss/people",                   "domain": "Talent & Org",         "type": "rss"},
        {"name": "RAPS Career",         "url": "https://www.raps.org/raps/media/news/rss.ashx",               "domain": "RA Careers",           "type": "rss"},
        {"name": "Medical Device Academy","url":"https://medicaldeviceacademy.com/feed/",                      "domain": "MedTech QA/RA",        "type": "rss"},
    ],

    "fda": [
        {"name": "FDA Guidance Docs",   "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/guidance/rss.xml",       "domain": "FDA Regulatory",   "type": "rss"},
        {"name": "FDA Warning Letters", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/warning-letters/rss.xml", "domain": "FDA Enforcement",  "type": "rss"},
        {"name": "FDA Recalls",         "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",         "domain": "FDA Recalls",      "type": "rss"},
        {"name": "CDRH Updates",        "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml", "domain": "CDRH",             "type": "rss"},
        {"name": "Regulatory Focus",    "url": "https://www.raps.org/raps/media/news/rss.ashx",                                             "domain": "Regulatory Affairs","type":"rss"},
    ],

    "rag": [
        {"name": "LangChain Blog",      "url": "https://blog.langchain.dev/rss/",                             "domain": "AI / LangChain",       "type": "rss"},
        {"name": "Towards Data Science","url": "https://towardsdatascience.com/feed",                          "domain": "AI / ML",              "type": "rss"},
        {"name": "Hugging Face Blog",   "url": "https://huggingface.co/blog/feed.xml",                        "domain": "AI Models",            "type": "rss"},
        {"name": "McKinsey Tech",       "url": "https://www.mckinsey.com/feeds/rss/technology",               "domain": "AI Strategy",          "type": "rss"},
        {"name": "AI Alignment Forum",  "url": "https://www.alignmentforum.org/feed.xml",                     "domain": "AI Safety",            "type": "rss"},
    ],

    "consulting": [
        {"name": "McKinsey Quarterly",        "url": "https://www.mckinsey.com/feeds/rss/quarterly",            "domain": "Consulting Frameworks", "type": "rss"},
        {"name": "BCG Henderson Institute",   "url": "https://www.bcg.com/rss/publications",                   "domain": "Strategy Frameworks",   "type": "rss"},
        {"name": "Bain Insights",             "url": "https://www.bain.com/insights/rss/",                      "domain": "Case Studies",          "type": "rss"},
        {"name": "Strategy+Business",         "url": "https://www.strategy-business.com/rss",                  "domain": "Methodology",           "type": "rss"},
        {"name": "Stanford Social Innovation","url": "https://ssir.org/site/rss",                               "domain": "Case Studies",          "type": "rss"},
    ],
    "ma_intelligence": [
        {"name": "BioPharma Dive",            "url": "https://www.biopharmadive.com/feeds/news/",               "domain": "M&A Deals",             "type": "rss"},
        {"name": "Fierce Biotech",            "url": "https://www.fiercebiotech.com/rss/xml",                   "domain": "M&A Deals",             "type": "rss"},
        {"name": "Fierce MedTech",            "url": "https://www.fiercemedtech.com/rss/xml",                   "domain": "M&A Deals",             "type": "rss"},
        {"name": "Evaluate Vantage",          "url": "https://www.evaluate.com/vantage/rss",                    "domain": "Deal Analysis",         "type": "rss"},
        {"name": "STAT News",                 "url": "https://www.statnews.com/feed/",                          "domain": "Deal News",             "type": "rss"},
    ],

    # Shared — ALL agents ingest these (Big 4 consulting + 50-year scope)
    "_shared": [
        {"name": "McKinsey Quarterly",  "url": "https://www.mckinsey.com/feeds/rss/quarterly",                "domain": "Management Consulting", "type": "rss"},
        {"name": "HBR Strategy",        "url": "https://hbr.org/topic/strategy/feed",                         "domain": "Business Strategy",    "type": "rss"},
        {"name": "PwC Insights",        "url": "https://www.pwc.com/us/en/services/consulting/insights.rss",  "domain": "Management Consulting", "type": "rss"},
        {"name": "Deloitte Insights",   "url": "https://www2.deloitte.com/us/en/insights/deloitte-insights-magazine/deloitte-insights-magazine.rss", "domain":"Consulting","type":"rss"},
        {"name": "Six Sigma Black Belt","url": "https://www.isixsigma.com/feed/",                             "domain": "Six Sigma / Lean",     "type": "rss"},
        {"name": "MIT Sloan Mgmt",      "url": "https://sloanreview.mit.edu/feed/",                           "domain": "Management Research",  "type": "rss"},
        {"name": "PubMed Central",      "url": "https://www.ncbi.nlm.nih.gov/feed/rss.cgi?ChanKey=pubmedcentral", "domain": "Medical Literature 50yr", "type": "rss"},
        {"name": "NEJM",                "url": "https://www.nejm.org/action/showFeed?jc=nejm&type=etoc&feed=rss", "domain": "Medical Literature 50yr", "type": "rss"},
    ],
}
