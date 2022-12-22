# DEPLOY.py - v1.0.10
# - Desc: Script to make deployments from Virtualmin server prompt interface
#
#
# Devnote:
# - Virtualmin commandline interface doesn't do interactive shells.  Process has to finish, and can't ask for user input.
# - "Cannot establish connection to the host." means running in non-interactive shell (e.g. Webmin), and script or subprocess (e.g. git) is requiring user input.
# 
# TODO:
# - Maybe change appName/envName to just deployName?
#   - (do what with: app1.dev.domain.net?)
# - Make log be 1-deploy-per-line
# - Add "--status" that lists deployables + last-deployed.

import os, sys, getopt
import subprocess
import datetime
import tempfile
import json

import utils1


def PrintAndQuit(msg):
	print(msg)
	quit()

# Append an arg or args to existing command.
# - cmdOrArgs can be a string (like "rsync -a /source/path/") or arg array (like ["rsync", "-a", "/source/path/"]).
def cmdAppendArg(cmdOrArgs, appendArg, prequoted=False):
	if not isinstance(appendArg, str):
		PrintAndQuit("If appendArg must be a string.")
	if isinstance(cmdOrArgs, list):
		#if not isinstance(appendArg, list):
		#	PrintAndQuit("If cmdOrArgs is a list, appendArg(s) must be a list.")
		output = cmdOrArgs + [appendArg]
	elif isinstance(cmdOrArgs, str):
		output = cmdOrArgs + " " + ('"' + appendArg.replace('"', '\\"') + '"')
	else:
		PrintAndQuit("Unsupported cmdOrArgs type.  Must be a string or list.")
	return output


def Subprocess_run2(cmdOrArgs, cwd=None, hideOutput=False):
	# Quirks/notes:
	# - Virtualmin commandline interface doesn't do interactive shells.  subprocess.run() with shell=True output doesn't appear, and process has to finish.  Can't require user input.
	# - Behaves always like check=True, since we error/halt on returncode!=0.
	# - capture_output must be True, to do halt-on-error stuff.
	# - capture_output=True seems to cause the "Cannot establish connection to the host" error in Virtualmin.  Per https://docs.python.org/3/library/subprocess.html, "If you wish to capture and combine both streams into one, use stdout=PIPE and stderr=STDOUT instead of capture_output."
	# - On cmdOrArgs format and shell=True|False - https://stackoverflow.com/a/15109975
	#     - tl;dr if cmd(str), shell must be True; if args, shell must be False.
	
	#print("cmdStr: " + str(cmdStr))
	#print("* cmd: " + " ".join(cmdOrArgs))
	#cp = subprocess.run(cmdOrArgs, capture_output=True, shell=False, cwd=cwd)
	shell = False if isinstance(cmdOrArgs, list) else True
	try:
		cp = subprocess.run(cmdOrArgs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell, cwd=cwd)
	except Exception as exn: # Happens in windows "copy filename_DNE src dst".
		print("***Subprocess threw exception:")
		print("- cmd: " + str(cmdOrArgs) + "\n- (wd: " + cwd + ") \n- " + str(exn))
		quit()

	if cp.returncode != 0:
		print("***Process returned non-zero returncode '" + str(cp.returncode) + "':")
		print("* cmd: " + str(cmdOrArgs) + "\n- (wd: " + cwd + ")")
		print('* exit status:', cp.returncode)
		print('* stdout+stderr:', cp.stdout.decode())
		#quit() # Cannot quit here e.g. Robocopy success return code is 1, ugh.  Downstream check for empty destination dir will handle issues here.
	else:
		if not hideOutput:
			if cp.stdout.decode():
				print(cp.stdout.decode().strip())
	return cp

#def CloneRepo(gitCmd, repoUrl, repoDir):
#    Subprocess_run2(gitCmd + ["clone", cloneUrl, repoUrl, repoName], cwd=(reposDir))
	
