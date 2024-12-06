FROM python:3.10-alpine3.20

# TODO: Change Copyright to your company if open sourcing or remove label
LABEL license='SPDX-License-Identifier: Apache-2.0' \
  copyright='Copyright (c) 2024: IOTech'

RUN apk add --update --no-cache git
# Ensure using latest versions of all installed packages to avoid any recent CVEs
RUN apk --no-cache upgrade

# Must specify root to the parent directory of app-functions-sdk-python source folder with --build-context argument
# when running docker build command
COPY --from=root /src /src
COPY --from=root /pyproject.toml /pyproject.toml
COPY --from=root /requirements.txt /requirements.txt
COPY --from=root /setup.py /setup.py
ADD res ./res
ADD main.py .
RUN pip3 install .
RUN pip3 install -r requirements.txt
CMD [ "python" , "./main.py" ]
