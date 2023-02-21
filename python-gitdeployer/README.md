# git-deployer

Python script to deploy from a git repository to a local directory.  Deseigned to be placed on a webserver, to deploy a web app.

## Usage (WIP)
1. Place git-deployer directory at destination/web server.
2. Create deployment config(s) in configs/ dir, from "config__APPENVNAME.json" example. (See "configs" section below.)
3. Configure git credentials so "git" command can be run non-interactively.
    - ".git-credentials" method - https://git-scm.com/docs/git-credential-store, https://git-scm.com/docs/gitcredentials, https://techexpertise.medium.com/storing-git-credentials-with-git-credential-helper-33d22a6b5ce7 - `git config --global credential.helper store`
    - For GitHub, access token is pw. (Settings > Developer settings > Personal Access Token > Tokens (classic)).
4. Execute:
    - `python DEPLOY.py` or `python DEPLOY.py --status` - list available (configured) deployables
    - Deploy latest commit: `python DEPLOY.py APPENVNAME`
    - Deploy specific commit `python DEPLOY.py --hash SHORTCOMMITHASH APPENVNAME`
    - (Script will prompt user to execute again with an additional check parameter to confirm deployment.)


## App/environment configs
- Create deployment config in configs/ dir, with format "config__APPNAME__ENVNAME.json".  APPNAME & ENVNAME are technically arbitrary strings that indicate and app/environment [e.g. "PROD", "DEV", ...] to deploy.  Config top-level properies:
    - "gitCmd" (deprecated,optional): array of command args to run a local git commnand.  Examples... ["git"], ["sudo", "-u", "otheruser", "git"].  Defaults to ["git"].
    - "cloneUrl": (optional) Will clone this git repository if a local repo doesn't exist.

    - "repoDir": path to local project repository root. Can be a relative path (relative to DEPLOY.py), or absolute path.
    - "branchName": git branch to checkout/deploy.
    - "createBuildCmd": a command string (like "rsync -a /source/path/") or array of command args (like ["rsync", "-a", "/source/path/"]) that creates a build.   (cwd/paths relative to repoDir).
        - Build destination dir will be appended to createBuildCmd as a final command argument.
        - Examples: can be a build script defined in the project ["python", "buildMe/buildme.py"], or as simple as copying files from a project subdirectory ["rsync", "-a", "source/path/"] (see https://stackoverflow.com/q/20300971).  (Note, in either case, destination dir is appended as final parameter, and command must create a build in that location.)
            - Note (rsync command): formats can be confusing, see https://stackoverflow.com/a/20301093.
            - Note (cp command): "*" in cp source path is a shell thing, not a command arg thing. [link needed].
            - Note: in Windows, "copy" command doesn't seem to work.  Try xcopy, robocopy.
    - "deployToDir": final deploy destination on the server.
