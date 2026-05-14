import json
import subprocess
from unittest.mock import ANY


def test_create(mongo_url):
    cmd = """
        db.createCollection('myCappedCollSizeLImit', {capped: true, size: 100000})
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.createCollection('myCappedCollCountLimit', {capped: true, size: 100000, max: 100})
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.myCappedCollCountLimit.insertMany([
               {
                  message: "system start",
                  type: "startup",
                  time: 1711403508
               },
               {
                  message: "user login attempt",
                  type: "info",
                  time: 1711403907
               },
               {
                  message: "user login fail",
                  type: "warning",
                  time: 1711404209
               },
               {
                  message: "user login success",
                  type: "info",
                  time: 1711404367
               },
               {
                  message: "user logout",
                  type: "info",
                  time: 1711404555
               }
        ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.myCappedCollCountLimit.find({type: 'info'}).limit(1).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "message": "user login attempt",
            "type": "info",
            "time": ANY,
            "_id": {"$oid": ANY},
        }
    ]
