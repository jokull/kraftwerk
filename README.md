Kraftwerk is a Python WSGI deployment and service management tool. The aim is to
make it fast and efficient to manage a number of Python based web sites or
services by formalizing and scripting deployments and site maintenance.

Kraftwerk uses existing tools like SSH, libcloud, Jinja2, YAML and argparse.
Kraftwerk is itself a Python package that installs a command line tool. The
servers only need a root login to perform actions.

Kraftwerk is VCS agnostic. It uses rsync to transfer code. 

Install
=======

    $ pip install git://github.com/jokull/kraftwerk.git@0.1

If you want to hack on Kraftwerk, fork on [GitHub](https://github.com/jokull/kraftwerk):

    $ git clone git@github.com:username/kraftwerk.git && cd kraftwerk
    $ virtualenv --distribute venv
    $ source venv/bin/activate
    $ python setup.py develop

Conventions
===========

Projects
--------

Kraftwerk installs your project requirements on the first deployment based on a
`requirements.txt` file in the root of your project. From there on you will need
to add a `--upgrade-packages` hook to the deploy command if you have new or
newer requirements.

Kraftwerk will look for a Python package of the same name as your project root
directory. You can override the Python package and WSGI path.
 
In addition you will require a `kraftwerk.yaml` configuration file to tell it
about domain names, HTTP redirects and more optional parameters:

    domain: 
      - www.project.com
    aliases:
      - project.com
    services:
      - files
      - postgres
    workers: 1
    wsgi: 'project.wsgi'
    environ:
      DJANGO_SETTINGS_MODULE: 'project.configs.production'

Servers
-------

You should have root SSH login to Kraftwerk servers with a minimal installation.
To install packages and prepare it for Kraftwerk site deployments run:

    kraftwerk setup-node my.server.tld

The server stack it creates is pretty hardcoded. Other server configuration
tools allow you to write recipes for any setup. Kraftwerk aims to serve the
needs of Python web developers. The stack and web routing looks like this:

Servers are configured to run any number of WSGI sites.

### HTTP routing

    NGiNX → uWSGI (one socket per site)
          → /static (for static assets)
          → /uploads (optional; for user generated assets)

[runit](http://smarden.org/runit/) is a UNIXy daemonizer and service management
framework that keeps your sites from crashing and brings them up on server
reboots. Look in `/etc/services` for the site runit scripts.

### Python Environment

Kraftwerk installs some binary compiled packages that are otherwise a pain to
install with pip (NumPy and PIL). It also installs `libmagickwand-dev` so you
can use [Wand](http://dahlia.github.com/wand/index.html) for faster imaging.

### Services

Kraftwerk servers are all equipped with PostgreSQL and Redis. PostgreSQL is
configured per app if the `postgres` service is found in `kraftwerk.yaml`. If
your project requires a writable directory with publicly served files (image
uploads or whatever) include `files`. Kraftwerk will then include a
`UPLOADS_PATH` environment variable to a writable directory.

### Packages

  + curl
  + wget
  + git-core
  + htop
  + unzip
  + zip
  + rsync
  + runit
  + build-essential 
  + nginx
  + postgresql
  + postgresql-server-dev-all
  + redis-server
  + libxml2-dev
  + libevent-dev
  + ncurses-dev
  + python-dev
  + python-lxml
  + python-numpy
  + python-setuptools
  + libmagickwand-dev

Using With AWS
==============

... or other cloud providers

Export your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. Kraftwerk will pick them up and enable `create-node`. 

    $ kraftwerk create-node --size-id t1.micro production

Kraftwerk will offer to write a line in your `/etc/hosts` for convenience. Try logging in. 

    $ ssh root@production

If you can login it's ready to prepare for Kraftwerk deployments.

    $ kraftwerk setup-node test

It'll output the `stdout` and ask some questions. 

Development vs. Stage vs. Production
====================================

The goal of a stage deployment is to mirror "real-world" application conditions
to decrease the chances of fucking up once an application is deployed to a live
server. To this end Kraftwerk provides the plumbing for a convenient and quick
stage test. Secondarily stage deployments are useful for client previews and
internal testing. 

Shortcomings
============

  + No way to declare worker processes or cronjobs
  + No backups configured
  + `sync-services` needs tests

Inspiration
===========

+ This project is very similar to [Silver Lining](http://cloudsilverlining.org/)
+ Heroku
+ [Markdoc](http://markdoc.org/)
