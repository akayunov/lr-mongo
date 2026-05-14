import json
import subprocess


def test_create(mongo_url):
    cmd = """
    db.testColl.insertMany(
    [
       { date: ISODate("2018-12-01"), item: "Cake - Chocolate", quantity: 2, amount: Decimal128("60") },
       { date: ISODate("2018-12-02"), item: "Cake - Peanut Butter", quantity: 5, amount: Decimal128("90") },
       { date: ISODate("2018-12-02"), item: "Cake - Red Velvet", quantity: 10, amount: Decimal128("200") },
       { date: ISODate("2018-12-04"), item: "Cookies - Chocolate Chip", quantity: 20, amount: Decimal128("80") },
       { date: ISODate("2018-12-04"), item: "Cake - Peanut Butter", quantity: 1, amount: Decimal128("16") },
       { date: ISODate("2018-12-05"), item: "Pie - Key Lime", quantity: 3, amount: Decimal128("60") },
       { date: ISODate("2019-01-25"), item: "Cake - Chocolate", quantity: 2, amount: Decimal128("60") },
       { date: ISODate("2019-01-25"), item: "Cake - Peanut Butter", quantity: 1, amount: Decimal128("16") },
       { date: ISODate("2019-01-26"), item: "Cake - Red Velvet", quantity: 5, amount: Decimal128("100") },
       { date: ISODate("2019-01-26"), item: "Cookies - Chocolate Chip", quantity: 12, amount: Decimal128("48") },
       { date: ISODate("2019-01-26"), item: "Cake - Carrot", quantity: 2, amount: Decimal128("36") },
       { date: ISODate("2019-01-26"), item: "Cake - Red Velvet", quantity: 5, amount: Decimal128("100") },
       { date: ISODate("2019-01-27"), item: "Pie - Chocolate Cream", quantity: 1, amount: Decimal128("20") },
       { date: ISODate("2019-01-27"), item: "Cake - Peanut Butter", quantity: 5, amount: Decimal128("80") },
       { date: ISODate("2019-01-27"), item: "Tarts - Apple", quantity: 3, amount: Decimal128("12") },
       { date: ISODate("2019-01-27"), item: "Cookies - Chocolate Chip", quantity: 12, amount: Decimal128("48") },
       { date: ISODate("2019-01-27"), item: "Cake - Carrot", quantity: 5, amount: Decimal128("36") },
       { date: ISODate("2019-01-27"), item: "Cake - Red Velvet", quantity: 5, amount: Decimal128("100") },
       { date: ISODate("2019-01-28"), item: "Cookies - Chocolate Chip", quantity: 20, amount: Decimal128("80") },
       { date: ISODate("2019-01-28"), item: "Pie - Key Lime", quantity: 3, amount: Decimal128("60") },
       { date: ISODate("2019-01-28"), item: "Cake - Red Velvet", quantity: 5, amount: Decimal128("100") }
    ]
    )
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.aggregate([
            {
                $match: {date: {$gte: new ISODate('1970-01-01')}}
            },
            {
                $group:{_id: {$dateToString: {format: "%Y-%m", date: '$date'}}, sales_quantity: {$sum: '$quantity'}, sales_amount: {$sum: '$amount'}}
            },
            {
                $merge: { into: 'monthlybakesales', whenMatched: 'replace'}
            }
        ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--eval", cmd])

    cmd = """
        db.monthlybakesales.find().sort({_id: 1}).toArray()
    """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": "2018-12",
            "sales_amount": {"$numberDecimal": "506"},
            "sales_quantity": 41,
        },
        {
            "_id": "2019-01",
            "sales_amount": {"$numberDecimal": "896"},
            "sales_quantity": 86,
        },
    ]

    cmd = """
        db.testColl.insertMany( [
           { date: ISODate("2019-01-28"), item: "Cake - Chocolate", quantity: 3, amount: Decimal128("90") },
           { date: ISODate("2019-01-28"), item: "Cake - Peanut Butter", quantity: 2, amount: Decimal128("32") },
           { date: ISODate("2019-01-30"), item: "Cake - Red Velvet", quantity: 1, amount: Decimal128("20") },
           { date: ISODate("2019-01-30"), item: "Cookies - Chocolate Chip", quantity: 6, amount: Decimal128("24") },
           { date: ISODate("2019-01-31"), item: "Pie - Key Lime", quantity: 2, amount: Decimal128("40") },
           { date: ISODate("2019-01-31"), item: "Pie - Banana Cream", quantity: 2, amount: Decimal128("40") },
           { date: ISODate("2019-02-01"), item: "Cake - Red Velvet", quantity: 5, amount: Decimal128("100") },
           { date: ISODate("2019-02-01"), item: "Tarts - Apple", quantity: 2, amount: Decimal128("8") },
           { date: ISODate("2019-02-02"), item: "Cake - Chocolate", quantity: 2, amount: Decimal128("60") },
           { date: ISODate("2019-02-02"), item: "Cake - Peanut Butter", quantity: 1, amount: Decimal128("16") },
           { date: ISODate("2019-02-03"), item: "Cake - Red Velvet", quantity: 5, amount: Decimal128("100") }
        ] )
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cmd = """
        db.testColl.aggregate([
            {
                $match: {date: {$gte: new ISODate('2019-01-01')}}
            },
            {
                $group:{_id: {$dateToString: {format: "%Y-%m", date: '$date'}}, sales_quantity: {$sum: '$quantity'}, sales_amount: {$sum: '$amount'}}
            },
            {
                $merge: { into: 'monthlybakesales', whenMatched: 'replace'}
            }
        ])
    """
    subprocess.check_output(["mongosh", mongo_url, "--eval", cmd])

    cmd = """
            db.monthlybakesales.find().sort({_id: 1}).toArray()
        """
    output = subprocess.check_output(["mongosh", mongo_url, "--json=relaxed", "--eval", cmd])
    assert json.loads(output.decode()) == [
        {
            "_id": "2018-12",
            "sales_amount": {"$numberDecimal": "506"},
            "sales_quantity": 41,
        },
        {
            "_id": "2019-01",
            "sales_amount": {"$numberDecimal": "1142"},
            "sales_quantity": 102,
        },
        {
            "_id": "2019-02",
            "sales_amount": {"$numberDecimal": "284"},
            "sales_quantity": 15,
        },
    ]
