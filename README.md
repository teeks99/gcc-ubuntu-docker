# gcc-ubuntu-docker

Docker images with a versioned GCC toolchain installed on Ubuntu, published to Docker Hub
as [teeks99/gcc-ubuntu](https://hub.docker.com/r/teeks99/gcc-ubuntu).

The older versions come from Ubuntu's own `gcc-<version>` packages; everything from GCC 11
on is compiled from source, so each image is built on the newest Ubuntu release that
version will build against.

## Images

| GCC | Ubuntu base | Built from | Built by |
| --- | ----------- | ---------- | -------- |
| 11, 12, 13 | `jammy` (22.04) | Release tarball (11.5.0, 12.5.0, 13.4.0) | legacy workflow |
| 14, 15 | `noble` (24.04) | Release tarball (14.4.0, 15.3.0) | legacy workflow |
| 16 | `noble` (24.04) | `releases/gcc-16` git branch | current workflow (also tagged `latest`) |
| 17 | `noble` (24.04) | `master` git branch (development snapshot) | pre-release workflow |

Older versions (GCC < 9) are no longer built; they no longer compile and their Ubuntu bases
are out of support.

Every image installs `build-essential` and `ca-certificates`. The source-built images (11
and later) add the tools needed for a GCC build — `m4`, `flex`, `bison`, `wget` — plus
`apt-utils`, `dialog` and `locales`; 13 and later also add `git`. GCC 17 installs
`libgmp-dev`, `libmpfr-dev`, `libmpc-dev`, `libisl-dev`, `texinfo` and `gawk` directly
instead of running `contrib/download_prerequisites`, and configures with `--disable-werror`
because it tracks the development branch.

Source builds are configured with `--enable-languages=c,c++ --disable-multilib`, installed
under `/usr/local/gcc-<version>` with `-<version>`-suffixed binaries in `/usr/bin`, and
their `lib64` directory added to `/etc/ld.so.conf.d`. On those images `/usr/bin/gcc` and
`/usr/bin/g++` are replaced with symlinks to the versioned binaries, so both `g++` and
`g++-16` work. The 9 and 10 images keep focal's default `gcc`/`g++` (GCC 9), so use the
versioned `g++-10` there. On the `noble` images the default `ubuntu` user is removed,
leaving UID 1000 free for a user created at runtime.

Images are published for both `linux/amd64` and `linux/arm64`.

```bash
docker run --rm teeks99/gcc-ubuntu:16 g++ --version
```

## Tag patterns

| Tag | Example | What it is |
| --- | ------- | ---------- |
| `latest` | `latest` | Multi-arch manifest for the current stable release (GCC 16) |
| `<version>` | `16` | Multi-arch manifest, moves with each rebuild of that version |
| `<version>_<timestamp>` | `16_20260901_0007` | Immutable multi-arch manifest for one build run |
| `<version>_<arch>_<timestamp>` | `16_amd64_20260901_0004` | The single-arch image a manifest is built from |

Timestamps are UTC, formatted `YYYYMMDD_HHMM`. The per-arch tags are what each builder
pushes; the manifest job then combines them and stamps its own timestamp on the
`<version>_<timestamp>` manifest, so it will differ by a few minutes from the per-arch tags
it references.

Pin `<version>_<timestamp>` for reproducible builds — the `<version>` and `latest` tags are
re-pointed every time the images are rebuilt.

## Building with build_img.py

`build_img.py` drives the whole build/test/tag/push/manifest cycle. It needs Python 3 and a
working `docker` CLI, and shells out to `docker` for everything.

For each requested version it will, by default:

1. `docker build --pull --no-cache` the matching `gcc-<version>` directory,
2. test the result by running `g++-<version> --version` inside it and checking the output,
3. apply a timestamp tag,
4. optionally push, and optionally combine per-arch builds into a manifest.

The default repo is `test/gcc`, so a bare run builds and tags locally without touching
Docker Hub. At least one `-v` is required; repeat it to act on several versions.

```bash
# Build and test one version locally
python build_img.py -v 16

# Build just GCC 14 and 15
python build_img.py -v 14 -v 15

# Build one version and push it to Docker Hub
python build_img.py -v 16 -r teeks99/gcc-ubuntu -p

# What CI runs on each builder: push only the arch-stamped timestamp tag
python build_img.py -v 16 -r teeks99/gcc-ubuntu -p -T --arch -l amd64_log.json

# Then, once both arches are up, combine them into the manifests
python build_img.py -v 16 -r teeks99/gcc-ubuntu --manifest-only 16_amd64_20260901_0004 16_arm64_20260901_0006 --latest
```

Source builds take a long time — an image for GCC 11 and up compiles the whole compiler
with `make -j$(nproc)`.

### Options

| Option | Effect |
| ------ | ------ |
| `-v`, `--version` | Version to act on; repeat for several. Required. |
| `-r`, `--repo` | Repo to tag and push to. Default `test/gcc`; use `teeks99/gcc-ubuntu` for Docker Hub. |
| `-p`, `--push` | Push the tags that were created. |
| `--arch [NAME]` | Include an architecture in the timestamp tag. Bare `--arch` autodetects (`amd64`/`arm64`). |
| `--latest` | Also tag/push `latest`. With several versions it applies to the last one; with `--manifest-add`/`--manifest-only` it creates a `latest` manifest. |
| `-T`, `--no-push-tag` | Don't push the bare `<version>` tag, only the timestamp tag. |
| `--no-tag-timestamp` | Skip the timestamp tag, version tag only. |
| `-d`, `--delete-timestamp-tag` | Drop the timestamp tag from the local machine when done. |
| `--no-build` | Skip the build step. |
| `--no-test` | Skip the test step. |
| `--no-force` | Drop `--no-cache`, reuse existing layers. |
| `--no-update-base` | Drop `--pull`, don't re-fetch the Ubuntu base image. |
| `-m`, `--manifest-add` | Build, then create a manifest from this build's timestamp tag plus the tag(s) given here. Single `-v` only. |
| `--manifest-only` | Don't build; create the `<version>` and `<version>_<timestamp>` manifests from the timestamp tags listed. Single `-v` only. |
| `-l`, `--log-file` | Write a JSON record of what was pushed, including the timestamp tag. |

The log file written by `-l` is how the two per-arch CI jobs hand their timestamp tags to
the manifest job:

```json
{"versions": {"16": {"timestamp": "16_amd64_20260901_0004"}}, "repo": "teeks99/gcc-ubuntu"}
```

## Automated builds

Three GitHub Actions workflows in [.github/workflows](.github/workflows) build on
`ubuntu-latest` and `ubuntu-24.04-arm`, then join the two into a manifest. All three can
also be started by hand with `workflow_dispatch`, and each one triggers a matching
[teeks99/boost-cpp-docker](https://github.com/teeks99/boost-cpp-docker) build when it
finishes.

| Workflow | Schedule | Versions |
| -------- | -------- | -------- |
| `build-current.yml` | Monthly, 1st at 00:00 UTC | 16, and updates `latest` |
| `build-legacy.yml` | May 1 and Nov 1 | 9–15, one matrix job per version |
| `build-prerelease.yml` | Weekly, Sundays | 17 |

The legacy workflow keeps going when a single version fails, so the versions that did build
on both arches still get their manifests.

## Adding a version

Copy the newest `gcc-<n>` directory to `gcc-<n+1>`, update the `gccver` and `suffix` ARGs in
the `Dockerfile`, and switch the source between the release tarball and the `git clone` —
both are in there, one commented out. Then point the workflow at it: bump `GCC_VERSION` in
`build-current.yml` or `build-prerelease.yml`, and move the version it replaces into the
`versions` list in `build-legacy.yml`.

## License

MIT — see [LICENSE](LICENSE).
