import json
import subprocess
from unittest.mock import ANY


def test_create_and_query(mongo_url, mongo_url_for_user):
    cmd = """db.testColl.insertMany(
        [
            {'sID': 22001, 'name': "Alex", 'year': 1, 'score': 4.0},
            {'sID': 21001, 'name': "bernie", 'year': 2, 'score': 3.7},
            {'sID': 20010, 'name': "Chris", 'year': 3, 'score': 2.5},
            {'sID': 22021, 'name': "Drew", 'year': 1, 'score': 3.2},
            {'sID': 17301, 'name': "harley", 'year': 6, 'score': 3.1},
            {'sID': 21022, 'name': "Farmer", 'year': 1, 'score': 2.2},
            {'sID': 20020, 'name': "george", 'year': 3, 'score': 2.8},
            {'sID': 18020, 'name': "Harley", 'year': 5, 'score': 2.8},
        ]
    )"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    assert json.loads(output.decode()) == {
        "acknowledged": True,
        "insertedIds": {
            "0": {"$oid": ANY},
            "1": {"$oid": ANY},
            "2": {"$oid": ANY},
            "3": {"$oid": ANY},
            "4": {"$oid": ANY},
            "5": {"$oid": ANY},
            "6": {"$oid": ANY},
            "7": {"$oid": ANY},
        },
    }

    cmd = """
        db.createCollection('testView', {
            'viewOn': "testColl",
            'pipeline':[{$match: {year: 1}}],
        })
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    assert json.loads(output.decode()) == {"ok": {"$numberInt": "1"}}

    cmd = 'db.testView.find({}, {"_id":0}).toArray()'
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 3

    cmd = """
        db.createCollection('testView2', {
            'viewOn': "testColl",
            'pipeline':[{$match: {year: {"$gt": 4}}}],
            'collation': {'locale': 'en', 'caseFirst':'upper'}
        })
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    assert json.loads(output.decode()) == {"ok": {"$numberInt": "1"}}

    cmd = """
        db.testView2.aggregate(
            [
                {$sort:{name: 1}},
                {$unset:["_id"]}
            ]
        ).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    response = json.loads(output.decode())
    assert len(response) == 2
    assert response[0]["name"] == "Harley"
    assert response[1]["name"] == "harley"


def test_view_roles(db_name, mongo_url, mongo_url_for_user):
    cmd = """db.createRole({
        role: "testRole1",    
        privileges:[{
            resource: {
                db: db.getName(), collection:"testView"
            },
            actions:["find"]}],
        roles:[]
    })"""
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """db.createRole({
        role: "testRole2",    
        privileges:[{
            resource: {
                db: db.getName(), collection:"testView"
            },
            actions:["find"]}],
        roles:[]
    })"""
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """db.createUser({
        user:'testUser1', 
        pwd:'123', 
        roles:[{
            role: "testRole1", 
            db: db.getName()
        }]
    })"""
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """db.createUser({
        user:'testUser2', 
        pwd:'321', 
        roles:[{
            role: "testRole2", 
            db: db.getName()
        }]
    })"""
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.testColl.insertMany( [
       {
          _id: 0,
          patientName: "Jack Jones",
          diagnosisCode: "CAS 17",
          creditCard: "1234-5678-9012-3456"
       },
       {
          _id: 1,
          patientName: "Mary Smith",
          diagnosisCode: "ACH 01",
          creditCard: "6541-7534-9637-3456"
       }
    ] )
    """
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """
        db.createView(
            'testView',
            'testColl',
            [
                {
                $set: {
                    'diagnosisCode':{
                        $cond:{
                            if: {$in:["testRole1", '$$USER_ROLES.role']},
                            then:"$diagnosisCode",
                            else: '$$REMOVE'
                        }
                    }
                }	
                },
                {
                $set : {
                    'creditCard':{
                        $cond: {
                            if: {$in:['testRole2', '$$USER_ROLES.role']},
                            then:'$creditCard',
                            else:'$$REMOVE'
                        }
                    }
                }
                }
            ]
            )
    """
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """db.testView.find().toArray()"""
    output = subprocess.check_output(
        [
            "mongosh",
            mongo_url_for_user("testUser1", "123"),
            "--json=relaxed",
            "--eval",
            cmd,
        ]
    )

    assert json.loads(output.decode()) == [
        {"_id": 0, "patientName": "Jack Jones", "diagnosisCode": "CAS 17"},
        {"_id": 1, "patientName": "Mary Smith", "diagnosisCode": "ACH 01"},
    ]

    cmd = """db.testView.find().toArray()"""
    output = subprocess.check_output(
        [
            "mongosh",
            mongo_url_for_user("testUser2", "321"),
            "--json=relaxed",
            "--eval",
            cmd,
        ]
    )
    assert json.loads(output.decode()) == [
        {"_id": 0, "patientName": "Jack Jones", "creditCard": "1234-5678-9012-3456"},
        {"_id": 1, "patientName": "Mary Smith", "creditCard": "6541-7534-9637-3456"},
    ]


def test_get_user_roles(db_name, mongo_url, mongo_url_for_user):
    cmd = """
    db.testColl.insert({
        'qwe':1
    })
    """
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """db.createRole({
        role: "testRole1",    
        privileges:[{
            resource: {
                db: db.getName(), collection:"testColl"
            },
            actions:["find"]}],
        roles:[]
    })"""
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])

    cmd = """db.createUser({
        user:'testUser1', 
        pwd:'123', 
        roles:[{
            role: "testRole1", 
            db: db.getName()
        }]
    })"""
    subprocess.check_call(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    cmd = """db.testColl.find({}, {'testUser1Roles': "$$USER_ROLES"}).toArray()"""
    output = subprocess.check_output(
        [
            "mongosh",
            mongo_url_for_user("testUser1", "123"),
            "--json=relaxed",
            "--eval",
            cmd,
        ]
    )
    assert json.loads(output.decode()) == [
        {
            "_id": {
                "$oid": ANY,
            },
            "testUser1Roles": [
                {
                    "_id": f"{db_name}.testRole1",
                    "db": db_name,
                    "role": "testRole1",
                },
            ],
        },
    ]
