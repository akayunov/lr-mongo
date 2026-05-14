import json
import subprocess


def test_atomic_update_without_transaction(mongo_url):
    cmd = """db.testColl.insertMany(
        [
            {'sID': 22001, 'name': "Alex", 'year': 1, 'score': 4.0},
        ]
    )"""
    subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl.updateOne(
        {name: "Alex"}, 
        {
            $set: {name: "Vasya"},
        }
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({name: "Vasya"}, {_id: 0}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [{"sID": 22001, "name": "Vasya", "year": 1, "score": 4}]
