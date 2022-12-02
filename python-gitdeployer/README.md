# git-deployer

Python script to deploy from a git repository to a local directory.  Deseigned to be placed on a webserver, to deploy a web app.

## Usage (WIP)
1. Place git-deployer directory at destination/web server.
2. Create deployment config(s) in configs/ dir, from "config__REPONAME__ENVNAME.json" example. (See "configs" section below.)
3. Configure git credentials so "git" command can be run non-interactively.
    - ".git-credentials" method - https://git-scm.com/docs/git-credential-store, https://git-scm.com/docs/gitcredentials, https://techexpertise.medium.com/storing-git-credentials-with-git-credential-helper-33d22a6b5ce7 - `git config --global credential.helper store`
    - For GitHub, access token is pw. (Settings > Developer settings > Personal Access Token > Tokens (classic)).
4. Run with `python DEPLOY.py APPNAME ENVNAME` (deploys latest commit)
    - Deploy arbitrary commit: `python DEPLOY.py --hash COMMITHASH APPNAME ENVNAME`
    - (Script will prompt user to execute again with an additional check parameter to confirm deployment.)

## App/environment configs
- Create deployment config in configs/ dir, with format "config__APPNAME__ENVNAME.json".  APPNAME & ENVNAME are technically arbitrary strings that indicate and app/environment [e.g. "PROD", "DEV", ...] to deploy.  Config top-level properies:
    - "gitCmd" (optional): array of command args to run a local git commnand.  Examples... ["git"], ["sudo", "-u", "otheruser", "git"].  Defaults to ["git"].
    - "repoDir": (optional) relative (to DEPLOY.py) or absolute path to local project repository.  (Will "git clone" into this dir if it doesn't yet exist.)  Defaults to: "repos/APPNAME"
    - "cloneUrl": (optional) Will clone this git repository if a local repo doesn't exist.

    - "branchName": git branch to checkout/deploy.
    - "createBuildCmd": array of command args to create a build (cwd relative to repoDir).  Build destination dir will be appended as to the arg array.
        - Examples: can be a build script defined in the project ["python", "buildMe/buildme.py"], or as simple as copying files from a project subdirectory ["rsync", "-a", "source/"] (see https://stackoverflow.com/q/20300971).  (Note, in either case, destination dir is appended as final parameter, and command must place a build there.)
    - "deployToDir": final deploy destination.
