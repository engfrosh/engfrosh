# Deploying to AWS

### Deploy an AWS EC2 Server
- Ubuntu 20.04 
    - Tested, others may work
- Tested on t2.micro (free), actual production deployment may require more powerful
- EBS storage, 
    - gp3, 
    - size 10 (for now),
    - Encryption, default key is fine
    - leave the other defaults
- Add a security group with SSH, HTTP, and HTTPS
- Add or create a new key pair


### Once Launched
- Create an elastic ip and assign it
- add ip to dns as a subdomain

#### Update your server
```sh
$ sudo apt update
$ sudo apt upgrade
```


### Install Postgres
```sh
$ sudo apt install postgresql postgresql-contrib nginx python3-pip gunicorn certbot python3-certbot-nginx
```

#### Setup Postgres

##### Accessing Postgres
```sh
$ sudo -i -u postgres
$ psql
```

To exit:
```
# \q
$ exit
```

##### Create Users

```sql
# CREATE USER django_engfrosh WITH PASSWORD '[my password]';
# CREATE USER discord_engfrosh WITH PASSWORD '[my password]';
```

##### Create Database
```sql
# CREATE DATABASE engfrosh WITH OWNER django_engfrosh;
```

### Install Nginx
[source](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04)


You can check the status and also check by going to the web address.
```sh
$ systemctl status nginx
```


#### Management Commands:

Check that it is installed and running by going to the domain you specified earlier, you 
should see a welcome to nginx site.

To stop your web server, type:

```
sudo systemctl stop nginx
```
To start the web server when it is stopped, type:
```
sudo systemctl start nginx
```
To stop and then start the service again, type:
```
sudo systemctl restart nginx
```
If you are only making configuration changes, Nginx can often reload without dropping connections. To do this, type:
```
sudo systemctl reload nginx
```
By default, Nginx is configured to start automatically when the server boots. If this is not what you want, you can disable this behavior by typing:
```
sudo systemctl disable nginx
```
To re-enable the service to start up at boot, you can type:
```
sudo systemctl enable nginx
```

### Clone the repo
Clone main for development or a release for production.

```
git clone https://github.com/engfrosh/engfrosh.git
```

### Install requirements
```
sudo pip install -r requirements.txt
```

Fix any dependancy errors
- psycopg2-binary if there is a compiling error
- install the proper version of requests for django

- create a credentials.py file in authentication.
- change the database password for django

- migrate django database
- create django super user
- run the django server and ideally using vscode or something check that at least some 
pages come up 

Now test gunicorn with django, run `gunicorn engfrosh_site.wsgi` do this from
the folder with manage.py

you can also run it as `gunicorn --bind 0.0.0.0:5000 engfrosh_site.wsgi` which will bind 
a different port to listen on.

#### Create the service
[source](https://www.linkedin.com/pulse/deploying-application-flask-nginx-gunicorn-3-daniela-morales/)

create `/etc/systemd/system/engfrosh_site.service`
and add the following to it:

```
[Unit]
Description=Starts engfrosh site gunicorn server
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/engfrosh/engfrosh_site
ExecStart=gunicorn --workers 3 --bind unix:/home/ubuntu/engfrosh/engfrosh_site/engfrosh_site.sock -m 007 engfrosh_site.wsgi

[Install]
WantedBy=multi-user.target
```

Now run
```
sudo systemctl start engfrosh_site
```
To start now, and
```
sudo systemctl enable engfrosh_site
```
To have it start on boot

# Configure nginx

write to `/etc/nginx/sites-available/alpha.engfrosh.com` the following
```
server {
    listen 80;
    server_name alpha.engfrosh.com, www.alpha.engfrosh.com;
    client_max_body_size 4G;


    location /static/ {
        root /home/ubuntu/engfrosh/files;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        # we don't want nginx trying to do something clever with
        # redirects, we set the Host: header above already.
        proxy_redirect off;
        proxy_pass http://unix:/home/ubuntu/engfrosh/engfrosh_site/engfrosh_site.sock;
    }
}
```

now link the config to enable it
```
sudo ln -s /etc/nginx/sites-available/alpha.engfrosh.com /etc/nginx/sites-enabled
```

test `sudo nginx -t`

restart `sudo systemctl restart nginx`

Your site should now be at least somewhat up.

## Next steps

<!-- Disable example site
```
sudo rm /etc/nginx/sites-enabled/default
``` -->

setup static files. run `manage.py collectstatic` to put the static files into the static 
root, you will have to rerun this whenever files change. 

You also need to watch that the environment puts it in the rigth spot, you maay want to change the static files root for in deployment.
