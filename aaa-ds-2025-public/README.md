# aaa-distributed-systems

## Требования

- Python 3.12

## Настройка окружения

`make init`

## Форматирование кода

`make format`

## Как прогнать тесты локально

- Необходимо установить act
[Инструкция для Windows, Linux и MacOS](https://nektosact.com/installation/index.html)
- Выполнить `make test`

## Задачи

### Надёжная связь в распределённой системе
В рамках этой задачи мы эмулируем ненадёжную связь между клиентом и сервером.

Ваша задача таким образом модифицировать код в функции `do_reliable_request`, чтобы, каждый из 
вызовов этой функции в рамках тестов (не стесняйтесь туда подсмотреть!) закончился успешно.

Если вы забыли как это можно сделать - пересмотрите первую часть лекции. 

Ссылки-подсказки:
https://www.python-httpx.org/advanced/timeouts/#setting-and-disabling-timeouts


### Поиск дубликатов объявлений
Мы должны написать клиент для работы с PostgreSQL, помогающий
при подаче объявления понимать, подавал ли ранее заданный пользователь объявление с такими
заголовком и описанием.

Для этого необходимо написать 3 SQL-запроса в файле `pg_task.py`:
- Создание таблицы, куда мы будем сохранять исторические данные - `create_tables_structure`
- Сохранение объявлений в эту таблицу - `save items`
- Поиск объявлений в этой таблице - `find_similar_items`

Ссылки-подсказки:
https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.execute
https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.executemany
https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.fetch

Так же можно пересмотреть часть лекции про БД.

### Поиск пользователей, имеющих объявление с заданным заголовком
Необходимо написать клиент для работы с Redis, позволяющий быстро находить
всех пользователей, имеющих объявления с заданным заголовком.

Хранить необходимо только уникальные uid, чтобы не тратить место впустую - Redis хранит все данные в оперативной памяти!

Для этого необходимо реализовать 2 метода в файле `redis_task.py`:
- `save_item` для сохранения очередной записи
- `find_users_by_title` для получения накопленной информации по заголовку

Ссылки-подсказки:
https://redis.io/commands/sadd/
https://redis.io/commands/smembers/

Так же можно пересмотреть часть лекции про KV-storage.