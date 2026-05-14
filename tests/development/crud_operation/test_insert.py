import json
import subprocess
from unittest.mock import ANY


def test_basic(mongo_url):
    cmd = """
       db.testColl.insertOne(
            {
                "item": "canvas",
                "qty": 100,
                "tags": ["cotton"],
                "size": {"h": 28, "w": 35.5, "uom": "cm"},
            }
       ) 
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl.find({'item': 'canvas'}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": {
                "$oid": ANY,
            },
            "item": "canvas",
            "qty": 100,
            "size": {
                "h": 28,
                "uom": "cm",
                "w": 35.5,
            },
            "tags": [
                "cotton",
            ],
        },
    ]

    cmd = """
    db.testColl.insertMany([
                {
            "item": "journal",
            "qty": 25,
            "tags": ["blank", "red"],
            "size": {"h": 14, "w": 21, "uom": "cm"},
        },
        {
            "item": "mat",
            "qty": 85,
            "tags": ["gray"],
            "size": {"h": 27.9, "w": 35.5, "uom": "cm"},
        },
        {
            "item": "mousepad",
            "qty": 25,
            "tags": ["gel", "blue"],
            "size": {"h": 19, "w": 22.85, "uom": "cm"},
        },
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])
    cmd = """
        db.testColl.find().toArray()
    """

    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 4
