#!/bin/bash
flake8 engfrosh_site/ --count --show-source --statistics --max-line-length=120 --exclude "*/migrations/*"
