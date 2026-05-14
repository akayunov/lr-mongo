import json
import subprocess


def test_basic(mongo_url):
    cmd = """
    db.testColl.insertMany([
        {
            "item": "journal",
            "instock": [
                {"warehouse": "A", "qty": 5},
                {"warehouse": "C", "qty": 15},
            ],
        },
        {"item": "notebook", "instock": [{"warehouse": "C", "qty": 5}]},
        {
            "item": "paper",
            "instock": [
                {"warehouse": "A", "qty": 60},
                {"warehouse": "B", "qty": 15},
            ],
        },
        {
            "item": "planner",
            "instock": [
                {"warehouse": "A", "qty": 40},
                {"warehouse": "B", "qty": 5},
            ],
        },
        {
            "item": "postcard",
            "instock": [
                {"warehouse": "B", "qty": 15},
                {"warehouse": "C", "qty": 35},
            ],
        },
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.find({"instock": {"warehouse": "B", "qty": 15}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 2

    cmd = """
        db.testColl.find({"instock.qty": {$lte:20}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 5
