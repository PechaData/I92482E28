from pathlib import Path
from pecha_uploader.config import Destination_url
from pecha_uploader.pipeline import upload_commentary
from openpecha.pecha import Pecha
import subprocess
from openpecha.utils import read_json, write_json
import re
import os
from openpecha.github_utils import commit
from git import Repo
from openpecha.storages import commit_and_push

Github_token = os.getenv("GITHUB_TOKEN")

def get_pecha_json(pecha: Pecha):
    pecha_id = pecha.id
    pecha_path = pecha.pecha_path.__str__()
    subprocess.run("git checkout pecha_json", cwd=pecha_path, shell=True, check=True)
    subprocess.run(["git pull"], cwd=pecha_path, shell=True, check=True)
    json_path = f"{pecha_path}/{pecha_id}.json"
    commentar_json = read_json(json_path)
    return commentar_json

def get_pecha_segments(pecha: Pecha):
    base_name = list(pecha.bases.keys())[0]
    segments = []
    for _, ann_store in pecha.get_layers(base_name=base_name):
        for ann in list(ann_store):
            segment_id = str(ann.data()[0])
            segment_text = ann.text()[0]
            segments.append({"id": segment_id, "text": segment_text})
    return segments

def insert_text_after_tag(text, new_text):
    pattern = r"(<\d+><\d+>)"
    match = re.match(pattern, text)
    if new_text == "":
        return match.group(1)
    updated_text = match.group(1) + new_text
    updated_text = updated_text.replace("$", "\n")
    return updated_text


def update_repo(repo_path):
    local_repo = Repo(repo_path)
    commit_and_push(repo=local_repo, message="updated with new serizlized json", branch="pecha_json")


def update_the_json(pecha: Pecha):
    new_content = []
    pecha_id = pecha.id
    opf_segments = get_pecha_segments(pecha)
    commentary_json = get_pecha_json(pecha)
    json_content = commentary_json["source"]["books"][0]["content"][0]
    for new_segment in opf_segments:
        new_text = new_segment["text"]
        segment_id = (int(new_segment["id"]) - 1)
        old_text = json_content[segment_id]
        updated_text = insert_text_after_tag(old_text, new_text)
        new_content.append(updated_text)
    commentary_json["source"]["books"][0]["content"][0] = new_content
    write_json(Path(f"{pecha.pecha_path}/{pecha_id}.json"), commentary_json)
    upload_commentary(Path(f"{pecha.pecha_path}/{pecha_id}.json"), Destination_url.STAGING, overwrite=True)
    update_repo(pecha.pecha_path.__str__())
    



def main():
    pecha_id = pecha_id = Path.cwd().name
    pecha = Pecha.from_id(pecha_id)
    update_the_json(pecha)

main()
