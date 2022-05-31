#!/usr/env/bin bash

pyinstaller --exclude-module pyinstaller --onefile --clean -y autoitincludeviz.py