def PullCheckoutRepo(gitCmd, repoDir, branchName, cloneUrl):
	# Create dir & clone repo if DNE...
	if not os.path.isdir(repoDir):
		print("Repo dir '" + repoDir + "' DNE; attempting repo clone...")
		if not cloneUrl:
			PrintAndQuit("Error, repoDir DNE and cloneUrl unspecified.")
		if not os.path.isdir(os.path.realpath(repoDir + "/..")):
			PrintAndQuit("Error, repo parent dir missing. (\"" + os.path.realpath(repoDir + "/..") + "\")")

		Subprocess_run2(gitCmd + ["clone", cloneUrl, repoDir], cwd=(selfDir))

	if not os.path.isdir(repoDir + "/.git/"):
		PrintAndQuit("Error: repo dir \"" + repoDir + "\" does not appear to be a git repository.")

	# If on detached head from a previous hash-deployment, get back on the branch.
	# Required for subsequent pull if not yet on a branch.
	Subprocess_run2(gitCmd + ["checkout", branchName], cwd=(repoDir))

	Subprocess_run2(gitCmd + ["pull"], cwd=(repoDir))


def CheckoutHash(gitCmd, repoDir, commitHash):
	Subprocess_run2(gitCmd + ["checkout", commitHash], cwd=(repoDir))

def GitHash(gitCmd, repoDir):
	# Pretty format placeholders https://devhints.io/git-log-format
	cp = Subprocess_run2(gitCmd + ["log", "--pretty=%H", "-n", "1"], cwd=(repoDir), hideOutput=True)
	return cp.stdout.decode().strip()

def GitDateIso(gitCmd, repoDir):
	# Pretty format placeholders https://devhints.io/git-log-format
	cp = Subprocess_run2(gitCmd + ["log", "--pretty=%ci", "-n", "1"], cwd=(repoDir), hideOutput=True)
	return cp.stdout.decode().strip()

def GitCommitSubject(gitCmd, repoDir):
	# Pretty format placeholders https://devhints.io/git-log-format
	cp = Subprocess_run2(gitCmd + ["log", "--pretty=%s", "-n", "1"], cwd=(repoDir), hideOutput=True)
	return cp.stdout.decode().strip()


