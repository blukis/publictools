# Release Notes

### 1.3.3 (2023-07-15)
* Output, wording, formatting changes
* Support experimental "--printlogexp" option

### 1.3.2 (2023-02-23)
* Calling with no parameters now outputs status;
* Support --help, --version; deprecating --list;
* Support executing from different cwd.;
* BREAKING: Made createBuildCmd take/require BUILD_TEMP_DIR env variable;
* support buildCmd_successCode, Subprocess_run2() quits in unexpected returncode.
* cloneURL now properly optional.
* fixed config paths, support "~/" paths; minor output fix

### 1.2.0 (2022-12-22)
* Added --list argument, to list deployable configurations.
* Removed utils1.py, making DEPLOY.py a single-file script.

### 1.1.0 (2022-12-22)
* appName, envName replaced by single appEnvName.  DEPLOY.py command now takes one fewer parameter.
* log files now one-line-per-deployment.

### 1.0.10 (2022-12-22)
* "repoDir" config value is now "required". (Formerly optional, default based on appName.)

### 1.0.9 (2022-12-22)
* Start
