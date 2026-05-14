import json
import subprocess
from unittest.mock import ANY


def test_basic(mongo_url):
    cmd = """
       db.testColl.insertMany([
            { _id: 1, name: "Java Hut", description: "Coffee and cakes" },
            { _id: 2, name: "Burger Buns", description: "Gourmet hamburgers" },
            { _id: 3, name: "Coffee Shop", description: "Just coffee" },
            { _id: 4, name: "Clothes Clothes Clothes", description: "Discount clothing" },
            { _id: 5, name: "Java Shopping", description: "Indonesian goods" },
            { _id: 6, name: "NYC_Coffee Shop", description: "local NYC coffee" }
            ]     
       ) 
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """   
        db.testColl.createIndex({name: "text", "description": "text"})
    """
    subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    cmd = """
            db.testColl.find({$text: {$search:"coffe shop"}}).sort({score:{$meta: "textScore"}}).toArray()
        """

    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert len(json.loads(output.decode())) == 3
