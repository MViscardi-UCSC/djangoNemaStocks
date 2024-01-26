# djangoNemaStocks
## Marcus Viscardi, 2023/2024

This is a project for the Arribere Lab at UC Santa Cruz.
It is a Django web app that will allow the lab to keep
track of our stock of *C. elegans* strains.

# Table of Contents
1. [Installation](#installation)
2. [Notes](#notes)
3. [To Do](#to-do)

# Installation

It would be best to install this project in a virtual environment.
I have just been using Python's built in venv module.
To create a virtual environment, run the following command in the terminal:

```bash
python -m venv ./venv
```

Most importantly is installing the requirements.txt file.
This can be accomplished by running the following command in the terminal:

```bash
pip install -r requirements.txt
```

# Notes

Below I will have a list of some general notes and steps!

So on Jan 26, 2023 I really wanted to make an attempt to have the project be accessible on the local network.
I followed [this guide on Medium](https://medium.com/@huzaifazahoor654/how-to-deploy-django-on-ubuntu-with-nginx-and-gunicorn-9288b2c4e922#id_token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ4YTYzYmM0NzY3Zjg1NTBhNTMyZGM2MzBjZjdlYjQ5ZmYzOTdlN2MiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIyMTYyOTYwMzU4MzQtazFrNnFlMDYwczJ0cDJhMmphbTRsamRjbXMwMHN0dGcuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiIyMTYyOTYwMzU4MzQtazFrNnFlMDYwczJ0cDJhMmphbTRsamRjbXMwMHN0dGcuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDQ0MDUxNjQ5NTY4NzczNDA5MzEiLCJlbWFpbCI6Im1hcmN1cy52aXNjYXJkaUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmJmIjoxNzA2Mjk5NjgwLCJuYW1lIjoiTWFyY3VzIFZpc2NhcmRpIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0t6X3VhM013YzNsbGlqLUFYdXlrbExjLUhnM2U2aHZuU2RfM1RIWlRueENMQUU9czk2LWMiLCJnaXZlbl9uYW1lIjoiTWFyY3VzIiwiZmFtaWx5X25hbWUiOiJWaXNjYXJkaSIsImxvY2FsZSI6ImVuIiwiaWF0IjoxNzA2Mjk5OTgwLCJleHAiOjE3MDYzMDM1ODAsImp0aSI6Ijk0MjkzMzQxYjJiZDhkN2MzNTA2Y2RkODQ4YTkxYTMzYTgzMmUyZDMifQ.ImnPq2T6rQQIcziPEM91PAbvtQZGHLBMAr8UKUD5pFn7f2MyKKX6jzW3rpJBajWVpoeX68Gvd_nNtlsq8pb9iLXzRDUUzyx5SJC1Vwz54V49V3JcxYoAKZ1PERDjuAW-z3D-y1usaIUEKA7JO79ccVCVRJzDxAQ5WhVrQQcJ9LhL40zxZIh7V_TVWoPB03dl_ddgBSygNbviRYonqKt9SCWqHZjSFhC2IURVSRMmtFwRnZ9RemxNiS5hFlGB7NRJbMVxm7UeyOX4oBJqCUYB6ShxjziIo041-6ojvash8aa0xgdiDWoqgMha7Kc8THLa8ZaH5SY-hOOI0sUmGVo0Tg).
Briefly, the guide included the following steps:

```bash
pip3 install gunicorn
sudo apt-get install -y nginx
gunicorn --bind 128.114.150.214:8080 djangoNemaStocks.wsgi:application
sudo apt-get install supervisor -y
```

Then we wrote a supervisor config file for gunicorn:
```bash
sudo nano /etc/supervisor/conf.d/gunicorn.conf
```
With the following contents:
```
[program:gunicorn]

directory=/home/marcus/PycharmProjects/djangoNemaStocks
command=/home/ubuntu/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/my_project/app.sock djangoNemaStocks.wsgi:application
autostart=true
autorestart=true
stderr_logfile=/var/log/gunicorn/gunicorn.err.log
stdout_logfile=/var/log/gunicorn/gunicorn.out.log
[group:guni]
programs:gunicorn
```


The guide continued from there with the following steps:
```bash
sudo mkdir /var/log/gunicorn
sudo supervisorctl update
sudo supervisorctl reread
```

Then we wrote a nginx config file:
```bash
sudo nano /etc/nginx/sites-available/django.conf
```
With the following contents:
```
server{
        server_name ip_address;
        server_name domain_name.com;

        location / {
                include proxy_params;
                proxy_pass http://unix:/home/ubuntu/my_project/app.sock;
        }
        location /static/ {
                autoindex on;
                alias /home/marcus/PycharmProjects/djangoNemaStocks/static/;
        }
        location /media/ {
                autoindex on;
                alias /home/marcus/PycharmProjects/djangoNemaStocks/media/;
        }
}
```

Then we linked the config file to the sites-enabled directory:
```bash
sudo ln -s /etc/nginx/sites-available/django.conf /etc/nginx/sites-enabled
```

Then we checked the nginx config and restarted supervisor and nginx:
```bash
sudo nginx -t
sudo supervisorctl reload && sudo systemctl reload nginx
```
***
But now that we got through all of that, I am not sure if it is working.

Now if I run the following command I have a working website at http://128.114.150.214:8080, which stops when I stop the process:
```bash
gunicorn --bind 128.114.150.214:8080 djangoNemaStocks.wsgi:application
```
But this only seems to be working on TinCan? I have another computer on the local network (via VPN),
which is able to ping TinCan's IP on the command line but is not able to access the website??

# To Do