import json
import subprocess


def test_basic(mongo_url):
    cmd = """
    db.testColl.insertMany([
        {
            "item": null,
            "status": "A",
            "size": {"h": 14, "w": 21, "uom": "cm"},
            "instock": [{"warehouse": "A", "qty": 5}],
        },
        {
            "status": "A",
            "size": {"h": 8.5, "w": 11, "uom": "in"},
            "instock": [{"warehouse": "C", "qty": 5}],
        },
        {
            "item": "journal",
            "status": "A",
            "size": {"h": 14, "w": 21, "uom": "cm"},
            "instock": [{"warehouse": "A", "qty": 5}],
        },
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.find({item: null}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 2

    cmd = """
        db.testColl.find({item: {$ne: null}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
        db.testColl.find({item: {$type: 10}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
        db.testColl.find({item: {$exists: false}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 1

    cmd = """
        db.testColl.find({item: {$exists: true}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 2
