import sys
import subprocess
import datetime
import argparse
import re

options = None

versions = [
    # Precise
    # "4.4", "4.5",
    # Trusty
    "4.6", "4.7", "4.8", "4.9", "5", "6",
    # Xenial
    "7",
    # Bionic
    "8",
    # Focal
    "9", "10", "11",
    # Jammy
    "12"
    ]

test_versions = {}


def update_base_images():
    if not options.no_update_base:
        # subprocess.check_call("docker pull ubuntu:precise", shell=True)
        subprocess.check_call("docker pull ubuntu:trusty", shell=True)
        subprocess.check_call("docker pull ubuntu:xenial", shell=True)
        subprocess.check_call("docker pull ubuntu:bionic", shell=True)
        subprocess.check_call("docker pull ubuntu:focal", shell=True)
        subprocess.check_call("docker pull ubuntu:jammy", shell=True)


def build(version):
    tag = f"{options.repo}:{version}"

    force = "--no-cache"
    if options.no_force:
        force = ""

    cmd = f"docker build {force} --tag {tag} gcc-{version}"
    print(cmd)
    try:
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print("Failure in command: " + cmd)
        raise
    return tag


def test(tag, test_version):
    cmd = f"docker run --rm {tag} g++-{test_version} --version"
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


def tag_timestamp(base_tag, version):
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M")
    tag = f"{options.repo}:{version}_{timestamp}"
    cmd = f"docker tag {base_tag} {tag}"
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print("Failure in command: " + cmd)
        raise
    return tag


def tag_latest(base_tag):
    tag = f"{options.repo}:latest"
    cmd = f"docker tag {base_tag} {tag}"
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print("Failure in command: " + cmd)
        raise
    return tag


def push_tag(tag):
    cmd = f"docker push {tag}"
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print("Failure in command: " + cmd)
        raise


def remove_tag(tag):
    cmd = f"docker rmi {tag}"
    try:
        print(cmd)
        subprocess.check_call(cmd, shell=True)
    except Exception:
        print("Failure in command: " + cmd)
        raise


def all():
    for version in versions:
        build_one(version)


def build_one(version):
    tags = []
    base_tag = None
    time_tag = None
    latest_tag = None

    if not options.no_build:
        base_tag = build(version)

    if not options.no_test:
        tv = version
        if version in test_versions:
            tv = test_versions[version]

        test(base_tag, tv)

    if not options.no_tag_timestamp:
        time_tag = tag_timestamp(base_tag, version)

    if not options.no_latest:
        latest_tag = tag_latest(base_tag)

    if options.push:
        for tag in (base_tag, time_tag, latest_tag):
            if tag:
                push_tag(tag)

    if options.delete_timestamp_tag:
        remove_tag(time_tag)


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
        "--no-latest", action="store_true",
        help="don't update each to latest tag, whichever version is"
        + " specified last will win")
    parser.add_argument(
        "-r", "--repo", default="test/gcc",
        help="repo to build for and push to. Default is test/gcc, " +
             "use teeks99/gcc-ubuntu for dockerhub")
    parser.add_argument(
        "-p", "--push", action="store_true", help="push to dockerhub")
    parser.add_argument(
        "-d", "--delete-timestamp-tag", action="store_true",
        help="remove the timestamp tag from the local machine")

    global options
    options = parser.parse_args()


def run():
    set_options()

    if options.version:
        global versions
        versions = options.version

    update_base_images()

    all()


if __name__ == "__main__":
    run()
