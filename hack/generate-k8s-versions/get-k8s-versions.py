# Little script to fetch current k8s versions for cloudprofile
#
# Usage: Set github token as env variable GITHUB_TOKEN and Charts.yaml file as first parameter
# and values.yaml as second parameter
#
# Example GITHUB_TOKEN=pat_blabla python get-k8s-versions.py Chart.yaml values.yaml

from github import Github
import semver
import sys
import ruamel.yaml as yaml
import os

g = Github(os.getenv("GITHUB_TOKEN"))

latest_semver = semver.VersionInfo.parse(g.get_repo("kubernetes/kubernetes").get_latest_release().tag_name[1:]) # cutting leading v
minor_old = semver.VersionInfo(1, latest_semver.minor - 1, 0, "incomplete")
minor_old2 = semver.VersionInfo(1, latest_semver.minor - 2, 0, "incomplete")
minor_old3 = semver.VersionInfo(1, latest_semver.minor - 3, 0, "incomplete")

new_versions = [latest_semver]
old_versions = []

for release in g.get_repo("kubernetes/kubernetes").get_releases():
    semver_release = semver.VersionInfo.parse(release.tag_name[1:]) # again, cut the hopefully leading v
    if semver_release.prerelease is not None:
        continue
    if semver_release.build is not None:
        continue
    if minor_old.prerelease == "incomplete" and semver_release.minor == minor_old.minor:
        minor_old = minor_old.replace(prerelease=None)
        minor_old = minor_old.replace(patch = semver_release.patch)
        new_versions.append(minor_old)
        continue
    if minor_old2.prerelease == "incomplete" and semver_release.minor == minor_old2.minor:
        minor_old2 = minor_old2.replace(prerelease=None)
        minor_old2 = minor_old2.replace(patch = semver_release.patch)
        new_versions.append(minor_old2)
        continue
    if minor_old3.prerelease == "incomplete" and semver_release.minor == minor_old3.minor:
        minor_old3 = minor_old3.replace(prerelease=None)
        minor_old3 = minor_old3.replace(patch = semver_release.patch)
        new_versions.append(minor_old3)
        continue
    if minor_old.prerelease is None and minor_old2.prerelease is None and  minor_old3.prerelease is None:
        break

with open(sys.argv[1], "r") as stream:
    try:
        values = yaml.safe_load(stream)
        for version in list(values["global"]["kubernetes"]["upstreamVersions"]["versions"].keys()):
            old_versions.append(semver.VersionInfo.parse(version))
    except yaml.YAMLError as exc:
        print(exc)

if len(new_versions) != 4 or len(old_versions) != 4:
    print("Error, expecting exactly 4 supported kubernetes verions.")
    exit()

new_versions.sort()
old_versions.sort()

# Version step is 0 if no version bump happens at all, it is 1 if only patch versions increase
# it is 2 if at least one minor version bump took place
version_step = 0

# Assuming major is always 1:
# First check if a minor version has been upgraded
for i, version in enumerate(new_versions):
    if new_versions[i].minor > old_versions[i].minor:
        version_step = 2
        print("We have a minor update")
        break

if version_step == 0:
# if no minor update took place, lets check if a patch update took place
    for i, version in enumerate(new_versions):
        if new_versions[i].minor == old_versions[i].minor:
            if new_versions[i].patch > old_versions[i].patch:
                version_step = 1
                print("We have a patch update")
                break

if version_step == 0:
    # All done
    exit()

# Write values.yaml
with open(sys.argv[1], "r") as stream:
    try:
        values = yaml.safe_load(stream)
        values["global"]["kubernetes"]["upstreamVersions"]["versions"].clear()
        for version in new_versions:
            values["global"]["kubernetes"]["upstreamVersions"]["versions"][str(version)] = {"classification": "supported"}
        with open(sys.argv[1], "w") as fp:
            try:
                yaml.dump(values, fp, default_flow_style=False)
            except yaml.YAMLError as exc:
                print(exc)
    except yaml.YAMLError as exc:
        print(exc)

# Write Chart.yaml
with open(sys.argv[2], "r") as stream:
    try:
        chart_yaml = yaml.safe_load(stream)
        chart_version = semver.VersionInfo.parse(chart_yaml["version"])
        if version_step == 1:
            chart_version = chart_version.bump_patch()
        elif version_step == 2:
            chart_version = chart_version.bump_minor()
        chart_yaml["version"] = str(chart_version)
        with open(sys.argv[2], "w") as fp:
            try:
                yaml.dump(chart_yaml, fp, default_flow_style=False)
            except yaml.YAMLError as exc:
                print(exc)
    except yaml.YAMLError as exc:
        print(exc)

