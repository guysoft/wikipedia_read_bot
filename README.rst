Wikipedia Read Bot
==================

A telegram bot that lets you search wikipedia articles.


How to use it?
--------------

No running instance at the moment

Features
--------

* Look up articles
* Disambiguation support

Developing
----------

Requirements
~~~~~~~~~~~~

#. Python 3

Install
~~~~~~~

Run the following::

    git clone https://github.com/guysoft/wikipedia_read_bot.git
    cd wikipedia_read_bot
    sudo pip3 install requirements.txt
    cd src
    cp config.ini.example config.ini
    
    
Put your bot token ``config.ini``. Then run::

    python3 wikipedia_read_bot/src/wikipedia_read_bot.py

4. Message ``/start`` to your bot to start.
    

Set up service on startup
-------------------------
Run ``src/add_startup_service.sh`` either as the user you want the service to be run as, or ``src/add_startup_service.sh <user to run script>``


Code contributions are loved!
