# Little script to fetch current k8s versions for cloudprofile
#
# Usage: Set github token as env variable GITHUB_TOKEN and values.yaml file as first parameter
# and Chart.yaml as second parameter
#
# Example GITHUB_TOKEN=pat_blabla python get-k8s-versions.py Chart.yaml values.yaml

from github import Github
import semver
import sys
import ruamel.yaml as yaml
import os

versions_pot = {}

g = Github(os.getenv("GITHUB_TOKEN"))
old_versions = []
with open(sys.argv[1], "r") as stream:
    try:
        values = yaml.safe_load(stream)
        for version in list(values["global"]["kubernetes"]["upstreamVersions"]["versions"].keys()):
            old_versions.append(semver.VersionInfo.parse(version))
            versions_pot[version] = "deprecated"
    except yaml.YAMLError as exc:
        print(exc)
        exit(1)
old_versions.sort() # newest version will be last in list (index -1)


minor_old0 = semver.VersionInfo(1, old_versions[-1].minor - 0, 0, "incomplete")
minor_old1 = semver.VersionInfo(1, old_versions[-1].minor - 1, 0, "incomplete")
minor_old2 = semver.VersionInfo(1, old_versions[-1].minor - 2, 0, "incomplete")
minor_old3 = semver.VersionInfo(1, old_versions[-1].minor - 3, 0, "incomplete")

new_versions = []

for release in g.get_repo("kubernetes/kubernetes").get_releases():
    semver_release = semver.VersionInfo.parse(release.tag_name[1:]) # again, cut the hopefully leading v
    if semver_release.prerelease is not None:
        continue
    if semver_release.build is not None:
        continue
    if minor_old0.prerelease == "incomplete" and semver_release.minor == minor_old0.minor:
        minor_old0 = minor_old0.replace(prerelease=None)
        minor_old0 = minor_old0.replace(patch = semver_release.patch)
        new_versions.append(minor_old0)
        continue
    if minor_old1.prerelease == "incomplete" and semver_release.minor == minor_old1.minor:
        minor_old1 = minor_old1.replace(prerelease=None)
        minor_old1 = minor_old1.replace(patch = semver_release.patch)
        new_versions.append(minor_old1)
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
    if minor_old0.prerelease is None and minor_old1.prerelease is None and  minor_old2.prerelease is None and  minor_old3.prerelease is None:
        break


if len(new_versions) != 4:
    print("Error, expecting exactly 4 supported kubernetes versions.")
    exit(1)

# Version step is 0 if no version bump happens at all, it is 1 if only patch versions increase
# it is 2 if at least one minor version bump took place
version_step = 0

# Assuming major is always 1:
# lets check if a patch update took place
for newversion in new_versions:
    if str(newversion) not in versions_pot:
        print("patch update: ", str(newversion))
        version_step = 1
    versions_pot[str(newversion)] = "supported"


if version_step == 0:
    # All done
    exit(0)

# Write values.yaml
with open(sys.argv[1], "r") as stream:
    try:
        values = yaml.safe_load(stream)
        values["global"]["kubernetes"]["upstreamVersions"]["versions"].clear()
        for version in versions_pot:
            values["global"]["kubernetes"]["upstreamVersions"]["versions"][version] = {"classification": versions_pot[version]}
        with open(sys.argv[1], "w") as fp:
            try:
                yaml.dump(values, fp, default_flow_style=False)
            except yaml.YAMLError as exc:
                print(exc)
                exit(1)
    except yaml.YAMLError as exc:
        print(exc)
        exit(1)

# Write Chart.yaml
with open(sys.argv[2], "r") as stream:
    try:
        chart_yaml = yaml.safe_load(stream)
        chart_version = semver.VersionInfo.parse(chart_yaml["version"])
        if version_step == 1:
            chart_version = chart_version.bump_patch()
        chart_yaml["version"] = str(chart_version)
        with open(sys.argv[2], "w") as fp:
            try:
                yaml.dump(chart_yaml, fp, default_flow_style=False)
            except yaml.YAMLError as exc:
                print(exc)
                exit(1)
    except yaml.YAMLError as exc:
        print(exc)
        exit(1)

