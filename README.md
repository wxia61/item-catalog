[![Build Status](https://travis-ci.com/wxia61/item-catalog.svg?branch=master)](https://travis-ci.com/wxia61/item-catalog)

# item-catalog
An application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

# setup
su vagrant -c 'createdb catalog'
$ sudo -u postgres psql
psql=# alter user vagrant with encrypted password '123';

insert into  category(name) values('catalog2');

insert into  item (name, description, category_id) values('item1', 'description of item1', 1);
