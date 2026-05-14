import json
import subprocess


def test_basic(mongo_url):
    cmd = """
    db.testColl.insertMany([
        {
            "item": "journal",
            "status": "A",
            "size": {"h": 14, "w": 21, "uom": "cm"},
            "instock": [{"warehouse": "A", "qty": 5}],
        },
        {
            "item": "notebook",
            "status": "A",
            "size": {"h": 8.5, "w": 11, "uom": "in"},
            "instock": [{"warehouse": "C", "qty": 5}],
        },
        {
            "item": "paper",
            "status": "D",
            "size": {"h": 8.5, "w": 11, "uom": "in"},
            "instock": [{"warehouse": "A", "qty": 60}],
        },
        {
            "item": "planner",
            "status": "D",
            "size": {"h": 22.85, "w": 30, "uom": "cm"},
            "instock": [{"warehouse": "A", "qty": 40}],
        },
        {
            "item": "postcard",
            "status": "A",
            "size": {"h": 10, "w": 15.25, "uom": "cm"},
            "instock": [{"warehouse": "B", "qty": 15}, {"warehouse": "C", "qty": 35}],
        },
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.find({status: "A"}, {item:1, status:1, "instock.warehouse": 1}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode())[0].get("_id") is not None
    assert json.loads(output.decode())[0].get("item") is not None
    assert json.loads(output.decode())[0].get("status") is not None
    assert json.loads(output.decode())[0].get("instock")[0].get("warehouse") is not None
    assert len(json.loads(output.decode())[0].get("instock")[0].keys()) == 1

    cmd = """
        db.testColl.find({}, {item:1, status:1, instock: {$slice: -1}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode())[0].get("instock")[0].get("qty") is not None
