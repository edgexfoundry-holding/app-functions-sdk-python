#
# Copyright (c) 2024 IOTech Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

.PHONY: docker run

# TODO: uncomment and remove default once files are in a Github repository or
#       remove totally including usage below
#GIT_SHA=$(shell git rev-parse HEAD)
GIT_SHA=no-sha

docker:
	docker build \
	--build-context root=../ \
	--build-arg http_proxy \
	--build-arg https_proxy \
	-f Dockerfile \
	--label "git_sha=$(GIT_SHA)" \
	-t $(USER)/app-service-template:latest \
	.

run:
	docker run -it --rm --name my-app-service $(USER)/app-service-template

test:
	python3 -m unittest discover . -v
