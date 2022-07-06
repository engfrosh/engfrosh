# Steps for setting everything up for Actual Frosh

1. Setup the website as specified in [Deployment](Deployment.md)
2. Add the site groups and Frosh Roles for Heads, Planning, Frosh, Facils
2. Manage Teams, create all the teams
    - Add colors to all the teams
    - Then create discord roles for all the teams
3. Add Users, either manually or using a spreadsheet



## Postgres

```sql
CREATE DATABASE engfrosh_prod;
```

```sql
GRANT ALL ON DATABASE engfrosh_prod TO engfrosh;
```

```sql
GRANT ALL ON ALL TABLES IN SCHEMA public TO engfrosh;
```

```ps1
$ python manage.py createsuperuser
```