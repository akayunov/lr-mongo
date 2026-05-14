import contextlib
import json
import os
import subprocess
from random import randint
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import pytest


@pytest.fixture
def db_name():
    return f"testDb_{randint(1, 1_000_000)}"


@pytest.fixture
def mongo_url(db_name):
    default_url = os.environ.get("MONGO_URL", "")
    parsed = urlparse(default_url)
    result = urlunparse(parsed._replace(path=f"/{db_name}"))
    yield result
    subprocess.check_call(["mongosh", result, "--json", "--eval", "db.dropDatabase()"])


@pytest.fixture
def co():
    def wrapper(*args, **kwargs):
        try:
            return subprocess.check_output(*args, text=True, **kwargs)
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            print(e.stderr)
    return wrapper


@pytest.fixture
def coa(mongo_url):
    def wrapper(*args, **kwargs):
        try:
            return subprocess.check_output(["mongosh", mongo_url, "--json", "--eval", *args], text=True, **kwargs)
        except subprocess.CalledProcessError as e:
            assert False, f"{e.stdout}\n{e.stderr}"
    return wrapper


@pytest.fixture(scope="session", autouse=True)
def check_sample_databases():
    default_url = os.environ.get("MONGO_URL", "")
    result = False
    cmd = """db.getMongo().getDBNames().includes('sample_mflix')"""
    try:
        output = subprocess.check_output(["mongosh", default_url, "--json", "--eval", cmd],
                                         stderr=subprocess.STDOUT,
                text=True)
        result = json.loads(output)
    except subprocess.CalledProcessError as e:
        print(e.output)
    assert result is True, 'sample database is not exists, please run `./cmd.sh ra`'


@pytest.fixture
def mongo_url_write_concern(mongo_url):
    def get_url(w_concern):
        # Разбираем URL на составляющие
        url_parts = list(urlparse(mongo_url))
        # Извлекаем текущие параметры в виде списка кортежей
        query = dict(parse_qsl(url_parts[4]))
        # Добавляем или обновляем параметр
        query["w"] = w_concern
        query["timeoutMS"] = "5000"
        # Кодируем параметры обратно в строку и сохраняем в компоненты URL
        url_parts[4] = urlencode(query)
        # Собираем URL обратно
        return urlunparse(url_parts)

    return get_url


@pytest.fixture
def mongo_url_for_user(mongo_url, db_name):
    def get_url(user, pwd):
        parsed = urlparse(mongo_url)
        new_netloc = f"{user}:{pwd}@{parsed.hostname}"
        new_query = f"{parsed.query}&authSource={db_name}"
        return urlunparse(parsed._replace(netloc=new_netloc, query=new_query))

    return get_url


@pytest.fixture
def docker_pause_node():
    @contextlib.contextmanager
    def stop_node(node):
        try:
            subprocess.check_call(
                [
                    "docker",
                    "compose",
                    "-f",
                    "/app/docker-compose.yml",
                    "-p",
                    "lr-mongo",
                    "pause",
                    f"mongo-{node}",
                ]
            )
            yield
        finally:
            subprocess.check_call(
                [
                    "docker",
                    "compose",
                    "-f",
                    "/app/docker-compose.yml",
                    "-p",
                    "lr-mongo",
                    "unpause",
                    f"mongo-{node}",
                ]
            )

    return stop_node


# @pytest.fixture
# def mongo_client_with_write_concern(mongo_url):
#     # В PyMongo 4.x параметры передаются как плоские keyword-аргументы
#     client = MongoClient(mongo_url, w="majority", wtimeoutMS=2000)  # 2 секунды (обязательно суффикс MS)
#     yield client
#     client.close()
