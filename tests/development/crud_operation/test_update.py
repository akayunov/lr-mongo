import json
import subprocess
from unittest.mock import ANY


def test_basic(mongo_url):
    cmd = """
        db.testColl.insertMany([
            {
                "item": "canvas",
                "qty": 100,
                "size": {"h": 28, "w": 35.5, "uom": "cm"},
                "status": "A",
            },
            {
                "item": "journal",
                "qty": 25,
                "size": {"h": 14, "w": 21, "uom": "cm"},
                "status": "A",
            },
            {
                "item": "mat",
                "qty": 85,
                "size": {"h": 27.9, "w": 35.5, "uom": "cm"},
                "status": "A",
            },
            {
                "item": "mousepad",
                "qty": 25,
                "size": {"h": 19, "w": 22.85, "uom": "cm"},
                "status": "P",
            },
            {
                "item": "notebook",
                "qty": 50,
                "size": {"h": 8.5, "w": 11, "uom": "in"},
                "status": "P",
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
            {
                "item": "sketchbook",
                "qty": 80,
                "size": {"h": 14, "w": 21, "uom": "cm"},
                "status": "A",
            },
            {
                "item": "sketch pad",
                "qty": 95,
                "size": {"h": 22.85, "w": 30.5, "uom": "cm"},
                "status": "A",
            },
        ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl.updateOne(
        {item: "paper"}, 
        {
            $set: {"size.uom": "cm", status: "P"},
            $currentDate: {lastModified: true}
        }
        )
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    assert json.loads(output.decode()) == {
        "acknowledged": True,
        "insertedId": None,
        "matchedCount": 1,
        "modifiedCount": 1,
        "upsertedCount": 0,
    }

    cmd = """
        db.testColl.find({item: "paper"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": {"$oid": ANY},
            "item": "paper",
            "qty": 100,
            "size": {"h": 8.5, "w": 11, "uom": "cm"},
            "status": "P",
            "lastModified": {"$date": ANY},
        }
    ]

    cmd = """
        db.testColl.updateMany(
            {qty: {$lt: 50}},
            {$set: {"size.uom": "in", "status": "P"}, "$currentDate": {"lastModified": true}}
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({qty: {$in: [45,25]}}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": {"$oid": ANY},
            "item": "journal",
            "lastModified": {"$date": ANY},
            "qty": 25,
            "size": {"h": 14, "uom": "in", "w": 21},
            "status": "P",
        },
        {
            "_id": {"$oid": ANY},
            "item": "mousepad",
            "lastModified": {"$date": ANY},
            "qty": 25,
            "size": {"h": 19, "uom": "in", "w": 22.85},
            "status": "P",
        },
        {
            "_id": {"$oid": ANY},
            "item": "postcard",
            "lastModified": {"$date": ANY},
            "qty": 45,
            "size": {"h": 10, "uom": "in", "w": 15.25},
            "status": "P",
        },
    ]

    cmd = """
        db.testColl.replaceOne(
            {item: "paper"},
            {item: "tratata"}
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({item: "tratata"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": {"$oid": ANY},
            "item": "tratata",
        },
    ]
