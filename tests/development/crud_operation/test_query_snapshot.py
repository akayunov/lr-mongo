import json
import subprocess
from unittest.mock import ANY


def test_basic(mongo_url):
    cmd = """
    db.testColl.insertMany([
        {
            insertNumber: 100500,
            timestamp: new Date(),
            status: "active"
        }
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    cycle_cmd = """
        print("Скрипт запущен. Будет выполнено ровно 10 вставок.");
        
        // Цикл выполнится от 0 до 9 (всего 10 раз)
        for (let i = 0; i < 10; i++) {
          // Делаем паузу в 1 секунду между вставками (кроме последней)
          if (i < 9) {
            sleep(1000);
          }
          try {
            // Вставляем документ напрямую в коллекцию текущей базы данных
            db.testColl.insertOne({
              insertNumber: i + 1, // Номер вставки от 1 до 10
              timestamp: new Date(),
              status: "active"
            });
            
            print(`[${new Date().toLocaleTimeString()}] Вставка ${i + 1}/10 успешна.`);
          } catch (error) {
            print(`Ошибка на шаге ${i + 1}: ${error.message}`);
          }
        }
        print("Скрипт успешно завершил работу.");
    """

    get_cmd = """sleep(11000);db.testColl.find({}).toArray()"""

    # WITHOUT SNAPSHOT
    get_process = subprocess.Popen(
        ["mongosh", mongo_url, "--json=relaxed", "--eval", get_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    cycle_process = subprocess.Popen(
        ["mongosh", mongo_url, "--json", "--eval", cycle_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output2_without_snapshot, stderr_data2 = get_process.communicate()
    output1, stderr_data1 = cycle_process.communicate()
    assert len(json.loads(output2_without_snapshot)) == 11

    # cleanup
    cmd = """db.testColl.drop()"""
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])
    cmd = """
    db.testColl.insertMany([
        {
            insertNumber: 500100,
            timestamp: new Date(),
            status: "active"
        }
    ])
    """
    subprocess.check_call(["mongosh", mongo_url, "--json", "--eval", cmd])

    get_cmd = """
        // Задаем имя коллекции
        const collectionName = "testColl";
        
        //print("Инициализация snapshot-сессии...");
        
        // 1. Создаем сессию с включенным snapshot
        const session = db.getMongo().startSession({ snapshot: true });
        
        try {
          // Получаем доступ к базе и коллекции через объект сессии
          const sessionDb = session.getDatabase(db.getName());
          const collection = sessionDb.getCollection(collectionName);
        
          // Важно: первый «пустой» или проверочный запрос для фиксации ClusterTime снимка.
          // Без первого обращения snapshot зафиксируется только после sleep, что сломает логику теста.
          collection.distinct("_id"); 
          //print(`[${new Date().toLocaleTimeString()}] Снимок зафиксирован. Засыпаем на 5 секунд...`);
        
          // 2. Ждем 10 секунд (пока в фоне могут идти вставки)
          sleep(10000);
        
          // 3. Получаем документы из зафиксированного 5 секунд назад снимка
          //print(`[${new Date().toLocaleTimeString()}] Проснулись. Выполняем чтение из снимка:`);
          
          const documents = collection.find({}).toArray();
          
          // Выводим результат в формате JSON строки (необходимо для корректного перехвата в subprocess)
          print(JSON.stringify(documents));
        
        } catch (error) {
          //print("Ошибка в процессе работы snapshot-сессии:", error.message);
        } finally {
          // 4. Обязательно закрываем сессию, освобождая ресурсы движка WiredTiger
          session.endSession();
          //print("Сессия закрыта.");
        }
    """

    # WITH SNAPSHOT
    get_process = subprocess.Popen(
        ["mongosh", mongo_url, "--json=relaxed", "--eval", get_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    cycle_process = subprocess.Popen(
        ["mongosh", mongo_url, "--json", "--eval", cycle_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output2_with_snapshot, stderr_data2 = get_process.communicate()
    output1, stderr_data1 = cycle_process.communicate()
    assert json.loads(output2_with_snapshot) == [
        {
            "_id": ANY,
            "insertNumber": 500100,
            "status": "active",
            "timestamp": ANY,
        }
    ]
