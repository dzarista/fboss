# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import urllib
import os

class AristaArtifactCache(object):
    artUrl = "https://artifactory.infra.corp.arista.io/artifactory/arista-fboss/getdeps-cache"

    def download_to_file(self, name, dest_file_name) -> bool:
        artifactUrl = f"{self.artUrl}/{name}"
        # Download cached artifact if it exists
        try:
            urllib.request.urlretrieve(artifactUrl, dest_file_name)
        except:
            return False
        return os.path.exists(dest_file_name)

    def upload_from_file(self, name, source_file_name) -> None:
        pass

def create_cache() -> None:
    return AristaArtifactCache()
