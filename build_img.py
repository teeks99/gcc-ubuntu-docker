import sys
import subprocess
import datetime
import argparse
import json
import platform

options = None
push_log = {"versions":{}}

class Image(object):
    def __init__(self, repo, tag):
        self.repo = repo
        self.tag = tag

    @property
    def image(self):
        return f"{self.repo}:{self.tag}"


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

    pull = "--pull"
    if options.no_update_base:
        pull = ""

    cmd = f"docker build {pull} {force} --tag {image.image} gcc-{version}"
    run_my_cmd(cmd)
    return image


SMOKE_PASSED = "SMOKE TEST PASSED"

# Compiled and run inside the image by the smoke test. Reports the gcc version
# it was built with and the libstdc++ it picked up, so a build log shows which
# standard library came along with the compiler.
HELLO_WORLD = """\
#include <iostream>
#include <string>
#include <vector>

int main()
{
    std::vector<std::string> words = {"hello", "world"};
    std::string message;
    for (const std::string& word : words)
    {
        if (!message.empty())
        {
            message += ", ";
        }
        message += word;
    }

    std::cout << message << std::endl;
    std::cout << "gcc major: " << __GNUC__ << std::endl;
    std::cout << "libstdc++: " << __GLIBCXX__ << std::endl;
    return 0;
}
"""

# The other language these images are configured for: --enable-languages=c,c++,
# and gcc gets the same unversioned symlink treatment as g++.
HELLO_WORLD_C = """\
#include <stdio.h>

int main(void)
{
    printf("hello, world\\n");
    printf("gcc major: %d\\n", __GNUC__);
    return 0;
}
"""

# Fed to bash on the container's stdin, with the gcc version as $1. Checks the
# versioned compilers and both unversioned symlinks, builds and runs hello world
# in C and C++, then makes sure the libstdc++ those binaries pick up at run time
# is no older than the one they were built against.
SMOKE_TEST = """\
set -eu

version="$1"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fail() {
    echo "SMOKE TEST FAILED: $*" >&2
    exit 1
}

contains() {
    case "$1" in
        *"$2"*) return 0 ;;
        *) return 1 ;;
    esac
}

check_version() {
    compiler="$1"
    echo "--- $compiler --version"
    output="$("$compiler" --version 2>&1)" || fail "could not run $compiler --version"
    echo "$output"
    contains "$output" "(GCC) $version." \\
        || fail "$compiler is not gcc version $version"
}

build_and_run() {
    label="$1"
    compiler="$2"
    src="$3"
    shift 3
    echo "--- $compiler $* -o hello_$label $src"
    "$compiler" "$@" -o "$work/hello_$label" "$work/$src" \\
        || fail "$compiler $* could not compile $src"
    output="$("$work/hello_$label" 2>&1)" || fail "the $label hello world would not run"
    echo "$output"
    contains "$output" "hello, world" \\
        || fail "the $label hello world printed the wrong thing"
    contains "$output" "gcc major: $version" \\
        || fail "the $label hello world was not built by gcc $version"
}

# The newest symbol version a libstdc++ carries, e.g. GLIBCXX_3.4.32.
newest_glibcxx() {
    objdump -T "$1" | grep -oE "GLIBCXX_3[.]4[.][0-9]+" | sort -uV | tail -1
}

cat > "$work/hello.cpp" <<'END_OF_HELLO_WORLD'
""" + HELLO_WORLD + """END_OF_HELLO_WORLD

cat > "$work/hello.c" <<'END_OF_HELLO_WORLD_C'
""" + HELLO_WORLD_C + """END_OF_HELLO_WORLD_C

# The versioned binaries, plus the unversioned symlinks the Dockerfile makes.
check_version "g++-$version"
check_version "gcc-$version"
check_version g++
check_version gcc

# Both languages, and the newer dialect people come to a hand-built gcc for.
build_and_run cxx17 "g++-$version" hello.cpp -std=c++17
build_and_run c11 "gcc-$version" hello.c -std=c11
build_and_run cxx20 g++ hello.cpp -std=c++20

# Compiling is only half the job. g++ links against the libstdc++ sitting next
# to it, but ld.so hands the program whatever its cache resolves at run time. If
# that is the older copy from the base image, anything reaching for a newer
# library symbol dies on startup even though it compiled cleanly here.
echo "--- libstdc++ the hello world runs against"
ldd "$work/hello_cxx20" || fail "could not run ldd on the hello world"
compiler_lib="$("g++-$version" -print-file-name=libstdc++.so.6)"
[ -f "$compiler_lib" ] || fail "g++-$version cannot find its own libstdc++.so.6"
runtime_lib="$(ldd "$work/hello_cxx20" | awk '$1 == "libstdc++.so.6" { print $3 }')"
[ -f "$runtime_lib" ] || fail "ld.so did not resolve libstdc++.so.6 to a file"
compiler_abi="$(newest_glibcxx "$compiler_lib")"
runtime_abi="$(newest_glibcxx "$runtime_lib")"
echo "compiler links: $compiler_lib ($compiler_abi)"
echo "ld.so resolves: $runtime_lib ($runtime_abi)"
older="$({ echo "$compiler_abi"; echo "$runtime_abi"; } | sort -V | head -1)"
if [ "$runtime_abi" != "$compiler_abi" ] && [ "$older" = "$runtime_abi" ]; then
    fail "ld.so resolves libstdc++ to $runtime_abi, older than the $compiler_abi that g++-$version builds against, so binaries using newer library symbols will not start"
fi

""" + 'echo "' + SMOKE_PASSED + '"\n'


