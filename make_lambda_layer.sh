#!/bin/bash

mkdir ./python &&\
poetry export --format requirements.txt --output ./python/requirements.txt &&\
cd ./python/ &&\
pip install -r requirements.txt -t . &&\
cd ../ &&\
zip -r discord-reminder-bot-layer.zip ./python/ &&\
rm -r ./python/