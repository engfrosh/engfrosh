- delete all magic links
- kick all frosh, facils, heads, and some of planning
- backup database

    - Log in as postgres user
    - run `pg_dump engfrosh_production > /usr/share/engfrosh_site/engfrosh_production_dump_yyyy_mm_dd_hh_mm`
    - Copy this file somewhere
        - `scp ubuntu@mars.engfrosh.com:/usr/share/engfrosh_site/engfrosh_production_dump_yyyy_mm_dd_hh_mm`
    - If you need to restore it, create a new database with `CREATE DATABASE engfrosh_production_backup` then run it with `\i path_to_backup_file`

- backup all media
    - `scp -r ubuntu@mars.engfrosh.com:/usr/share/engfrosh_site/files ./backup/`

- add any fixes that aren't in git
    - currently just copying and pasting via vs code

- stop the server
- remove the instance
- delete the ebs volume
- remove any backup images
- release any elastic ips
- check for anything else running or being stored
- release the dns record
