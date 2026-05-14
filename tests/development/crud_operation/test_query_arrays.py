import json
import subprocess


def test_basic(mongo_url):
    cmd = """
    db.testColl.insertMany([
        {"item": "journal", "qty": 25, "tags": ["blank", "red"], "dim_cm": [14, 21]},
        {"item": "notebook", "qty": 50, "tags": ["red", "blank"], "dim_cm": [14, 21]},
        {
            "item": "paper",
            "qty": 100,
            "tags": ["red", "blank", "plain"],
            "dim_cm": [14, 21],
        },
        {"item": "planner", "qty": 75, "tags": ["blank", "red"], "dim_cm": [22.85, 30]},
        {"item": "postcard", "qty": 45, "tags": ["blue"], "dim_cm": [10, 15.25]},
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.find({"tags": ["red", "blank"]}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
        db.testColl.find({"tags": {"$all": ["red", "blank"]}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 4

    cmd = """
        db.testColl.find({"tags": "red"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 4

    cmd = """
            db.testColl.find({dim_cm:{"$gt": 25}}).toArray()
        """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
            db.testColl.find({dim_cm: {$gt: 22, "$lt": 30}}).toArray()
        """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
            db.testColl.find({dim_cm: {$elemMatch: {$gt: 22, $lt: 30}}}).toArray()
        """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
                db.testColl.find({"dim_cm.1": {$gt: 25}}).toArray()
            """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
                db.testColl.find({tags: {$size:3}}).toArray()
            """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1
