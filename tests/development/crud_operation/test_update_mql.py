import json
import subprocess


def test_basic(mongo_url):
    cmd = """
        db.testColl.insertMany([
              {
                 _id: 'SF',
                 engineering: [
                    { name: 'Alice', email: 'missingEmail', salary: 100000 },
                    { name: 'Bob', email: 'missingEmail', salary: 75000 }
                 ],
                 sales: [
                    { name: 'Charlie', email: 'charlie@mail.com', salary: 90000, bonus: 1000 }
                 ]
              },
              {
                 _id: 'NYC',
                 engineering: [
                    { name: 'Dave', email: 'dave@mail.com', salary: 55000 },
                 ],
                 sales: [
                    { name: 'Ed', email: 'ed@mail.com', salary: 99000, bonus: 2000 },
                    { name: 'Fran', email: 'fran@mail.com', salary: 50000, bonus: 10000 }
                 ]
              }
           ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl.updateOne(
            {"engineering.email": "missingEmail"}, 
            {$set: {"engineering.$.email": "alice@mail.com"}}
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({_id: "SF"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": "SF",
            "engineering": [
                {"name": "Alice", "email": "alice@mail.com", "salary": 100000},
                {"name": "Bob", "email": "missingEmail", "salary": 75000},
            ],
            "sales": [{"name": "Charlie", "email": "charlie@mail.com", "salary": 90000, "bonus": 1000}],
        },
    ]

    cmd = """   
        db.testColl.updateOne(
            {"engineering": {$elemMatch:{name: "Bob", email:"missingEmail"}}}, 
            {$set: {"engineering.$.email": "bob@mail.com"}}
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({_id: "SF"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": "SF",
            "engineering": [
                {"name": "Alice", "email": "alice@mail.com", "salary": 100000},
                {"name": "Bob", "email": "bob@mail.com", "salary": 75000},
            ],
            "sales": [{"name": "Charlie", "email": "charlie@mail.com", "salary": 90000, "bonus": 1000}],
        },
    ]

    cmd = """   
        db.testColl.updateOne(
            { "_id": "NYC" }, 
            {$inc: {"sales.$[].bonus": 2000}}
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({_id: "NYC"}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": "NYC",
            "engineering": [
                {
                    "email": "dave@mail.com",
                    "name": "Dave",
                    "salary": 55000,
                },
            ],
            "sales": [
                {
                    "bonus": 4000,
                    "email": "ed@mail.com",
                    "name": "Ed",
                    "salary": 99000,
                },
                {
                    "bonus": 12000,
                    "email": "fran@mail.com",
                    "name": "Fran",
                    "salary": 50000,
                },
            ],
        },
    ]

    cmd = """   
        db.testColl.updateMany(
            {},
            {$set:{
                "engineering.$[elemX].salary": 95000,
                "sales.$[elemY].salary": 75000
            }},
            {
                arrayFilters:[
                    {"elemX.name": "Bob", "elemX.salary": 75000},
                    {"elemY.name":"Ed", "elemY.salary":50000}
                ]
            }
        )
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.find({"engineering.name": "Bob"}, {engineering: {$elemMatch:{name:"Bob"}} ,_id:0}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [{"engineering": [{"name": "Bob", "email": "bob@mail.com", "salary": 95000}]}]
