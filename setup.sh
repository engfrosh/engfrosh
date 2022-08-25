#! /bin/bash

cd ~/engfrosh
git submodule init
git submodule update
pip install -r requirements.txt

cd ~/

apt update
apt upgrade -y

apt install postgresql postgresql-contrib nginx python3-pip gunicorn certbot python3-certbot-nginx

