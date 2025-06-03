# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import urllib
import os
import requests

# Artifactory repository and authentication information
ARTIFACTORY_URL = "https://artifactory.infra.corp.arista.io/artifactory/fboss-build-stash/getdeps-cache"
ARTIFACTORY_SERVICE_USER = "srv-fboss-arista@arista.com"

class AristaArtifactCache(object):
    def __init__(self):
        self.artUrl = ARTIFACTORY_URL
        self.user = ARTIFACTORY_SERVICE_USER
        self.secret = os.environ.get("FBOSS_ARTIFACTORY_TOKEN")
        if self.secret:
            print("AristaArtifactCache: Found Artifactory token")

    def download_to_file(self, name, dest_file_name) -> bool:
        artifactUrl = f"{self.artUrl}/{name}"
        # Download cached artifact if it exists
        try:
            urllib.request.urlretrieve(artifactUrl, dest_file_name)
        except:
            return False
        return os.path.exists(dest_file_name)

    def upload_from_file(self, name, source_file_name) -> None:
        uploadUrl = f"{self.artUrl}/{name}"
        # Do not upload if secret is not present in environment
        if self.secret:
            try:
                with open(source_file_name, 'rb') as uploadFile:
                    resp = requests.put(url=uploadUrl, 
                                        data=uploadFile,
                                        auth=(self.user, self.secret))
                    print(f"AristaArtifactCache: upload status code {resp.status_code}")
            except Exception as e:
                print("AristaArtifactCache: Caught exception but continuing")
                print(e)
                pass

def create_cache() -> None:
    return AristaArtifactCache()
