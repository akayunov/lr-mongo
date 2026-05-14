import json
import subprocess
from unittest.mock import ANY


def test_basic(mongo_url):
    cmd = """
        db.testColl.insertMany([
           { _id: 1, test1: 95, test2: 92, test3: 90, modified: new Date("01/05/2020") },
           { _id: 2, test1: 98, test2: 100, test3: 102, modified: new Date("01/05/2020") },
           { _id: 3, test1: 95, test2: 110, modified: new Date("01/04/2020") }
        ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl.updateOne(
        {_id: 3}, 
        [{$set: {newField: 58, modified: "$$NOW"}}]
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({_id: 3},).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {"_id": 3, "test1": 95, "test2": 110, "modified": {"$date": ANY}, "newField": 58}
    ]

    cmd = """   
        db.testColl.updateMany(
        {}, 
        [
            {$replaceRoot: {newRoot:{
                $mergeObjects: [{tratata:1} , "$$ROOT"]
            }}},
            {$set: {modified: "$$NOW"}}
        ]
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find().toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {"_id": 1, "test1": 95, "test2": 92, "test3": 90, "tratata": 1, "modified": {"$date": ANY}},
        {"_id": 2, "test1": 98, "test2": 100, "test3": 102, "tratata": 1, "modified": {"$date": ANY}},
        {"_id": 3, "test1": 95, "test2": 110, "newField": 58, "tratata": 1, "modified": {"$date": ANY}},
    ]

    cmd = """
        db.testColl2.insertMany([
           { "_id" : 1, "tests" : [ 95, 92, 90 ], "modified" : ISODate("2019-01-01T00:00:00Z") },
           { "_id" : 2, "tests" : [ 94, 88, 90 ], "modified" : ISODate("2019-01-01T00:00:00Z") },
           { "_id" : 3, "tests" : [ 70, 75, 82 ], "modified" : ISODate("2019-01-01T00:00:00Z") }
        ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl2.updateMany(
        {}, 
        [
           {$set: {average: {$trunc: [{$avg: "$tests"}, 0]}, modified: "$$NOW"}},
           {$set: {grade: {$switch:{
                branches: [
                    {case: {$gte: ["$average", 90]}, then:"A"},
                    {case: {$gte: ["$average", 80]}, then:"B"},
                    {case: {$gte: ["$average", 70]}, then:"C"},
                    {case: {$gte: ["$average", 60]}, then:"D"},
                ],
                default: "F"
           }}}}
        ]
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl2.find().toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": 1,
            "average": 92,
            "grade": "A",
            "modified": {
                "$date": ANY,
            },
            "tests": [
                95,
                92,
                90,
            ],
        },
        {
            "_id": 2,
            "average": 90,
            "grade": "A",
            "modified": {
                "$date": ANY,
            },
            "tests": [
                94,
                88,
                90,
            ],
        },
        {
            "_id": 3,
            "average": 75,
            "grade": "C",
            "modified": {
                "$date": ANY,
            },
            "tests": [
                70,
                75,
                82,
            ],
        },
    ]

    cmd = """
        db.testColl3.insertMany([
           { _id: 1, flavor: "chocolate" },
           { _id: 2, flavor: "strawberry" },
           { _id: 3, flavor: "cherry" }
        ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl3.updateMany(
        {$expr: {$eq: ["$flavor","$$targetFlavor"]}},
        [{
            $set: {flavor: "$$newFlavor"}
        }],
        {let: {targetFlavor: "cherry", newFlavor:"orange"}}
    )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl3.find().toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {"_id": 1, "flavor": "chocolate"},
        {"_id": 2, "flavor": "strawberry"},
        {"_id": 3, "flavor": "orange"},
    ]
