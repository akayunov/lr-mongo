import subprocess


def test_write_concern(mongo_url_write_concern, docker_pause_node):
    cmd = """db.testColl.insertMany(
           [
               {'sID': 22001, 'name': "Alex", 'year': 1, 'score': 4.0},
           ]
       )"""
    subprocess.check_call(["mongosh", mongo_url_write_concern("majority"), "--json", "--eval", cmd])
    # паузим только  реплики
    with docker_pause_node("secondary1"), docker_pause_node("secondary2"):
        cmd = """db.testColl.insertMany(
                   [
                       {"sID": 22002, "name": "Vasya", "year": 2, "score": 5.0},
                   ]
               )"""
        result = subprocess.run(
            [
                "mongosh",
                mongo_url_write_concern("majority"),
                "--json",
                "--eval",
                cmd,
            ],
            capture_output=True,
            text=True,  # Декодируем байты в строку автоматически
        )

        assert result.returncode != 0
        # Проверяем наличие нужного текста в выводе
        expected_error = "Server reported a timeout error"
        expected_error2 = "Timed out during socket read"
        assert expected_error in result.stdout or expected_error in result.stderr or expected_error2 in result.stdout
