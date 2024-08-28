#!/bin/bash
flake8 engfrosh_site/ lambda_function.py qrcode_gen.py --count --show-source --statistics --max-line-length=120 --exclude "*/migrations/*"
