# Including environment variables to the makefile
include .env

# This command will populate the database on the container's database
populatedb:
	docker cp ./default-data.sql api-onlibrary-db-1:/home/default-data.sql
	docker exec -it api-onlibrary-db-1 /bin/sh -c 'mysql -u ${SQL_USER} -p${SQL_PASS} ${SQL_DB} < /home/default-data.sql'

# This command will copy the required environment files to the application container
copyenv:
	docker cp ./.env api-onlibrary-api-1:/app/.env
	docker cp ./service-credentials.json api-onlibrary-api-1:/app/service-credentials.json

# This command will extract texts to be translated and translate them
translate:
	pybabel extract -F babel.cfg -k _l -o messages.pot .
	pybabel update -i messages.pot -d app/translations -l de
	pybabel update -i messages.pot -d app/translations -l es
	pybabel update -i messages.pot -d app/translations -l fr
	pybabel update -i messages.pot -d app/translations -l pt
	python translate_texts.py
	pybabel compile -d app/translations

.PHONY: populatedb copyenv translate
