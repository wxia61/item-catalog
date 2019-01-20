[![Build Status](https://travis-ci.com/wxia61/item-catalog.svg?branch=master)](https://travis-ci.com/wxia61/item-catalog)

# item-catalog
An application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

# setup

1. $ `sudo -u postgres psql`

2. psql=# `alter user vagrant with encrypted password '123';`

3. postgres=# `\q`

4. $ `sudo -u vagrant  psql`

5. vagrant=> `CREATE DATABASE catalog;`

6. vagrant=> `\q`

7. $ `python database_setup.py`

8. $ `python app.py`

Open broswer and go to http://localhost:5000

