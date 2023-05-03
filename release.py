from zipfile import ZipFile
import os
from os.path import basename
import os
import re
import logging
import pathlib

logging.basicConfig(file=os.getenv("GITHUB_STEP_SUMMARY"), level=logging.INFO)

ACCEPTED_PATTERNS = tuple(
    re.compile(pattern) for pattern in (r".*\.py$", r".*\.blend$", r".*\.md$")
)
EXCLUDED_PATTERNS = tuple(
    re.compile(pattern) for pattern in (r".*/__pycache__/.*", ".*/.vscode/.*")
)


TAG = os.getenv("GITHUB_REF")
if TAG is None or "/" in TAG:
    try:
        from kuba_addon import bl_info
    except ModuleNotFoundError as e:
        bl_info = e.bl_info

    TAG = "v" + ".".join(str(v) for v in bl_info["version"])

if __name__ == "__main__":
    # old way:
    # print(f"::set-output name=tag_string::{TAG}")

    # new way:
    if github := os.environ["GITHUB_OUTPUT"]:
        with open(github, "a") as fh:
            print(f"tag_string={TAG}", file=fh)
    with ZipFile(f"kuba-addon-{TAG}.zip", "w") as zipObj:
        for folderName, subfolders, filenames in os.walk("kuba_addon"):
            for filename in filenames:
                # create complete filepath of file in directory
                filePath = os.path.join(folderName, filename)
                filePath = pathlib.Path(filePath).as_posix()
                is_exluded = any(pat.match(filePath) for pat in EXCLUDED_PATTERNS)
                if is_exluded:
                    continue
                is_accepted = any(pat.match(filePath) for pat in ACCEPTED_PATTERNS)
                if not is_accepted:
                    continue
                logging.info(f"zipping: {filePath}")
                # Add file to zip
                zipObj.write(filePath, filePath)
