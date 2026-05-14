import json
import time


def test_basic(mongo_url, coa):
    cmd = """db.getSiblingDB('sample_mflix').movies.createSearchIndex(
        "default",
        { mappings: { dynamic: true } },
    )"""
    coa(cmd)

    cmd = """
        db.getSiblingDB('sample_mflix').movies.aggregate([
            {$search: {
                "text": {
                    query: "baseball",
                    path: "plot",
                }
            }}, 
            {$limit: 3},
            {$project:{
                _id: 0,
                title: 1,
                plot: 1
            }}
        ]).toArray()
    """
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "A trio of guys try and make up for missed opportunities in childhood by forming a three-player baseball team to compete against standard children baseball squads.",
            "title": "The Benchwarmers",
        },
        {"plot": "A trained chimpanzee plays third base for a minor-league baseball team.", "title": "Ed"},
        {
            "plot": "A young boy is bequeathed the ownership of a professional baseball team.",
            "title": "Little Big League",
        },
    ]

    query = [
        {
            "$search": {
                "compound": {
                    "must": [
                        {
                            "text": {
                                "query": "baseball",
                                "path": "plot",
                            }
                        }
                    ],
                    "mustNot": [{"text": {"query": ["Comedy", "Romance"], "path": "genres"}}],
                }
            }
        },
        {"$limit": 3},
        {"$project": {"_id": 0, "title": 1, "plot": 1}},
    ]
    cmd = f"""db.getSiblingDB('sample_mflix').movies.aggregate({query}).toArray()"""
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "Babe Ruth becomes a baseball legend but is unheroic to those who know " "him.",
            "title": "The Babe",
        },
        {
            "plot": "The story of the life and career of the famed baseball player, Lou " "Gehrig.",
            "title": "The Pride of the Yankees",
        },
        {
            "plot": 'Dominican baseball star Miguel "Sugar" Santos is recruited to play in ' "the U.S. minor-leagues.",
            "title": "Sugar",
        },
    ]


def test_index_autocomplete(coa):
    query = {"mappings": {"fields": {"plot": {"type": "autocomplete"}}}}
    json_query = json.dumps(query)
    cmd = f"""db.getSiblingDB('sample_mflix').movies.createSearchIndex(
        "partial-match-tutorial-autocomplete",
        {json_query}
    )"""
    coa(cmd)
    query = [
        {"$search": {"index": "partial-match-tutorial-autocomplete", "autocomplete": {"path": "plot", "query": "haw"}}},
        {"$limit": 2},
        {"$project": {"_id": 0, "title": 1, "plot": 1}},
    ]
    cmd = f"""
        db.getSiblingDB('sample_mflix').movies.aggregate({query}).toArray()
    """
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "Hawking is the extraordinary story of the planet's most famous living "
            "scientist, told for the first time in his own words and by those "
            "closest to him. Made with unique access to Hawking's ...",
            "title": "Hawking",
        },
        {
            "plot": "The treasure seeking adventures of young Jim Hawkins and pirate " "captain Long John Silver.",
            "title": "Treasure Island",
        },
    ]


def test_index_phrase_regex_wildcard(coa):
    query = {"mappings": {"fields": {"plot": {"type": "string"}}}}
    json_query = json.dumps(query)
    cmd = f"""db.getSiblingDB('sample_mflix').movies.createSearchIndex(
        "partial-match-tutorial",
        {json_query}
    )"""
    coa(cmd)
    time.sleep(1)
    query = [
        {"$search": {"index": "partial-match-tutorial", "phrase": {"path": "plot", "query": "jason york", "slop": 10}}},
        {"$limit": 2},
        {"$project": {"_id": 0, "title": 1, "plot": 1}},
    ]
    cmd = f"""
        db.getSiblingDB('sample_mflix').movies.aggregate({json.dumps(query)}).toArray()
    """
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "A passing boat bound for New York pulls Jason Voorhees along for the ride. Look out New York, here comes hell in a hockey mask.",
            "title": "Friday the 13th Part VIII: Jason Takes Manhattan",
        },
    ]

    query = [
        {
            "$search": {
                "index": "partial-match-tutorial",
                "regex": {"path": "plot", "query": ".*baseball.*", "allowAnalyzedField": True},
            }
        },
        {"$limit": 2},
        {"$project": {"_id": 0, "title": 1, "plot": 1}},
    ]
    cmd = f"""
         db.getSiblingDB('sample_mflix').movies.aggregate({json.dumps(query)}).toArray()
     """
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "The story of the life and career of the famed baseball player, Lou " "Gehrig.",
            "title": "The Pride of the Yankees",
        },
        {
            "plot": "An Iowa corn farmer, hearing voices, interprets them as a command to "
            "build a baseball diamond in his fields; he does, and the Chicago "
            "White Sox come.",
            "title": "Field of Dreams",
        },
    ]

    query = [
        {
            "$search": {
                "index": "partial-match-tutorial",
                "wildcard": {"path": "plot", "query": "how*", "allowAnalyzedField": True},
            }
        },
        {"$limit": 2},
        {"$project": {"_id": 0, "title": 1, "plot": 1}},
    ]
    cmd = f"""
         db.getSiblingDB('sample_mflix').movies.aggregate({json.dumps(query)}).toArray()
     """
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "Years after her aunt was murdered in her home, a young woman moves "
            "back into the house with her new husband. However, he has a secret "
            "that he will do anything to protect, even if it means driving his "
            "wife insane.",
            "title": "Gaslight",
        },
        {
            "plot": "A woman is asked to spy on a group of Nazi friends in South America. "
            "How far will she have to go to ingratiate herself with them?",
            "title": "Notorious",
        },
    ]
