import json
import subprocess


def test_basic(mongo_url):
    cmd = """
    db.testColl.insertMany([
        {
            "item": "journal",
            "qty": 25,
            "size": {"h": 14, "w": 21, "uom": "cm"},
            "status": "A",
        },
        {
            "item": "notebook",
            "qty": 50,
            "size": {"h": 8.5, "w": 11, "uom": "in"},
            "status": "A",
        },
        {
            "item": "paper",
            "qty": 100,
            "size": {"h": 8.5, "w": 11, "uom": "in"},
            "status": "D",
        },
        {
            "item": "planner",
            "qty": 75,
            "size": {"h": 22.85, "w": 30, "uom": "cm"},
            "status": "D",
        },
        {
            "item": "postcard",
            "qty": 45,
            "size": {"h": 10, "w": 15.25, "uom": "cm"},
            "status": "A",
        },
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.find({}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 5

    cmd = """
        db.testColl.find({"status": "D"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 2

    cmd = """
        db.testColl.find({"status": {"$in": ["A", "D"]}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 5

    cmd = """
            db.testColl.find({"status": "A", qty: {"$lt": 30}}).toArray()
        """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
            db.testColl.find({"$or": [{"status": "A"}, {"qty":{"$lt": 30}}]}).toArray()
        """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 3

    cmd = """
                db.testColl.find({"status": "A", "$or": [{"item": {"$regex": "^p.*"}}, {"qty":{"$lt": 30}}]}).toArray()
            """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 2
