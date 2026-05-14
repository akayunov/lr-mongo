import json
import subprocess
from unittest import mock


def test_aggregations1(mongo_url, co):
    cmd = """
        db.getSiblingDB("sample_mflix").movies.aggregate([
            {"$match": {genres: "Drama"}},
            {"$sort": {_id: 1}},
            {"$limit": 5},
            {$project: {title: 1, _id: 0}}
        ]).toArray()
    """
    output = co(["mongosh", mongo_url, "--json", "--eval", cmd])
    result = json.loads(output)
    assert result == [
        {"title": "A Corner in Wheat"},
        {"title": "Traffic in Souls"},
        {"title": "In the Land of the Head Hunters"},
        {"title": "The Italian"},
        {"title": "Regeneration"},
    ]


def test_aggregation2(mongo_url, co):
    cmd = """db.createCollection("testColl", { collation: { locale: 'en_US', strength: 2 } } )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """db.testColl.insertMany([
        {
          customer_id: "elise_smith@myemail.com",
          orderdate: new Date("2020-05-30T08:35:52Z"),
          value: 231,
        },
        {
          customer_id: "elise_smith@myemail.com",
          orderdate: new Date("2020-01-13T09:32:07Z"),
          value: 99,
        },
        {
          customer_id: "oranieri@warmmail.com",
          orderdate: new Date("2020-01-01T08:25:37Z"),
          value: 63,
        },
        {
          customer_id: "tj@wheresmyemail.com",
          orderdate: new Date("2019-05-28T19:13:32Z"),
          value: 2,
        },
        {
          customer_id: "tj@wheresmyemail.com",
          orderdate: new Date("2020-11-23T22:56:53Z"),
          value: 187,
        },
        {
          customer_id: "tj@wheresmyemail.com",
          orderdate: new Date("2020-08-18T23:04:48Z"),
          value: 4,
        },
        {
          customer_id: "elise_smith@myemail.com",
          orderdate: new Date("2020-12-26T08:55:46Z"),
          value: 4,
        },
        {
          customer_id: "tj@wheresmyemail.com",
          orderdate: new Date("2021-02-29T07:49:32Z"),
          value: 1024,
        },
        {
          customer_id: "elise_smith@myemail.com",
          orderdate: new Date("2020-10-03T13:49:44Z"),
          value: 102,
        }
        ]
    )"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.aggregate([
            {"$match": {orderdate: {
                "$gte": new Date("2020-01-01T00:00:00Z"),
                "$lt": new Date("2021-01-01T00:00:00Z")
            }}},
            {"$sort": {orderdate: 1}},
            {"$group": {
                _id: "$customer_id",
                first_purchase_date: {$first: "$orderdate"},
                total_value: {$sum: "$value"},
                total_orders: {$sum: 1},
                orders: {
                    $push: {
                        orderdate: "$orderdate",
                        value: "$value"
                    }
                }
            }},
            { $sort: { first_purchase_date: 1 } },
            { $set: { customer_id: "$_id" } },
            { $unset: ["_id"] }
        ]).toArray()
    """
    output = co(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    result = json.loads(output)
    assert len(result) == 3
    assert result[0] == {
        "first_purchase_date": {"$date": "2020-01-01T08:25:37Z"},
        "total_value": 63,
        "total_orders": 1,
        "orders": [{"orderdate": {"$date": "2020-01-01T08:25:37Z"}, "value": 63}],
        "customer_id": "oranieri@warmmail.com",
    }


def test_variables(mongo_url, co):
    cmd = """
        db.aggregate([
            {
                // Создаем виртуальный документ из пустоты
                $documents: [ {
                    initial_document: "initial document value",
                    list_field: ['a', 'b', 'c'],
                    xxx_to_remove: 1
                } ] 
            },
            {
                $project: {
                    now: "$$NOW",
                    cluster_time: "$$CLUSTER_TIME",
                    root: "$$ROOT",
                    // current: "$$CURRENT",
                    remove: {
                        $cond :{
                            if: {$ne: ["$xxx_to_remove", 1]},
                            then: "NOT REMOVED",
                            else: "$$REMOVE"
                        }
                    },
                    // descent: "$$DESCENT",
                    // prune: "$$PRUNE",
                    // keep: "$$KEEP",
                    // search_meta: "$$SEARCH_META",
                    user_roles: "$$USER_ROLES",
                    // idx: "$$IDX",
                    idx: {
                        $map: {
                            input: "$list_field",
                            in: {
                                item_index: "$$IDX",  // Получаем индекс элемента (0, 1, 2)
                                item_name: "$$this"   // Получаем значение элемента
                            }
                        }
                    }
                },
            },
            {
                $merge: {
                    into: 'testColl',
                    on: "_id", 
                    whenMatched: "replace",
                    whenNotMatched: "insert"
                }
            }
        ]).toArray()
    """
    output = co(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert output == "[]\n"
    cmd = """
        db.testColl.find().toArray()
    """
    output = co(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    print(output)
    assert json.loads(output) == [
        {
            "_id": {"$oid": mock.ANY},
            "now": {"$date": mock.ANY},
            "cluster_time": {"$timestamp": {"t": mock.ANY, "i": mock.ANY}},
            "root": {
                "initial_document": "initial document value",
                "list_field": ["a", "b", "c"],
                "xxx_to_remove": 1,
            },
            "user_roles": [{"_id": "admin.root", "role": "root", "db": "admin"}],
            "idx": [
                {
                    "item_index": 0,
                    "item_name": "a",
                },
                {
                    "item_index": 1,
                    "item_name": "b",
                },
                {
                    "item_index": 2,
                    "item_name": "c",
                },
            ],
        }
    ]
