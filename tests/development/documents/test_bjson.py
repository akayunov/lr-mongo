import datetime

from bson import BSON, Int64


def test_bson():
    data = {
        "name": "tratata",
        "$qwe": "qwe",
        # 'id': ObjectId('0123456789ab0123456789ab'),
        "date": datetime.datetime.strptime("15.05.2026 16:30:00", "%d.%m.%Y %H:%M:%S"),
        "long": Int64(1250000),
    }
    assert (
        b"A\x00\x00\x00\x02name\x00\x08\x00\x00\x00tratata\x00\x02$qwe\x00\x04\x00\x00\x00qwe\x00\tdate\x00@/y,\x9e\x01\x00\x00\x12long\x00\xd0\x12\x13\x00\x00\x00\x00\x00\x00"
        == BSON.encode(data)
    )
