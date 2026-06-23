import datetime
import json


def test_facet_search(coa):
    index_mapping = {
        "mappings": {
            "dynamic": True,
            "fields": {
                "genres": {
                    "type": "token",
                }
            },
        }
    }

    cmd = f"""
        db.getSiblingDB('sample_mflix').movies.createSearchIndex(
            "facet-tutorial",
            {json.dumps(index_mapping)}
        )
    """
    coa(cmd)
    cmd = """
            db.getSiblingDB('sample_mflix').movies.aggregate([
                {
                    "$searchMeta": {
                        "index": "facet-tutorial",
                        "facet": {
                            "operator": {
                                "near": {
                                    "path": "released",
                                    "origin": ISODate("1921-11-01T00:00:00.000+00:00"),
                                    "pivot": 7776000000,
                                }
                            },
                            "facets": {
                                "genresFacet": {"type": "string", "path": "genres"},
                                "yearFacet": {"type": "number", "path": "year", "boundaries": [1910, 1920, 1930, 1940]},
                            },
                        },
                    },
                }
            ]).toArray()
        """
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "count": {"lowerBound": 20878},
            "facet": {
                "genresFacet": {
                    "buckets": [
                        {"_id": "Drama", "count": 12149},
                        {"_id": "Comedy", "count": 6436},
                        {"_id": "Romance", "count": 3274},
                        {"_id": "Crime", "count": 2429},
                        {"_id": "Thriller", "count": 2400},
                        {"_id": "Action", "count": 2349},
                        {"_id": "Adventure", "count": 1876},
                        {"_id": "Documentary", "count": 1755},
                        {"_id": "Horror", "count": 1432},
                        {"_id": "Biography", "count": 1244},
                    ],
                },
                "yearFacet": {
                    "buckets": [
                        {
                            "_id": 1910,
                            "count": 14,
                        },
                        {"_id": 1920, "count": 47},
                        {
                            "_id": 1930,
                            "count": 238,
                        },
                    ],
                },
            },
        },
    ]
