import sys, neuro3d, semver

print(len(sys.argv), len(sys.argv[0]), len(sys.argv[1]), len(sys.argv[2]))
semver.VersionInfo(neuro3d.__version__)
