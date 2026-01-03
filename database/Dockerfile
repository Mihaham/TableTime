FROM postgres:15-alpine

# Копируем скрипт инициализации
COPY init-user-db.sh /docker-entrypoint-initdb.d/init-user-db.sh

# Даем права на выполнение скрипта
RUN chmod +x /docker-entrypoint-initdb.d/init-user-db.sh
