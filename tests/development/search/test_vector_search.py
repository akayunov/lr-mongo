import json
import math
import os
import tempfile
import time
from pathlib import Path


def test_basic(mongo_url, coa):
    cmd = """db.getSiblingDB('sample_mflix').embedded_movies.createSearchIndex(
              "vector_index", 
              "vectorSearch", 
              {
                "fields": [
                  {
                    "type": "vector",
                    "path": "plot_embedding_voyage_3_large",
                    "numDimensions": 2048,
                    "similarity": "dotProduct",
                    "quantization": "scalar"
                  }
                ]
              }
            );
            """
    coa(cmd)

    with open(f'{Path(__file__).with_name("query_embedings.json")}') as f:
        embds = json.loads(f.read())
    query = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "plot_embedding_voyage_3_large",
                "queryVector": embds["QUERY_EMBEDDING1"],
                "numCandidates": 150,
                "limit": 2,
            }
        },
        {"$project": {"_id": 0, "plot": 1, "title": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    cmd = f"""db.getSiblingDB('sample_mflix').embedded_movies.aggregate({query}).toArray()"""
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "plot": "At the age of 21, Tim discovers he can travel in time and change what "
            "happens and has happened in his own life. His decision to make his "
            "world a better place by getting a girlfriend turns out not to be as "
            "easy as you might think.",
            "title": "About Time",
            "score": 0.7704319953918457,
        },
        {
            "plot": "A psychiatrist makes multiple trips through time to save a woman that "
            "was murdered by her brutal husband.",
            "title": "Retroactive",
            "score": 0.760108470916748,
        },
    ]


