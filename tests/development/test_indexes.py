import json
import subprocess
from unittest.mock import ANY


def test_index_on_object(mongo_url):
    cmd = """db.testColl.insertMany([
            {type: "person", properties: {name: "Alex", location: "usa"}},
            {type: "person", properties: {name: "Alex", location: "usa", age: "1"}},
        ]
    )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """db.testColl.createIndex({properties: 1})"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """db.testColl.find({properties: {name: "Alex", location: "usa"}}).toArray()"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    assert json.loads(output.decode("utf-8")) == [
        {
            "_id": {
                "$oid": ANY,
            },
            "properties": {
                "location": "usa",
                "name": "Alex",
            },
            "type": "person",
        },
    ]

    cmd = """db.testColl.find({properties: {name: "Alex", location: "usa", age: "1"}}).toArray()"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    assert json.loads(output.decode("utf-8")) == [
        {
            "_id": {
                "$oid": ANY,
            },
            "properties": {
                "location": "usa",
                "name": "Alex",
                "age": "1",
            },
            "type": "person",
        },
    ]

    # index used
    cmd = """db.testColl.find({properties: {name: "Alex", location: "usa"}}).explain("executionStats")"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    result = json.loads(output.decode("utf-8"))
    assert result["queryPlanner"]["winningPlan"]["inputStage"]["stage"] == "IXSCAN"
    assert result["executionStats"]["nReturned"] == {"$numberInt": "1"}
    assert result["executionStats"]["totalKeysExamined"] == {"$numberInt": "1"}
    assert result["executionStats"]["totalDocsExamined"] == {"$numberInt": "1"}

    # index used
    cmd = """db.testColl.find({properties: {name: "Alex", location: "usa", age: "1"}}).explain("executionStats")"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    result = json.loads(output.decode("utf-8"))
    assert result["queryPlanner"]["winningPlan"]["inputStage"]["stage"] == "IXSCAN"
    assert result["executionStats"]["nReturned"] == {"$numberInt": "1"}
    assert result["executionStats"]["totalKeysExamined"] == {"$numberInt": "1"}
    assert result["executionStats"]["totalDocsExamined"] == {"$numberInt": "1"}

    # index used despite field order but result is empty and no one index key is examined!!!
    cmd = """db.testColl.find({properties: {location: "usa", name: "Alex"}}).explain("executionStats")"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    result = json.loads(output.decode("utf-8"))
    assert result["queryPlanner"]["winningPlan"]["inputStage"]["stage"] == "IXSCAN"
    assert result["executionStats"]["nReturned"] == {"$numberInt": "0"}
    assert result["executionStats"]["totalKeysExamined"] == {"$numberInt": "0"}
    assert result["executionStats"]["totalDocsExamined"] == {"$numberInt": "0"}


def test_case_sensitivity_collation(mongo_url):
    # collection with osme collation - somethink like collation on distinct mysql table fields
    cmd = """db.createCollection("testColl", { collation: { locale: 'en_US', strength: 2 } } )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    # create index with collation - no any mysql analogs
    cmd = """db.testColl.createIndex({type: 1}, {collation: {locale: "en", strength: 1}})"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """db.testColl.insertMany([
            {type: "person", properties: {name: "Alex", location: "usa"}},
            {type: "person", properties: {name: "Vasya", location: "eu"}},
            {type: "cat", properties: {name: "Petya", location: "ch"}},  
        ]
    )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    # use query with colation same as index -> index used
    cmd = """db.testColl.find({type: "person"}).collation({ locale: "en", strength: 1 }).explain("executionStats")"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    result = json.loads(output.decode("utf-8"))
    assert result["queryPlanner"]["winningPlan"]["inputStage"]["stage"] == "IXSCAN"
    assert result["executionStats"]["totalKeysExamined"] == {"$numberInt": "2"}
    assert result["executionStats"]["totalDocsExamined"] == {"$numberInt": "2"}

    # use query with colation same as default collection collation ->
    # index NOT used(index collation is distinct from default)
    cmd = """db.testColl.find({type: "person"}).collation({ locale: "en_US", strength: 2 }).explain("executionStats")"""
    output = subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", cmd])
    result = json.loads(output.decode("utf-8"))
    assert result["queryPlanner"]["winningPlan"]["stage"] == "COLLSCAN"
    assert result["executionStats"]["totalKeysExamined"] == {"$numberInt": "0"}
    assert result["executionStats"]["totalDocsExamined"] == {"$numberInt": "3"}
