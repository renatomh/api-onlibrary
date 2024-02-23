<h1 align="center"><img alt="OnLibrary" title="OnLibrary" src=".github/logo.png" width="250" /></h1>

# OnLibrary

## 💡 Project's Idea

This project was developed to create an online library platform for customers.

## 🔍 Features

* Login and signup to the application;
* Update user's profile;
* Multilanguage support;
* Different timezones support;
* Files thumbnails creation;

## 💹 Extras

* API pagination for better performance;

## 🛠 Technologies

During the development of this project, the following techologies were used:

- [Python](https://www.python.org/)
- [Flask](https://flask.palletsprojects.com/en/2.0.x/)
- [Alembic (Migrations)](https://alembic.sqlalchemy.org/en/latest/)
- [Flasgger (Swagger Documentation)](https://github.com/flasgger/flasgger)
- [SQLAlchemy (ORM)](https://www.sqlalchemy.org/)
- [Flask-Babel](https://flask-babel.tkte.ch/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/index.html)
- [Firebase Cloud Messaging (Push Notifications)](https://firebase.google.com/docs/cloud-messaging)
- [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/)
- [Gunicorn](https://gunicorn.org/)
- [Black Formatter](https://github.com/psf/black)
- [Let's Encrypt](https://letsencrypt.org/pt-br/)
- [FFmpeg](https://ffmpeg.org/)
- [Docker](https://www.docker.com/)
- [Sentry - Application Performance Monitoring & Error Tracking](https://sentry.io/welcome/)
- [Terraform](https://www.terraform.io/)
- [GitHub Actions (CI/CD)](https://github.com/features/actions)

## 💻 Project Configuration

### First, create a new virtual environment on the root directory

```bash
$ python -m venv env
```

### Activate the created virtual environment

```bash
$ .\env\Scripts\activate # On Windows machines
$ source ./env/bin/activate # On MacOS/Unix machines
```

### Install the required packages/libs

```bash
(env) $ pip install -r requirements.txt
```

### Internationalization (i18n) and Localization (l10n)

In order to provide results according to the specified languages set in the request headers ([*Accept-Language*](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Headers/Accept-Language)), we make use of [Flask-Babel](https://flask-babel.tkte.ch/). Here are a few commands for its use:

```bash
(env) $ pybabel extract -F babel.cfg -k _l -o messages.pot . # Gets list of texts to be translated
(env) $ pybabel init -i messages.pot -d app/translations -l pt # Creates file (messages.po) with 'pt' translations (replace 'pt' with required language code)
(env) $ pybabel update -i messages.pot -d app/translations -l pt # Updates file (messages.po) with 'pt' translations (replace 'pt' with required language code)
(env) $ python translate_texts.py # Optional: auto translate the entries from the '.po' translation files
(env) $ pybabel compile -d app/translations # Compiles the translation files
```

It's important to compile the translation files before running the application, should it provide the correct translations for the system users.

## 🌐 Setting up config files

Create an *.env* file on the root directory, with all needed variables, credentials and API keys, according to the sample provided (*.env.example*).

### Microsoft SQL Server

When using the Microsoft SQL Server, it is also required to [download and install the ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver15). Otherwise, it won`t be possible to connect with the SQL server.

Also, in order to install *pyodbc* on Linux, it might be necessary to install *unixodbc-dev* with the command below:

```bash
$ sudo apt-get install unixodbc-dev
```

**Note**: some Docker images have troubles when installing this dependency. Hence, we're avoiding to use SQL Server when deploying the application with Docker.

### MySQL Server

When using the MySQL Server, it is required to choose a default charset which won't conflict with some models fields data length. The 'utf8/utf8_general_ci' should work.

### FFmpeg

In order to be able to create thumbnail images for video files, the [FFmpeg](https://ffmpeg.org/) must be installed on the machine. Also, the *path* to the FFmpeg executable file must be set on the *.env* file.

### Firebase Cloud Messaging

In order to be able to send *push notifications* to mobile applications, currently the [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging) solution it's being used. Aside from setting the *.env* file, you must also have your service account JSON credentials file present on the app's root folder.

### Time Zones

Since the application allows working with different time zones, it might be interesting to use the same time zone as the machine where the application is running when defining the *TZ* variable on the *.env* file, since internal database functions (which are used for creating columns like *created_at* and *updated_at*) usually make use of the system's time zone (when not set manually).

Also, on server's migration, the database backup could be coming from a machine with a different time zone definition. In this case, it might be necessary to convert the datetime records to the new machine time zone, or set the new machine time zone to the same as the previous machine.

### Black Formatter

The project uses the [Black Python code formatter](https://github.com/psf/black), provided by the Black Formatter VS Code extension (**ms-python.black-formatter**). It's a good practice to install it on your VS Code environment, so the code formatting will be consistent.

## ⏱ Setting up services

In order to execute tasks, jobs, scripts and others periodically, we can set up services in the computer where the application should be running.
* On Unix machines, we can use [Crontab](https://ostechnix.com/a-beginners-guide-to-cron-jobs/);
* On Windows machines, we can use [Task Scheduler](https://www.windowscentral.com/how-create-automated-task-using-task-scheduler-windows-10);

The sample crontab configuration provided (*crontab-script example*) shows how to set tasks to be executed at the specified dates and times on a Unix machine, using *crontab*.

These must be set in order to run the *jobs* created for the application (from the folder *app/jobs*).

## 💾 Database Migrations

Once the SQL server is ready (MySQL, PostgreSQL, etc.) and the required credentials to access it are present in the *.env* file, you can run the migrations with the command:

```bash
(env) $ alembic upgrade head
```

You can also downgrade the migrations with the following command:

```bash
(env) $ alembic downgrade base
```

Alternatively, you can migrate up or down by a specific number of revision, or to a specific revision:

```bash
(env) $ alembic upgrade +2 # Migrating up 2 revisions
(env) $ alembic downgrade -1 # Migrating down 1 revision
(env) $ alembic upgrade db9257fac0e2 # Migrating to a specific revision
```

When there are changes to the application models, new revisions for the migrations can be generated with the command below (where you can provide a custom short description for the update):

```bash
(env) $ alembic revision --autogenerate -m "revision description"
```

## ⏯️ Running

To run the project in a development environment, execute the following command on the root directory, with the virtual environment activated.

```bash
(env) $ python run.py
```

In order to leave the virtual environment, you can simply execute the command below:

```bash
(env) $ deactivate
```

## 🔨 *Production* Server

In order to execute the project in a production server, you must make use of a *Web Server Gateway Interface* (WSGI), such as [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) for Linux or [waitress](https://docs.pylonsproject.org/projects/waitress/en/latest/) for Windows.

### 💻 Windows
In Windows, you could run the *wsgi.py* file, like so:

```bash
(env) $ python wsgi.py
```

After that, a Windows Task can be created to restart the application, activating the virtual environment and calling the script, whenever the machine is booted.

### ⌨ Linux
In Linux systems, you can use the following command to check if the server is working, changing the port number to the one you're using in the app:

```bash
(env) $ gunicorn --worker-class eventlet --bind 0.0.0.0:8080 wsgi:app --reload
```

The *api-onlibrary.service* file must be updated and placed in the '/etc/systemd/system/' directory. After that, you should execute the following commands to enable and start the service:

```bash
$ sudo systemctl daemon-reload
$ sudo systemctl enable api-onlibrary
$ sudo systemctl start api-onlibrary
$ sudo systemctl status api-onlibrary
```

In order to serve the application with Nginx, it can be configured like so (adjusting the paths, server name, etc.):

```
# Flask Server
server {
    listen 80;
    server_name api.domain.com.br;

    location / {
        include proxy_params;
        proxy_pass http://localhost:8080;
        client_max_body_size 16M;
    }

    location /socket.io {
        include proxy_params;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_pass http://localhost:8080/socket.io;
    }
}
```

#### 📜 SSL/TLS

You can also add security with SSL/TLS layer used for HTTPS protocol. One option is to use the free *Let's Encrypt* certificates.

For this, you must [install the *Certbot*'s package](https://certbot.eff.org/instructions) and use its *plugin*, with the following commands (also, adjusting the srver name):

```bash
$ sudo apt install snapd # Installs snapd
$ sudo snap install core; sudo snap refresh core # Ensures snapd version is up to date
$ sudo snap install --classic certbot # Installs Certbot
$ sudo ln -s /snap/bin/certbot /usr/bin/certbot # Prepares the Certbot command
$ sudo certbot --nginx -d api.domain.com.br
```

## 🐳 Docker

There's also the option to deploy the application using [Docker](https://www.docker.com/). In this case, we have a *Dockerfile* for the Flask Application.

If you want to deploy the application with an already existing database, you just need the Flask Dockerfile, otherwise, you can use the *docker-compose* to deploy the application as well as the database server on your machine.

To build a container image for the Flask application, we can run the following command on the app's root folder:

```bash
$ docker build -t api-onlibrary .
```

A few useful Docker commands are listed below:

```bash
$ docker image ls # Shows available images
$ docker ps --all # Shows available containers
$ docker run --name <container-name> -p 8080:8080 -it <image-name> # Runs a container from an image with specified options
$ docker exec -it <container> bash # Access the Docker container's shell
```

After starting the container, you should add the environment and credentials files to it, in order for it to work correctly. You can do it with the following commands:

```bash
$ docker cp ./.env <container>:/app/.env
$ docker cp ./service-credentials.json <container>:/app/service-credentials.json
```

If you want to create containers for both the Flask Application and the database server, you can use the following command for the Docker Composer:

```bash
$ docker compose up
```

This will first try to pull existing images to create the containers. If they're not available, it'll build the images and then run the conatainers.

Finally, a [Makefile](./Makefile) was created in order to help providing some of the commands listed above in a simple way.

## 🧪 Testing

In order to make sure that the application's main features are working as expected, some tests were created to assert the functionalities.

To allow the execution of the tests, first the required dependencies must be installed:

```bash
(env) $ pip install -r requirements-test.txt
```

The tests can then be run:

```bash
(env) $ pytest # Optionally, you can add options like '-W ignore::DeprecationWarning' to suppress specific warnings or '-o log_cli=true' to show logs outputs
```

Also, you can generate HTML test coverage reports with the commands below:

```bash
(env) $ coverage run -m pytest
(env) $ coverage html
```

## 🏗️ Infrastructure as Code (IaC) with Terraform

To make it easier to provision infrastructure on cloud providers, you can make use of the [Terraform template](main.tf) provided.

First, you'll need to [install Terraform](https://developer.hashicorp.com/terraform/downloads) on your machine; then, since we're using AWS for the specified resources, you'll need to install the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) as well.

After that, you must set up an IAM user with permissions to manage resources, create an access key for the new user and configure the AWS CLI with the following command (entering the access key ID, secret access key, default region and outout format):

```bash
$ aws configure
```

Once these steps are done, you can use the Terraform commands to create, update and delete resources.

```bash
$ terraform init # Downloads the necessary provider plugins and set up the working directory
$ terraform plan # Creates the execution plan for the resources
$ terraform apply # Executes the actions proposed in a Terraform plan
$ terraform destroy # Destroys all remote objects managed by a particular Terraform configuration
```

If you want to provide the required variables for Terraform automatically when executing the script, you can create a file called *prod.auto.tfvars* file on the root directory, with all needed variables, according to the sample provided ([auto.tfvars](auto.tfvars)).

### Documentation:
* [Como servir os aplicativos Flask com o Gunicorn e o Nginx no Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04-pt)
* [Como servir aplicativos Flask com o uWSGI e o Nginx no Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04-pt)
* [How to host multiple flask apps under a single domain hosted on nginx?](https://stackoverflow.com/questions/34692600/how-to-host-multiple-flask-apps-under-a-single-domain-hosted-on-nginx)
* [Deploying Flask on Windows](https://towardsdatascience.com/deploying-flask-on-windows-b2839d8148fa)
* [Deploy de aplicativo Python / Flask no windows](https://www.tecnasistemas.com.br/hc/pt-br/articles/360041410791-Deploy-de-aplicativo-Python-Flask-no-windows)
* [How to serve static files in Flask](https://stackoverflow.com/questions/20646822/how-to-serve-static-files-in-flask)
* [Get list of all routes defined in the Flask app](https://stackoverflow.com/questions/13317536/get-list-of-all-routes-defined-in-the-flask-app)
* [Switching from SQLite to MySQL with Flask SQLAlchemy](https://stackoverflow.com/questions/27766794/switching-from-sqlite-to-mysql-with-flask-sqlalchemy)
* [Token-Based Authentication With Flask](https://realpython.com/token-based-authentication-with-flask/#user-status-route)
* [Define Relationships Between SQLAlchemy Data Models](https://hackersandslackers.com/sqlalchemy-data-models/)
* [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
* [Uploading Files](https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/)
* [Python - Flask - Working with middleware for specific route](https://www.youtube.com/watch?v=kJSl7pWeOfU)
* [Como Instalar o Python 3 e Configurar um Ambiente de Programação no Ubuntu 18.04 [Quickstart]](https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment-on-ubuntu-18-04-quickstart-pt)
* [What is the meaning of "Failed building wheel for X" in pip install?](https://stackoverflow.com/questions/53204916/what-is-the-meaning-of-failed-building-wheel-for-x-in-pip-install)
* [Install Certbot on ubuntu 20.04](https://askubuntu.com/questions/1278936/install-certbot-on-ubuntu-20-04)
* [The Flask Mega-Tutorial Part XIII: I18n and L10n](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiii-i18n-and-l10n)
* [Flask Babel - 'translations/de/LC_MESSAGES/messages.po' is marked as fuzzy, skipping](https://stackoverflow.com/questions/12555692/flask-babel-translations-de-lc-messages-messages-po-is-marked-as-fuzzy-skip)
* [List of tz database time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
* [How to translate text with python](https://medium.com/analytics-vidhya/how-to-translate-text-with-python-9d203139dcf5)
* [deep-translator - PyPI](https://deep-translator.readthedocs.io/en/latest/)
* [How to Install FFmpeg on Windows, Mac, Linux Ubuntu and Debian](https://www.videoproc.com/resource/how-to-install-ffmpeg.htm)
* [Using PYTHONPATH](https://bic-berkeley.github.io/psych-214-fall-2016/using_pythonpath.html)
* [How do you set your pythonpath in an already-created virtualenv?](https://stackoverflow.com/questions/4757178/how-do-you-set-your-pythonpath-in-an-already-created-virtualenv)
* [cannot import local module inside virtual environment from subfolder](https://stackoverflow.com/questions/58642026/cannot-import-local-module-inside-virtual-environment-from-subfolder)
* [Socket.IO](https://socket.io/pt-br/)
* [Gunicorn ImportError: cannot import name 'ALREADY_HANDLED' from 'eventlet.wsgi' in docker](https://stackoverflow.com/questions/67409452/gunicorn-importerror-cannot-import-name-already-handled-from-eventlet-wsgi)
* [Error when running Flask application with web sockets and Gunicorn](https://stackoverflow.com/questions/56532961/error-when-running-flask-application-with-web-sockets-and-gunicorn)
* [eventlet worker: ALREADY_HANDLED -> WSGI_LOCAL #2581](https://github.com/benoitc/gunicorn/pull/2581)
* [polling-xhr.js:157 Error 502 Bad Gateway While trying to establish connection between the client and the server using SocketIO #1804](https://github.com/miguelgrinberg/Flask-SocketIO/discussions/1804)
* [Python - Flask-SocketIO send message from thread: not always working](https://stackoverflow.com/a/49411246)
* [Firebase Admin Python SDK](https://firebase.google.com/docs/reference/admin/python/)
* [Firebase cloud messaging and python 3](https://blog.iampato.me/firebase-cloud-messaging-and-python-3)
* [From inside of a Docker container, how do I connect to the localhost of the machine?](https://stackoverflow.com/questions/24319662/from-inside-of-a-docker-container-how-do-i-connect-to-the-localhost-of-the-mach)
* [Dockerizing Flask with Postgres, Gunicorn, and Nginx](https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/)
* [docker-flask-uwsgi-nginx-simple](https://github.com/Julian-Nash/docker-flask-uwsgi-nginx-simple)
* [Install matplotlib In A Docker Container](https://earthly.dev/blog/python-matplotlib-docker/)
* [A complete guide to using environment variables and files with Docker and Compose](https://towardsdatascience.com/a-complete-guide-to-using-environment-variables-and-files-with-docker-and-compose-4549c21dc6af)
* [How to Create a MySql Instance with Docker Compose](https://medium.com/@chrischuck35/how-to-create-a-mysql-instance-with-docker-compose-1598f3cc1bee)
* [How to run a makefile in Windows?](https://stackoverflow.com/questions/2532234/how-to-run-a-makefile-in-windows)
* [How to get a shell environment variable in a makefile?](https://stackoverflow.com/questions/28890634/how-to-get-a-shell-environment-variable-in-a-makefile)
* [Tutorial — Alembic 1.12.0 documentation](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
* [Flask | Sentry Documentation](https://docs.sentry.io/platforms/python/guides/flask/)
* [ChatGPT | Terraform AWS Usage](https://chat.openai.com/share/c6aee35c-e817-4d30-9bab-885e116153e1)

## 📄 License

This project is under the **MIT** license. For more information, access [LICENSE](./LICENSE).
