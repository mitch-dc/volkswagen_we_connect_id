"""
Initialize container with modules used by volkswage_we_connect_id component
"""

import json
import pip

PIP_ARGUMENTS = [ "install", "--user", "homeassistant" ]
MANIFEST_PATH = "custom_components/volkswagen_we_connect_id/manifest.json"

with open(MANIFEST_PATH, "r", encoding="utf8") as MANIFEST_FILE:
    MANIFEST = json.load(MANIFEST_FILE)
    REQUIREMENTS: list[str] = MANIFEST["requirements"]

pip.main(PIP_ARGUMENTS + REQUIREMENTS)
