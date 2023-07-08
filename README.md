# Kindertic crawler

Very simple crawler to archive my kid memories. The kindergarten my kid used to go used this platform called Kindertic. They would share pictures on every special ocasion, like birthdays, celebrations or after any quarter.
This script download all those assets (images and descriptions of every event). Available events are not self discovered, but hardcored (do your part and send a PR!). SOme extra clean methods have been applied in order to generate coherent event names.

## How to execute it

Create a `.env` file setting some contants:

```bash
KT_USER={provided_username}
KT_PASSWD={provided_password}
```

Then simply create a virtualenv, install dependencies and execute the script:

```bash
$ mkvirtualenv -p 3.11 kindertic-crawler
$ pip install -r requeriments.txt
$ python crawl.py
```

All assets will be downloaded in a nice folder structure under `output/`. That is all.
