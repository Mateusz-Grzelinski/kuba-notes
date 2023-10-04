from zipfile import ZipFile
import os
from os.path import basename
import os
import re
import logging
import pathlib

logging.basicConfig(filename=os.getenv("GITHUB_STEP_SUMMARY"), level=logging.INFO)

ACCEPTED_PATTERNS = set(
    re.compile(pattern)
    for pattern in (
        r".*\.py$",
        r".*\.blend$",
        r".*\.md$",
    )
)
EXCLUDED_PATTERNS = set(
    re.compile(pattern)
    for pattern in (
        r".*/__pycache__/.*",
        ".*/.vscode/.*",
    )
)


def get_version() -> None | str:
    try:
        from kuba_addon import bl_info
    except ModuleNotFoundError as e:
        # hacky way of getting addon version
        bl_info = e.bl_info
        tag = "v" + ".".join(str(v) for v in bl_info["version"])
        return tag


TAG = get_version()


def write_github_output():
    # old way:
    # print(f"::set-output name=tag_string::{TAG}")

    # new way
    github_output_file = os.getenv("GITHUB_OUTPUT")
    if github_output_file is None:
        return None
    with open(github_output_file, "a") as fh:
        print(f"tag_string={TAG}", file=fh)


def create_release_zip():
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


if __name__ == "__main__":
    create_release_zip()
    write_github_output()