def DeployApp(appName, envName, commitHash, checkSum):
	if not appName or not envName:
		PrintAndQuit("Error: missing appName or envName. (" + str(appName) + " / " + str(envName) + ")")

	# Load config-xxx.json file
	configPath = configsDir + "/config__" + appName + "__" + envName + ".json"
	if not os.path.exists(configPath):
		PrintAndQuit("Error: config file " + configPath + " does not exist.")
	with open(configPath, 'r') as f:
		config1 = json.load(f)

	if "repoDir" not in config1:
		PrintAndQuit("Error: repoDir not found in config.")
	if "branchName" not in config1:
		PrintAndQuit("Error: branchName not found in config.")
	if "deployToDir" not in config1:
		PrintAndQuit("Error: deployToDir not found in config.")
	if "createBuildCmd" not in config1:
		PrintAndQuit("Error: createBuildCmd missing.")
	# TODO: require createBuildCmd is a string or array of strings.

	branchName = config1["branchName"]
	createBuildCmd = config1["createBuildCmd"]
	deployToDir = config1["deployToDir"]
	cloneUrl = config1["cloneUrl"]
	gitCmd = config1["gitCmd"] if "gitCmd" in config1 else ["git"]
	repoDir = os.path.normpath(config1["repoDir"])

	# Pull,checkout latest version from git repo.
	print("Pull/checkout latest version from repo...")
	PullCheckoutRepo(gitCmd, repoDir, branchName, cloneUrl)
	if commitHash:
		CheckoutHash(gitCmd, repoDir, commitHash)

	# Interrogate latest commit info.
	hash = GitHash(gitCmd, repoDir)
	gitSubject = GitCommitSubject(gitCmd, repoDir)
	gitDateIso1 = GitDateIso(gitCmd, repoDir)
	gitDate = datetime.datetime.strptime(gitDateIso1, '%Y-%m-%d %H:%M:%S %z')
	gitDateIso2 = gitDate.isoformat()
	print("")
	print("Project/app '" + appName + "' last commit:")
	print("- CommitMsg: \"" + gitSubject + "\"")
	print("- Date: " + gitDateIso2)
	print("- Hash: " + hash)
	# TODO: warn if age of last commit is > a few days old.?

	print("")
	#print("DEPLOY the above commit to \"" + deployToDir + "\"?")
	#answer = input("Type hash[0:3] to deploy... ")
	#if answer.lower() != hash[0:3]:
	#    PrintAndQuit("Deploy cancelled.")
	if (checkSum != hash[0:3] and checkSum != "NOCHECK"):
		print("To deploy this commit, call again with additional hash.left(3) argument.")
		quit()

	# Create build, per project build command, passing tempDir as first partameter (build destination, by convention).
	tempDir = tempfile.TemporaryDirectory()
	buildDir = tempDir.name
	print("Creating build in \"" + buildDir + "\"...")
	Subprocess_run2(cmdAppendArg(createBuildCmd, buildDir), cwd=repoDir)

	# Sanity-check that createBuildCmd actually populated the build dir.
	if not os.path.isdir(buildDir) or len(os.listdir(buildDir)) == 0:
		PrintAndQuit("Build dir DNE is is empty (" + buildDir + ")!")

	# DEPLOY to live deployDir, form temporary build dir.
	print("")
	print("* DEPLOYING build to deployDir \"" + deployToDir + "\"...")
	utils1.copyContentsIntoExisting(buildDir, deployToDir)

	# Log the deployment.
	# If log file DNE, create.
	timeNowIso = datetime.datetime.now().replace(microsecond=0).isoformat()
	logFilePath = logsDir + "/" + appName + "__" + envName + ".log"
	with open (logFilePath, "a+") as file1:
		file1.write(timeNowIso + " - Deployed \"" + appName + "\" to " + envName + "\n")
		file1.write("\t- Commit: " + gitDateIso2 + " / " + hash + "\n")
	print("* Deployment logged in \"" + logsDir + "\"")

	print("Deploy complete!")



# Require Python 3+.
if sys.version_info[0] < 3:
	PrintAndQuit("Must be run with Python 3+")

#selfDir = os.path.dirname(sys.argv[0]) + "/"
selfDir = (os.path.dirname(__file__) if os.path.dirname(__file__) else ".") # "if" for linux, where __file__ is relative.
logsDir = os.path.normpath(selfDir + "/logs") # No reason for normapth().
configsDir = os.path.normpath(selfDir + "/configs")
#print("selfDir3: " + selfDir)

# Check for required dirs.
if not os.path.isdir(configsDir):
	PrintAndQuit("Error, required configs/ dirs missing.")
#if not os.path.isdir(reposDir):
#	os.makedirs(reposDir)
if not os.path.isdir(logsDir):
	os.makedirs(logsDir)

# When run directly.
if __name__ == "__main__":
	#buildsDir = selfDir + "/../builds/"
	#buildIdStr = "litapp2"

	appName = "example-app"
	envName = "DEV"
	commitHash = ""
	checkSum = ""
	nocheck = False
	try:
		opts, args = getopt.getopt(sys.argv[1:], "", ["help", "hash=", "nocheck"])
	except getopt.GetoptError as err:
		# print help information and exit:
		print("getopt error: " + str(err))  # will print something like "option -a not recognized"
		#getopt.getopt.usage()
		sys.exit(2)
	for o, a in opts:
		if o in ("-s", "--hash"):
			commitHash = a
		elif o == "--nocheck":
			checkSum = "NOCHECK"
		else:
			print("opts error.") #assert False, "unhandled option"
	if len(args) > 0:
		appName = args[0]
	if len(args) > 1:
		envName = args[1]
	if len(args) > 2:
		checkSum = args[2]

	DeployApp(appName, envName, commitHash, checkSum)

