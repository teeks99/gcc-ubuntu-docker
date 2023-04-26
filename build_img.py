import sys
import subprocess
import datetime
import argparse
import re
import json

options = None
push_log = {"versions":{}}

versions = [
    # Precise
    # "4.4", "4.5",
    # Trusty
    # "4.6", "4.7", "4.8", "4.9", "5", "6",
    # Xenial
    "7",
    # Bionic
    "8",
    # Focal
    "9", "10", "11",
    # Jammy
    "12", "13", "14"
    ]

test_versions = {}

class Image(object):
    def __init__(self, repo, tag):
        self.repo = repo
        self.tag = tag

    @property
    def image(self):
        return f"{self.repo}:{self.tag}"

def update_base_images():
    if not options.no_update_base:
        # subprocess.check_call("docker pull ubuntu:precise", shell=True)
        #subprocess.check_call("docker pull ubuntu:trusty", shell=True)
        subprocess.check_call("docker pull ubuntu:xenial", shell=True)
        subprocess.check_call("docker pull ubuntu:bionic", shell=True)
        subprocess.check_call("docker pull ubuntu:focal", shell=True)
        subprocess.check_call("docker pull ubuntu:jammy", shell=True)


def run_my_cmd(cmd):
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print("Failure in command: " + cmd)
        raise
def build(version):
    image = Image(options.repo, version)

    force = "--no-cache"
    if options.no_force:
        force = ""

    cmd = f"docker build {force} --tag {image.image} gcc-{version}"
    run_my_cmd(cmd)
    return image


def test(image, test_version):
    cmd = f"docker run --rm {image.image} g++-{test_version} --version"
    re_expected = f"g\+\+-{test_version}.*\) {test_version}\."
    try:
        print(cmd)
        output = subprocess.check_output(cmd, shell=True)
        if not re.search(re_expected, output.decode()):
            msg = f"Expected regex: \n{re_expected}\n"
            msg += f"Not found in actual output: \n{output}\n"
            raise AssertionError(msg)
        else:
            print("Corectly got:")
            print(output.decode())
    except Exception:
        print("Failure in command: " + cmd)
        raise


def tag_timestamp(base_image, version):
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M")
    tag = f"{version}_{timestamp}"
    image = Image(options.repo, tag)
    cmd = f"docker tag {base_image.image} {image.image}"
    run_my_cmd(cmd)
    return image


def tag_latest(base_image):
    image = Image(options.repo,"latest")
    cmd = f"docker tag {base_image.image} {image.image}"
    run_my_cmd(cmd)
    return image


def push_image(image):
    cmd = f"docker push {image.image}"
    run_my_cmd(cmd)


def create_and_push_manifest(time_image, version_tag):
    manifest_image = Image(options.repo, version_tag)
    cmd = f"docker manifest rm {manifest_image.image}"
    try:
        run_my_cmd(cmd)
    except subprocess.CalledProcessError:
        pass

    cmd = f"docker manifest create {manifest_image.image}"
    cmd += f" --amend {time_image.image}"
    for additional in options.manifest_add:
        cmd += f" --amend {options.repo}:{additional}"
    run_my_cmd(cmd)

    cmd = f"docker manifest push {manifest_image.image}"
    run_my_cmd(cmd)


def remove_image(image):
    cmd = f"docker rmi {image.image}"
    run_my_cmd(cmd)


def all():
    for version in versions:
        latest = False
        if options.latest and version == versions[-1]:
            latest = True
        build_one(version, latest)


def build_one(version, push_latest=False):
    tags = []
    base_image = None
    time_image = None
    latest_image = None

    if not options.no_build:
        base_image = build(version)

    if not options.no_test:
        tv = version
        if version in test_versions:
            tv = test_versions[version]

        test(base_image, tv)

    if not options.no_tag_timestamp:
        time_image = tag_timestamp(base_image, version)

    if push_latest:
        if not options.manifest_add:
            latest_image = tag_latest(base_image)

    if options.no_push_tag or options.manifest_add:
        base_image = None

    if options.push:
        for img in (base_image, time_image, latest_image):
            if img:
                push_image(img)

        pushes = {}
        if base_image:
            pushes["base"] = base_image.tag
        if time_image:
            pushes["timestamp"] = time_image.tag
        if latest_image:
            pushes["latest"] = True
        push_log["versions"][version] = pushes

    if options.manifest_add:
        create_and_push_manifest(time_image, version)
        if push_latest:
            create_and_push_manifest(time_image, "latest")

    if options.delete_timestamp_tag:
        remove_image(time_image)


def set_options():
    parser = argparse.ArgumentParser(
        description="Build one or more docker images for gcc-ubuntu")
    parser.add_argument(
        "-v", "--version", action="append",
        help="Use one of more times to specify the versions to run, skip"
        + " for all")
    parser.add_argument(
        "--no-update-base", action="store_true",
        help="Don't update the base images")
    parser.add_argument(
        "--no-build", action="store_true", help="skip build step")
    parser.add_argument(
        "--no-force", action="store_true",
        help="don't force an update, use existing layers")
    parser.add_argument(
        "--no-test", action="store_true", help="skip the test step")
    parser.add_argument(
        "--no-tag-timestamp", action="store_true", help="only version tag")
    parser.add_argument(
        "--latest", action="store_true",
        help="Update latest tag. If multiple versions, applies to last one." +
        " If --manifest-add specified will create a latest manifest")
    parser.add_argument(
        "-T", "--no-push-tag", action="store_true",
        help="Do not apply the tag for the version, only the timestamp tag")
    parser.add_argument(
        "-r", "--repo", default="test/gcc",
        help="repo to build for and push to. Default is test/gcc, " +
             "use teeks99/gcc-ubuntu for dockerhub")
    parser.add_argument(
        "-p", "--push", action="store_true", help="push to dockerhub")
    parser.add_argument(
        "-d", "--delete-timestamp-tag", action="store_true",
        help="remove the timestamp tag from the local machine")
    parser.add_argument(
        "-m", "--manifest-add", action="append",
        help="Generate a manifest for the version supplied, using the" +
        " timestamp upload as the first version add the timestamp(s)" +
        " specified here as additional versions. Used for generating" + 
        " multiarch images on different machines.")
    parser.add_argument(
        "-l", "--log-file", default="",
        help="json file to log pushes into")

    global options
    options = parser.parse_args()

    if options.manifest_add and len(options.version) > 1:
        raise RuntimeError("Cannot support manifest with multiple versions")

def run():
    set_options()
    push_log["repo"] = options.repo

    if options.version:
        global versions
        versions = options.version

    update_base_images()

    all()

    if options.log_file:
        with open(options.log_file, "w") as f:
            json.dump(push_log, f)

if __name__ == "__main__":
    run()
