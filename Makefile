# Including environment variables to the makefile
include .env

# This command installs Docker in a Linux Ubuntu machine
install-docker:
	sudo apt update
	sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
	echo "deb [signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
	sudo apt update
	sudo apt install -y docker-ce
	sudo systemctl start docker
	sudo systemctl enable docker
	docker --version

# This command will create a MySQL container
mysql:
	docker run --name mysql-onlibrary -p 3306:3306 -e MYSQL_ROOT_PASSWORD=${SQL_PASS} -e MYSQL_DATABASE=${SQL_DB} -v sql-data:/var/lib/mysql -d mysql:8.0.32-debian

# This command will create a PostgreSQL container
postgresql:
	docker run --name postgres-onlibrary -p 5432:5432 -e POSTGRES_USER=${SQL_USER} -e POSTGRES_PASSWORD=${SQL_PASS} -e POSTGRES_DB=${SQL_DB} -v pgdata:/var/lib/postgresql/data -d postgres:15-alpine

# This command will populate the database on the composed container's database
populatedb:
	docker cp ./default-data.sql api-onlibrary-db-1:/home/default-data.sql
	docker exec -it api-onlibrary-db-1 /bin/sh -c 'mysql -u ${SQL_USER} -p${SQL_PASS} ${SQL_DB} < /home/default-data.sql'

# This command will copy the required environment files to the application composed container
copyenv:
	docker cp ./.env api-onlibrary-api-1:/app/.env
	docker cp ./service-credentials.json api-onlibrary-api-1:/app/service-credentials.json

# This command will extract texts to be translated and translate them
translate:
	pybabel extract -F babel.cfg -k _l -o messages.pot .
	pybabel update -i messages.pot -d app/translations -l es
	pybabel update -i messages.pot -d app/translations -l pt
	python translate_texts.py
	pybabel compile -d app/translations

# This command will test the app, setting up deprecation warnings and logging options
test:
	pytest -W ignore::DeprecationWarning -v -p no:logging

# This command will test the app and generate a HTML coverage report
test-cov:
	coverage run -m pytest -W ignore::DeprecationWarning -v -p no:logging
	coverage html

# This command will run the required migrations up for the database
migrateup:
	alembic upgrade head

# This command will downgrade all migrations on the database
migratedown:
	alembic downgrade base

# This command starts the application
start:
	python run.py

.PHONY: install-docker mysql postgresql populatedb copyenv translate test test-cov migrateup migratedown start
