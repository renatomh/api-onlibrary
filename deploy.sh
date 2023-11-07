#!/bin/sh

# Example shell script to deploy updated apps on Unix machines
# App must already be setup locally, according to the README instructions

# The script can be executed with the command 'bash deploy.sh'

# Defining app name and path
APP_SERVICE_NAME="api-onlibrary" # TODO: update for specific service name
APP_PATH="/home/user/systems/api-onlibrary" # TODO: update for specific paths

# Using the correct app directory
cd $APP_PATH

# Storing git credentials (required for the first time we access the remote repository)
git config credential.helper store
# Setting git directory as safe
git config --global --add safe.directory $APP_PATH

# Getting last version from repository
git pull

# Activating the virtual environemnt
source ./env/bin/activate
# Compiling new translations
pybabel compile -d app/translations
# Upgrading migrations for the database schema
make migrateup
# Deactivating the virtual environemnt
deactivate

# Restarting the service
echo "Stopping $APP_SERVICE_NAME service..."
service $APP_SERVICE_NAME stop
sleep 5 # Waiting for 5 seconds
echo "Starting $APP_SERVICE_NAME service..."
service $APP_SERVICE_NAME start
