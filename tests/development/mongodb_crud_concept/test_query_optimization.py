import json
import subprocess


def test_explain_covered_index(mongo_url):
    cmd = """db.testColl.createIndex(
                {name: 1, age:1},
        )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """db.testColl.insertOne(
            {name: "Alex", age: 3},
    )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.find({name: "Alex"}, {_id: 0, age: 1, name: 1}).explain()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    result = json.loads(output.decode())
    assert result["queryPlanner"]["winningPlan"]["stage"] == "PROJECTION_COVERED"
    assert result["queryPlanner"]["winningPlan"]["inputStage"]["stage"] == "IXSCAN"
