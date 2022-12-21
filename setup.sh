#! /usr/bin/bash


apt update
apt upgrade -y

apt install -y postgresql postgresql-contrib nginx python3-pip gunicorn certbot python3-certbot-nginx

cd /home/ubuntu/engfrosh
git submodule init
git submodule update
pip install -r requirements.txt
