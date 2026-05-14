import subprocess


def test_schema_validation(mongo_url):
    cc = {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "title": "Some validator",
                "required": ["address"],
                "properties": {
                    "name": {
                        "bsonType": "string",
                        "description": "'name' must be string"
                    },
                    "year": {
                        "bsonType": "int",
                        "description": "'year must be in interval'",
                        "minimum": 1,
                        "maximum": 31,
                    }
                }
            }
        }
    }
    cmd = f"""db.createCollection("testColl",  {cc})"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """db.testColl.insertOne({name: "Alex", "year": 32, address:1})"""
    output = subprocess.run(["mongosh", mongo_url, "--json", "--eval", cmd], capture_output=True)
    assert b'"Document failed validation"' in output.stdout

    cmd = """db.testColl.insertOne({name: "Alex", "year": 31, address: 2})"""
    output = subprocess.run(["mongosh", mongo_url, "--json", "--eval", cmd], capture_output=True)
    assert b'"Document failed validation"' not in output.stdout


