# Copyright (c) 2025 Nokia All rights reserved.
# Licensed under the BSD 3-Clause License
# SPDX-License-Identifier: BSD-3-Clause

FROM python:3.13

COPY requirements.txt /opt/number-verification-backend-app/
RUN pip install -U -r /opt/number-verification-backend-app/requirements.txt

RUN mkdir -p /home/serveruser/number-verification-backend-app
COPY scripts/ /home/serveruser/number-verification-backend-app/
WORKDIR "/home/serveruser/number-verification-backend-app"
CMD [ "python", "./main.py" ]
