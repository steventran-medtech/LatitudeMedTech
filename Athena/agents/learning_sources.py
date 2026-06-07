"""
Latitude MedTech — Learning Source Registry
=============================================
Dependency-free single source of truth for each agent's curated learning feeds.
Lives apart from agent_learning.py so lightweight tools (skills_profile.py,
dashboards) can import the registry without pulling in feedparser/requests.

Every agent gets:
  - Domain-specific sources (their primary expertise)
  - Consulting/business sources (Big 4 mindset) via "_shared"
  - Historical sources (50-year scope) via "_historical" — retrospectives,
    institutional memory, and regulatory/management evolution since the 1970s
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
        # Historical — media evolution and journalism craft
        {"name": "Nieman Lab",          "url": "https://www.niemanlab.org/feed/",                             "domain": "Media Evolution 50yr",  "type": "rss"},
        {"name": "CJR",                 "url": "https://www.cjr.org/feed",                                   "domain": "Journalism History 50yr","type": "rss"},
    ],

    "briefing": [
        {"name": "FDA Medical Devices", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml", "domain": "FDA Regulatory",   "type": "rss"},
        {"name": "FDA CDRH Guidance",   "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/guidance/rss.xml",       "domain": "FDA Regulatory",   "type": "rss"},
        {"name": "IMDRF",               "url": "https://www.imdrf.org/rss.xml",                                                             "domain": "Global Regulatory", "type": "rss"},
        {"name": "Fierce Biotech",      "url": "https://www.fiercebiotech.com/rss/xml",                                                     "domain": "Biotech Industry",  "type": "rss"},
        {"name": "Biocom California",   "url": "https://www.biocom.org/feed/",                                                              "domain": "SoCal MedTech",     "type": "rss"},
        {"name": "MedCity News",        "url": "https://medcitynews.com/feed/",                                                             "domain": "MedTech Industry",  "type": "rss"},
        # Historical — regulatory rulemaking archive and policy history
        {"name": "Federal Register FDA","url": "https://www.federalregister.gov/documents/search.rss?conditions%5Bagency_ids%5D%5B%5D=157", "domain": "Regulatory History 50yr", "type": "rss"},
        {"name": "Health Affairs",      "url": "https://www.healthaffairs.org/action/showFeed?type=etoc&feed=rss",                          "domain": "Health Policy History",   "type": "rss"},
    ],

    "iso": [
        {"name": "ASQ Quality Progress","url": "https://asq.org/quality-progress/rss",                        "domain": "Quality Systems",      "type": "rss"},
        {"name": "ISO News",            "url": "https://www.iso.org/cms/render/live/en/sites/isoorg/home/news/releases.html", "domain":"ISO Standards","type":"web"},
        {"name": "FDA Quality Systems", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",        "domain": "FDA QMS",          "type": "rss"},
        {"name": "Six Sigma Daily",     "url": "https://www.sixsigmadaily.com/feed/",                         "domain": "Six Sigma / Lean",     "type": "rss"},
        {"name": "Quality Digest",      "url": "https://www.qualitydigest.com/rss.xml",                       "domain": "Quality Management",   "type": "rss"},
        {"name": "HBR Operations",      "url": "https://hbr.org/topic/operations-management/feed",            "domain": "Operations Strategy",  "type": "rss"},
        # Historical — QMS origins: Deming/Juran era to present
        {"name": "Deming Institute",    "url": "https://deming.org/feed/",                                    "domain": "Quality History 50yr", "type": "rss"},
        {"name": "IEEE Reliability",    "url": "https://rs.ieee.org/component/easyblog/archive.feed?type=rss","domain": "Reliability History 50yr","type":"rss"},
    ],

    "coaching": [
        {"name": "HBR Leadership",      "url": "https://hbr.org/topic/leadership/feed",                       "domain": "Leadership",           "type": "rss"},
        {"name": "HBR Career",          "url": "https://hbr.org/topic/career-planning/feed",                  "domain": "Career Development",   "type": "rss"},
        {"name": "McKinsey People",     "url": "https://www.mckinsey.com/feeds/rss/people",                   "domain": "Talent & Org",         "type": "rss"},
        {"name": "RAPS Career",         "url": "https://www.raps.org/raps/media/news/rss.ashx",               "domain": "RA Careers",           "type": "rss"},
        {"name": "Medical Device Academy","url":"https://medicaldeviceacademy.com/feed/",                      "domain": "MedTech QA/RA",        "type": "rss"},
        # Historical — career landscape evolution in MedTech RA/QA
        {"name": "Drucker Institute",   "url": "https://www.drucker.institute/feed/",                         "domain": "Management History 50yr","type":"rss"},
        {"name": "SHRM HR Topics",      "url": "https://www.shrm.org/rss/pages/rss.aspx",                     "domain": "Workforce History 50yr","type":"rss"},
    ],

    "fda": [
        # Unique to FDA agent — not shared with briefing
        {"name": "FDA Warning Letters",  "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/warning-letters/rss.xml",    "domain": "FDA Enforcement",   "type": "rss"},
        {"name": "FDA Recalls",          "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml",             "domain": "FDA Recalls",       "type": "rss"},
        {"name": "FDA MedWatch Alerts",  "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch-safety-alerts/rss.xml","domain": "FDA Safety",      "type": "rss"},
        {"name": "FDA Press Releases",   "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-announcements/rss.xml", "domain": "FDA Announcements", "type": "rss"},
        {"name": "MDDI Online",          "url": "https://www.mddionline.com/rss.xml",                                                            "domain": "MedTech Regulatory","type": "rss"},
        {"name": "Health Affairs",       "url": "https://www.healthaffairs.org/action/showFeed?type=etoc&feed=rss",                              "domain": "Health Policy",     "type": "rss"},
        # Historical — FDA rulemaking archive (1976 MDA forward) + NEJM device safety research
        {"name": "Federal Register FDA", "url": "https://www.federalregister.gov/documents/search.rss?conditions%5Bagency_ids%5D%5B%5D=157",    "domain": "Regulatory History 50yr","type":"rss"},
        {"name": "NEJM Original Res.",   "url": "https://www.nejm.org/action/showFeed?jc=nejm&type=etoc&feed=rss",                              "domain": "Medical Literature 50yr","type":"rss"},
    ],

    "rag": [
        {"name": "LangChain Blog",      "url": "https://blog.langchain.dev/rss/",                             "domain": "AI / LangChain",       "type": "rss"},
        {"name": "Towards Data Science","url": "https://towardsdatascience.com/feed",                          "domain": "AI / ML",              "type": "rss"},
        {"name": "Hugging Face Blog",   "url": "https://huggingface.co/blog/feed.xml",                        "domain": "AI Models",            "type": "rss"},
        {"name": "McKinsey Tech",       "url": "https://www.mckinsey.com/feeds/rss/technology",               "domain": "AI Strategy",          "type": "rss"},
        {"name": "AI Alignment Forum",  "url": "https://www.alignmentforum.org/feed.xml",                     "domain": "AI Safety",            "type": "rss"},
        # Historical — AI/ML research evolution (arXiv preprints + Semantic Scholar)
        {"name": "arXiv cs.AI",         "url": "https://export.arxiv.org/rss/cs.AI",                          "domain": "AI Research History",  "type": "rss"},
        {"name": "arXiv cs.IR",         "url": "https://export.arxiv.org/rss/cs.IR",                          "domain": "IR/RAG History",       "type": "rss"},
        # QARA regulatory sources — 50-year knowledge base
        {"name": "RAPS Regulatory Focus", "url": "https://www.raps.org/news-and-articles/rss",                 "domain": "Regulatory Affairs",   "type": "rss"},
        {"name": "Federal Register MedDev","url": "https://www.federalregister.gov/documents/search.rss?conditions%5Bagencies%5D%5B%5D=food-and-drug-administration&conditions%5Btopic%5D%5B%5D=medical-devices", "domain": "FDA Federal Register", "type": "rss"},
        {"name": "IMDRF Documents",       "url": "https://www.imdrf.org/rss.xml",                              "domain": "Global Harmonization", "type": "rss"},
        {"name": "FDA Medical Devices",   "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml", "domain": "FDA CDRH",          "type": "rss"},
    ],

    "consulting": [
        {"name": "McKinsey Quarterly",        "url": "https://www.mckinsey.com/feeds/rss/quarterly",            "domain": "Consulting Frameworks", "type": "rss"},
        {"name": "BCG Henderson Institute",   "url": "https://www.bcg.com/rss/publications",                   "domain": "Strategy Frameworks",   "type": "rss"},
        {"name": "Bain Insights",             "url": "https://www.bain.com/insights/rss/",                      "domain": "Case Studies",          "type": "rss"},
        {"name": "Strategy+Business",         "url": "https://www.strategy-business.com/rss",                  "domain": "Methodology",           "type": "rss"},
        {"name": "Stanford Social Innovation","url": "https://ssir.org/site/rss",                               "domain": "Case Studies",          "type": "rss"},
        # Historical — management framework origins: Drucker, BCG/McKinsey classics
        {"name": "Drucker Institute",         "url": "https://www.drucker.institute/feed/",                     "domain": "Management History 50yr","type":"rss"},
        {"name": "Ivey Business Journal",     "url": "https://iveybusinessjournal.com/feed/",                   "domain": "Consulting History 50yr","type":"rss"},
    ],
    "voice_bridge": [
        {"name": "MIT Technology Review","url": "https://www.technologyreview.com/feed/",                       "domain": "AI Technology",        "type": "rss"},
        {"name": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/feed/",                   "domain": "AI Industry",          "type": "rss"},
        {"name": "Google AI Blog",       "url": "https://blog.google/technology/ai/rss/",                      "domain": "Conversational AI",    "type": "rss"},
        {"name": "The Gradient",         "url": "https://thegradient.pub/rss/",                                "domain": "ML Research",          "type": "rss"},
        {"name": "AI Business",          "url": "https://aibusiness.com/rss.xml",                              "domain": "AI Applications",      "type": "rss"},
        # Historical — voice/speech AI evolution (DARPA SUR 1970s → Whisper 2022)
        {"name": "IEEE Spectrum",        "url": "https://spectrum.ieee.org/feeds/feed.rss",                    "domain": "Technology History 50yr","type":"rss"},
        {"name": "arXiv cs.CL",          "url": "https://export.arxiv.org/rss/cs.CL",                          "domain": "NLP/Speech History",   "type": "rss"},
    ],

    "ma_intelligence": [
        {"name": "BioPharma Dive",            "url": "https://www.biopharmadive.com/feeds/news/",               "domain": "M&A Deals",             "type": "rss"},
        {"name": "Fierce Biotech",            "url": "https://www.fiercebiotech.com/rss/xml",                   "domain": "M&A Deals",             "type": "rss"},
        {"name": "Fierce MedTech",            "url": "https://www.fiercemedtech.com/rss/xml",                   "domain": "M&A Deals",             "type": "rss"},
        {"name": "Evaluate Vantage",          "url": "https://www.evaluate.com/vantage/rss",                    "domain": "Deal Analysis",         "type": "rss"},
        {"name": "STAT News",                 "url": "https://www.statnews.com/feed/",                          "domain": "Deal News",             "type": "rss"},
        # Historical — 50-year M&A pattern library (serial acquirers, PE rollups, integration failures)
        {"name": "Institutional Investor",    "url": "https://www.institutionalinvestor.com/rss",               "domain": "M&A History 50yr",      "type": "rss"},
        {"name": "PE Hub / Buyouts",          "url": "https://www.pehub.com/feed/",                             "domain": "PE/Rollup History 50yr","type":"rss"},
    ],

    "eu_mdr": [
        {"name": "EU MDR News",          "url": "https://www.medtechdive.com/feeds/news/",                      "domain": "EU MDR Regulatory",    "type": "rss"},
        {"name": "RAPS EU/Global",       "url": "https://www.raps.org/raps/media/news/rss.ashx",               "domain": "Global Regulatory",    "type": "rss"},
        {"name": "Fierce MedTech EU",    "url": "https://www.fiercemedtech.com/rss/xml",                       "domain": "MedTech EU",           "type": "rss"},
        {"name": "MDDI EU Regulation",   "url": "https://www.mddionline.com/rss.xml",                          "domain": "EU Device Regulation", "type": "rss"},
        # Historical — EU directive evolution: MDD 1993 → MDR 2017 → mandatory 2021
        {"name": "Federal Register FDA", "url": "https://www.federalregister.gov/documents/search.rss?conditions%5Bagency_ids%5D%5B%5D=157", "domain": "Regulatory History 50yr", "type": "rss"},
        {"name": "Health Affairs",       "url": "https://www.healthaffairs.org/action/showFeed?type=etoc&feed=rss", "domain": "Health Policy History", "type": "rss"},
    ],

    "hr": [
        {"name": "SHRM HR Topics",       "url": "https://www.shrm.org/rss/pages/rss.aspx",                     "domain": "Human Resources",      "type": "rss"},
        {"name": "HBR Managing People",  "url": "https://hbr.org/topic/managing-people/feed",                  "domain": "People Management",    "type": "rss"},
        {"name": "McKinsey People",      "url": "https://www.mckinsey.com/feeds/rss/people",                   "domain": "Talent Strategy",      "type": "rss"},
        # Historical — HR profession evolution from personnel to strategic HRBP
        {"name": "Drucker Institute",    "url": "https://www.drucker.institute/feed/",                         "domain": "Management History 50yr","type":"rss"},
        {"name": "MIT Sloan Mgmt",       "url": "https://sloanreview.mit.edu/feed/",                           "domain": "Org Behavior History", "type": "rss"},
    ],

    "marketing": [
        {"name": "HBR Marketing",        "url": "https://hbr.org/topic/marketing/feed",                        "domain": "Marketing Strategy",   "type": "rss"},
        {"name": "Content Marketing Inst","url": "https://contentmarketinginstitute.com/feed/",                 "domain": "Content Marketing",    "type": "rss"},
        {"name": "Substack Writing",     "url": "https://on.substack.com/feed",                                "domain": "Newsletter Marketing", "type": "rss"},
        {"name": "MedTech Dive",         "url": "https://www.medtechdive.com/feeds/news/",                     "domain": "MedTech Industry",     "type": "rss"},
        # Historical — B2B MedTech marketing evolution: trade shows → digital → thought leadership
        {"name": "Nieman Lab",           "url": "https://www.niemanlab.org/feed/",                             "domain": "Media Evolution 50yr", "type": "rss"},
        {"name": "Drucker Institute",    "url": "https://www.drucker.institute/feed/",                         "domain": "Marketing History 50yr","type":"rss"},
    ],

    "deck": [
        {"name": "McKinsey Quarterly",   "url": "https://www.mckinsey.com/feeds/rss/quarterly",                "domain": "Consulting Frameworks", "type": "rss"},
        {"name": "BCG Henderson Inst.",  "url": "https://www.bcg.com/rss/publications",                        "domain": "Strategy Frameworks",   "type": "rss"},
        {"name": "HBR Strategy",         "url": "https://hbr.org/topic/strategy/feed",                        "domain": "Business Strategy",    "type": "rss"},
        {"name": "Bain Insights",        "url": "https://www.bain.com/insights/rss/",                         "domain": "Case Studies",         "type": "rss"},
        # Historical — consulting deck and visualization evolution: Minto Pyramid to modern data viz
        {"name": "Drucker Institute",    "url": "https://www.drucker.institute/feed/",                         "domain": "Consulting History 50yr","type":"rss"},
        {"name": "Ivey Business Journal","url": "https://iveybusinessjournal.com/feed/",                       "domain": "Framework History 50yr","type":"rss"},
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

    # Historical — ALL agents ingest these to build 50-year domain evolution context.
    # These sources publish retrospectives, milestone analyses, and institutional memory
    # that ground every agent's reasoning in how their field has improved since the 1970s.
    "_historical": [
        {"name": "Deming Institute",     "url": "https://deming.org/feed/",                                                                                    "domain": "Quality History 50yr",      "type": "rss"},
        {"name": "Drucker Institute",    "url": "https://www.drucker.institute/feed/",                                                                         "domain": "Management History 50yr",   "type": "rss"},
        {"name": "Federal Register FDA", "url": "https://www.federalregister.gov/documents/search.rss?conditions%5Bagency_ids%5D%5B%5D=157",                   "domain": "Regulatory History 50yr",   "type": "rss"},
        {"name": "IEEE Spectrum",        "url": "https://spectrum.ieee.org/feeds/feed.rss",                                                                    "domain": "Technology History 50yr",   "type": "rss"},
        {"name": "Nieman Lab",           "url": "https://www.niemanlab.org/feed/",                                                                             "domain": "Media Evolution 50yr",      "type": "rss"},
        {"name": "Health Affairs",       "url": "https://www.healthaffairs.org/action/showFeed?type=etoc&feed=rss",                                            "domain": "Health Policy History 50yr","type": "rss"},
    ],
}
