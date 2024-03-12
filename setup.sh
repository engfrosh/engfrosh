#! /usr/bin/bash


apt update
apt upgrade -y

apt install -y nginx python3-pip gunicorn certbot python3-certbot-nginx

cd /home/ubuntu/engfrosh
git submodule init
git submodule update
pip3 install -r requirements.txt