def test_mock_vector(coa):
    figures = [
        "круг",
        "10угольник",
        "9угольник",
        "8угольник",
        "7угольник",
        "6угольник",
        "5угольник",
        "квадрат",
        "треугольник",
    ]
    colours = ["красный", "оранжевый", "желтый", "зеленый", "голубой", "синий", "фиолетовый"]
    data_to_insert = []
    # во всех векторах только один элемент 1 значит и длина вектора 1 поэтому значения нормировать не нужно 1/1==1
    for c_i, colour in enumerate(colours):
        for f_i, figure in enumerate(figures):
            vector_figure = [0] * len(figures)
            vector_colour = [0] * len(colours)
            vector_figure[f_i] = 1
            vector_colour[c_i] = 1
            data_to_insert.append(
                {"figure": figure, "colour": colour, "vector_figure": vector_figure, "vector_colour": vector_colour}
            )

    cmd = f"db.testColl.insertMany({data_to_insert})"
    coa(cmd)

    # create index
    query = {
        "fields": [
            {
                "type": "vector",
                "path": "vector_figure",
                "numDimensions": len(figures),
                "similarity": "dotProduct",
                "quantization": "scalar",
            },
            {
                "type": "vector",
                "path": "vector_colour",
                "numDimensions": len(colours),
                "similarity": "dotProduct",
                "quantization": "scalar",
            },
        ]
    }
    cmd = f"""db.testColl.createSearchIndex(
              "vector_index_name",
              "vectorSearch",
              {query}
            )
            """
    coa(cmd)

    # wait till index create
    time.sleep(5)
    query = [
        {
            "$vectorSearch": {
                "index": "vector_index_name",
                "path": "vector_figure",
                # ищем элемент на 100% 9угольник, длина этого вектора 1 а значит так же нормировать не нужно
                "queryVector": [
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
                "numCandidates": 150,
                "limit": 2,
            }
        },
        {"$project": {"_id": 0, "figure": 1, "vector_figure": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    cmd = f"""db.testColl.aggregate({query}).toArray()"""
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "figure": "9угольник",
            "vector_figure": [
                0,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            "score": 1,
        },
        {
            "figure": "9угольник",
            "vector_figure": [
                0,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            "score": 1,
        },
    ]

    # создадим документ с частичными значениями, для удобства будем считать вклады от разных фигур в процентах
    vector_figure = [
        10,
        21,
        32,
        43,
        54,
        65,
        76,
        87,
        98,
    ]  # фигура котора ближе к треугольнику чем к кругу, "но это не точно"
    vector_colour = [99, 88, 77, 66, 55, 44, 33]  # цвет который ближе к красному, "но это не точно"

    # так как длина этих векторов не 1 то их надо нормировать
    figure_norm = math.sqrt(sum(i * i for i in vector_figure))
    vector_figure = [el / figure_norm for el in vector_figure]

    colour_norm = math.sqrt(sum(i * i for i in vector_colour))
    vector_colour = [el / colour_norm for el in vector_colour]
    value = [
        {
            "figure": "смесь фигур",
            "colour": "смесь цветов",
            "vector_figure": vector_figure,
            "vector_colour": vector_colour,
        }
    ]
    cmd = f"db.testColl.insertMany({value})"
    coa(cmd)

    # wait till value will be indexed
    time.sleep(5)
    # ищем нашу не определившуюся фигуру, которая ближе к треугольнику чем к остальным
    # так как длина вектора не 1 то его тоже надо нормировать
    query_vector = [
        0,
        0,
        0,
        0,
        0,
        0,
        54,
        67,
        88,
    ]
    query_vector_norm = math.sqrt(sum(i * i for i in query_vector))
    query_vector = [el / query_vector_norm for el in query_vector]
    query = [
        {
            "$vectorSearch": {
                "index": "vector_index_name",
                "path": "vector_figure",
                "queryVector": query_vector,
                "numCandidates": 150,
                "limit": 2,
            }
        },
        {"$project": {"_id": 0, "figure": 1, "vector_figure": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    cmd = f"""db.testColl.aggregate({query}).toArray()"""
    output = coa(cmd)
    assert json.loads(output) == [
        {
            "figure": "смесь фигур",
            "vector_figure": [
                0.05463257492190807,
                0.11472840733600695,
                0.17482423975010583,
                0.23492007216420469,
                0.29501590457830357,
                0.35511173699240245,
                0.41520756940650133,
                0.4753034018206002,
                0.535399234234699,
            ],
            "score": 0.9369728565216064,
        },
        {
            "figure": "треугольник",
            "vector_figure": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
            ],
            "score": 0.8575060963630676,
        },
    ]


# нужно много памяти, сильно свопится система
def self_embeddings(get_embeddings, coa):
    # check vector generation
    # curl -i -X POST http://openai-proxy:8000/embeddings \
    #                                     -H "Content-Type: application/json" \
    #                                        -d '{"input": "круг красный", "model": "bge-m3"}'
    figures = [
        "круг",
        "10угольник",
        "9угольник",
        "8угольник",
        "7угольник",
        "6угольник",
        "5угольник",
        "квадрат",
        "треугольник",
    ]
    colours = ["красный", "оранжевый", "желтый", "зеленый", "голубой", "синий", "фиолетовый"]

    texts = [f"{f} {c}" for f in figures for c in colours]
    metadata = [{"figure": f, "colour": c} for f in figures for c in colours]

    all_vectors = get_embeddings(texts)

    # 2. Собираем JS-документы в текстовом формате, чтоб избежать ошибки argument too long в mongo.sh
    js_documents = []
    for meta, vec in zip(metadata, all_vectors):
        doc_str = f"""{{
            "figure": "{meta['figure']}",
            "colour": "{meta['colour']}",
            "vector_figure": {vec}
        }}"""
        js_documents.append(doc_str)

    # Формируем итоговый JS-скрипт для mongosh
    bulk_array_str = "[\n" + ",\n".join(js_documents) + "\n]"
    js_script = f"db.testColl.drop();\ndb.testColl.insertMany({bulk_array_str});\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(js_script)
        temp_file_path = f.name

    try:
        print(f"Загружаю {len(js_documents)} документов через файл {temp_file_path}...")
        coa(f"load('{temp_file_path}')")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    print(f"Вставка успешно завершена без переполнения аргументов командной строки!")
    time.sleep(3)

    index_config = {
        "fields": [
            {
                "type": "vector",
                "path": "vector_figure",
                "numDimensions": 1024,
                "similarity": "dotProduct",
                "quantization": "scalar",
            }
        ]
    }
    coa(f'db.testColl.createSearchIndex("simple_index", "vectorSearch", {index_config})')

    # Даем локальному поисковому движку Lucene время считать 63 документа
    time.sleep(3)

    # 5. Запрос векторного поиска
    query_vector = get_embeddings("9угольник красный")

    pipeline = [
        {
            "$vectorSearch": {
                "index": "simple_index",
                "path": "vector_figure",
                "queryVector": query_vector,
                "numCandidates": 63,
                "limit": 2,
            }
        },
        {
            "$project": {
                "_id": 0,
                "figure": 1,
                "colour": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    output = coa(f"db.testColl.aggregate({pipeline}).toArray()")
    results = json.loads(output)
    assert len(results) > 0, "Поиск вернул пустой массив документов"
    assert results[0]["figure"] == "9угольник"
    assert results[0]["colour"] == "красный"

    query_vector = get_embeddings("фигура цвета неба")

    pipeline = [
        {
            "$vectorSearch": {
                "index": "simple_index",
                "path": "vector_figure",
                "queryVector": query_vector,
                "numCandidates": 63,
                "limit": 2,
            }
        },
        {
            "$project": {
                "_id": 0,
                "figure": 1,
                "colour": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    output = coa(f"db.testColl.aggregate({pipeline}).toArray()")
    results = json.loads(output)
    assert len(results) > 0, "Поиск вернул пустой массив документов"
    assert results[0]["colour"] == "голубой"
    assert results[1]["colour"] == "голубой"
