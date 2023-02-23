# git-deployer

Python script to deploy from a git repository to a local directory.  Deseigned to be placed on a webserver, to deploy a web app.

## Usage (WIP)
1. Place DEPLOY.py on destination web server.
2. Create deployment config(s) in configs/ (under DEPLOYdir, from "config__APPENVNAME.json" example. (See "configs" section below.)
3. Configure git credentials so "git" command can be run non-interactively.
    - ".git-credentials" method - [link1](https://git-scm.com/docs/git-credential-store), [link2](https://git-scm.com/docs/gitcredentials), [link3](https://techexpertise.medium.com/storing-git-credentials-with-git-credential-helper-33d22a6b5ce7) - `git config --global credential.helper store`
    - For GitHub, access token is pw. (Settings > Developer settings > Personal Access Token > Tokens (classic)).
4. Execute:
    - `python DEPLOY.py` or `python DEPLOY.py --status` - list available (configured) deployables
    - Deploy latest commit: `python DEPLOY.py APPENVNAME`
    - Deploy specific commit `python DEPLOY.py --hash SHORTCOMMITHASH APPENVNAME`
    - (Script will prompt user to execute again with an additional check parameter to confirm deployment.)


## App/environment configs
- Create deployment config in configs/ dir, with format "config__APPENVNAME.json".  Config properties:
    - "gitCmd" (deprecated,optional): array of command args to run a local git commnand.  Examples... ["git"], ["sudo", "-u", "otheruser", "git"].  Defaults to ["git"].
    - "cloneUrl": (optional) Will clone this git repository if a local repo doesn't exist.
    - "buildCmd_successCode": (optional) Deployment will be canceled if createBuildCmd return code != 0 (default).  Supply a different value if createBuildCmd returns a less-standard code to indicate success.  (e.g. Robocopy on Windows success return code is 1.)

    - "repoDir": path to local project repository root. Can be a relative path (relative to DEPLOY.py), or absolute path.
    - "branchName": git branch to checkout/deploy.
    - "createBuildCmd": custom create-a-build command (string), to be executed with python subprocess.call().  Must reference environment variable "BUILD_TEMP_DIR", and create a build there (Linux:`$BUILD_TEMP_DIR`, Windows:`%BUILD_TEMP_DIR%`).
        - Executed from cwd=REPO_DIR.
        - To run multiple commands, insert multiple commands on [one line](https://stackoverflow.com/q/8055371).
        - Examples:
            1. To just copy files from e.g. repoDir/source, `"cp -r source/$BUILD_TEMP_DIR"`.
            2. App has custom build cmd "repoDir/buildMe.py" that takes destination dir as an argument. `"python buildme.py $BUILD_TEMP_DIR"`.
            3. App has custom build cmd "repoDir/buildMe.py" that creates build in hardcoded destination dir "repoDir/mybuild". `"python buildMe.py ; cp -r mybuild/ $BUILD_TEMP_DIR"`.
        - Notes/quirks on commands for copying dirs:
            - Note (rsync command): formats can be confusing, see https://stackoverflow.com/a/20301093. (ex: `"rsync -a /source/path/"`, `["rsync", "-a", "/source/path/"]`)
            - Note (cp command): "*" in cp source path is a shell thing, not a command arg thing. [citation needed].
            - Note: in Windows, "copy" command doesn't seem to work.  Try xcopy, robocopy.

    - "deployToDir": final deploy destination on the server.