def test(image, test_version):
    cmd = f"docker run --rm -i {image.image} bash -s {test_version}"
    print(cmd)
    result = subprocess.run(
        cmd, shell=True, input=SMOKE_TEST.encode(),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout.decode()
    print(output)
    if result.returncode != 0 or SMOKE_PASSED not in output:
        raise AssertionError(f"Smoke test failed for {image.image}")


def tag_timestamp(base_image, version):
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M")
    arch_str = f"_{options.arch}" if options.arch else ""
    tag = f"{version}{arch_str}_{timestamp}"
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


def create_and_push_manifest(version_tag, amend_tags):
    # Not `docker manifest create`: it rejects a source that is itself an index,
    # which a per-arch push becomes once the build attaches a provenance
    # attestation (the default with Docker's containerd image store).
    # imagetools takes either kind, and creates and pushes in one step.
    manifest_image = Image(options.repo, version_tag)
    cmd = f"docker buildx imagetools create --tag {manifest_image.image}"
    for tag in amend_tags:
        cmd += f" {options.repo}:{tag}"
    run_my_cmd(cmd)


def remove_image(image):
    cmd = f"docker rmi {image.image}"
    run_my_cmd(cmd)


def build_one(version, push_latest=False):
    tags = []
    base_image = None
    time_image = None
    latest_image = None

    if options.manifest_only:
        amend_tags = options.manifest_only
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M")
        time_tag = f"{version}_{timestamp}"

        create_and_push_manifest(time_tag, amend_tags)
        create_and_push_manifest(version, amend_tags)
        if push_latest:
            create_and_push_manifest("latest", amend_tags)

        pushes = {}
        pushes["timestamp"] = time_tag
        if push_latest:
            pushes["latest"] = True
        push_log["versions"][version] = pushes
        return

    if not options.no_build:
        base_image = build(version)

    if not options.no_test:
        test(base_image, version)

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
        amend_tags = [time_image.tag] + options.manifest_add
        create_and_push_manifest(version, amend_tags)
        if push_latest:
            create_and_push_manifest("latest", amend_tags)

    if options.delete_timestamp_tag:
        remove_image(time_image)


def set_options():
    parser = argparse.ArgumentParser(
        description="Build one or more docker images for gcc-ubuntu")
    parser.add_argument(
        "-v", "--version", action="append", required=True,
        help="Use one or more times to specify the versions to run")
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
        "--manifest-only", nargs="+",
        help="Create a manifest from the provided timestamp tags, without building." +
        " Will create a manifest for the version and a new timestamp.")
    parser.add_argument(
        "--arch", nargs='?', const='auto', default="",
        help="Architecture string to include in the timestamp tag (e.g. amd64, arm64). If passed without value, it autodetects.")
    parser.add_argument(
        "-l", "--log-file", default="",
        help="json file to log pushes into")

    global options
    options = parser.parse_args()

    if options.manifest_add and len(options.version) > 1:
        raise RuntimeError("Cannot support manifest with multiple versions")

    if options.manifest_only and len(options.version) > 1:
        raise RuntimeError("Cannot support manifest-only with multiple versions")


def run():
    set_options()
    push_log["repo"] = options.repo

    if options.arch == 'auto':
        machine = platform.machine().lower()
        if machine in ['x86_64', 'amd64']:
            options.arch = 'amd64'
        elif machine in ['aarch64', 'arm64']:
            options.arch = 'arm64'
        else:
            options.arch = machine

    for version in options.version:
        latest = options.latest and version == options.version[-1]
        build_one(version, latest)

    if options.log_file:
        with open(options.log_file, "w") as f:
            json.dump(push_log, f)


if __name__ == "__main__":
    run()
