#!/bin/bash

set -e

# Функция для сборки контейнеров
build() {
    echo "Сборка контейнеров..."
    docker compose -f docker-compose.yml build
}

# Функция для старта контейнеров
start() {
    echo "Запуск контейнеров..."
    docker compose -f docker-compose.yml up -d
    # Автоматический вызов инициализации для удобства
    initrs
}

# Функция для инициализации репликасета и создания пользователя
initrs() {
    echo "Ожидание запуска процесса MongoDB в контейнере..."
    set +e
    until docker compose exec mongo-primary env HOME=/tmp mongosh --quiet --eval "db.ping" 2>/dev/null; do
        echo "База данных еще не отвечает, ждем 1 секунду..."
        sleep 1
    done
    set -e

    echo "Инициализация репликасета..., выставлен приоритет как примари для первой ноды"
    docker compose exec mongo-primary env HOME=/tmp mongosh --eval 'rs.initiate({
      _id: "rs0",
      members: [
        { _id: 0, host: "mongo-primary.mongo.local:27017", priority: 2 },
        { _id: 1, host: "mongo-secondary1.mongo.local:27017", priority: 1 },
        { _id: 2, host: "mongo-secondary2.mongo.local:27017", priority: 1 },
        { _id: 3, host: "mongo-arbiter1.mongo.local:27017", arbiterOnly: true },
        { _id: 4, host: "mongo-arbiter2.mongo.local:27017", arbiterOnly: true }
      ]
    })'

    echo "Ожидание выбора PRIMARY узла..."
    primary=""

    # Цикл будет выполняться, пока переменная primary пустая или равна null
    while [ -z "$primary" ] || [ "$primary" = "null" ]; do
        echo "Мастер еще не выбран, ждем 2 секунды..."
        sleep 2

        # Временно выключаем set -e, чтобы скрипт не упал, если mongosh вернет ошибку во время поднятия базы
        set +e
        primary=$(docker compose exec mongo-primary env HOME=/tmp mongosh --quiet --eval "db.hello().primary" 2>/dev/null | tr -d '"' | tr -d '\r')
        # Возвращаем строгий режим обратно
        set -e
    done

    echo "Мастер успешно выбран! Текущий primary=$primary"
    echo "Создание администратора..."

    # TODO choose host name by replica name
    docker compose exec mongo-primary env HOME=/tmp mongosh mongodb://localhost/admin --eval 'db.createUser({ user: "root", pwd: "privetserver", roles: [ { role: "root", db: "admin" } ] })'

    create_mongot_user
}

create_mongot_user() {
    echo "Инициализация пользователя mongot внутри контейнера..."

    # Запускаем bash внутри контейнера БЕЗ интерактивного режима (-T)
    docker compose exec -T mongo-test bash -c '
        mongosh "$MONGO_URL" --eval '\''
            const adminDb = db.getSiblingDB("admin");

            const userExists = adminDb.getUsers().users.some(u => u.user === "mongot-user");

            if (!userExists) {
                adminDb.createUser({
                    user: "mongot-user",
                    pwd: "mongot-search-password",
                    roles: [{ role: "searchCoordinator", db: "admin" }]
                });
                print("Пользователь mongot-user успешно создан.");
            } else {
                print("Пользователь mongot-user уже существует, пропускаем.");
            }
        '\''
    '
}

# Функция для остановки контейнеров
stop() {
    echo "Остановка и удаление контейнеров..."
    docker compose -f docker-compose.yml down --timeout 0
}

test() {
    docker compose exec -it mongo-test bash --rcfile /venv/bin/activate
}

restore_archive(){
  docker compose exec -it mongo-test  bash -c 'mongorestore --archive=sampledata.archive --uri $MONGO_URL'
}
# Обработка переданного аргумента
case "$1" in
    build)
        build
        ;;
    start)
        start
        ;;
    initrs)
        initrs
        ;;
    stop)
        stop
        ;;
    test)
        test
        ;;
    ra)
        restore_archive
        ;;
    cmtu)
        create_mongot_user
        ;;
    *)
        echo "Использование: $0 {build|start|initrs|stop|cmtu}"
        exit 1
        ;;
esac
