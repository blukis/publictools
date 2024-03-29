# DEPLOY.py - v1.3.3 - https://github.com/blukis/publictools/blob/main/python-gitdeployer/
VERSION = "1.3.3"
HOME_URL = "https://github.com/blukis/publictools/blob/main/python-gitdeployer/"
# - Desc: Script to make deployments from Virtualmin server prompt interface
#
#
# Devnote:
# - Virtualmin commandline interface doesn't do interactive shells.  Process has to finish, and can't ask for user input.
# - "Cannot establish connection to the host." means running in non-interactive shell (e.g. Webmin), and script or subprocess (e.g. git) is requiring user input.
# 
# TODO:
# - 

import os, sys, getopt
import subprocess
import datetime
import tempfile
import json
import shutil, distutils.dir_util

#import utils1

class utils1:
	@staticmethod
	def copyContentsIntoExisting(srcDir, dstDir):
		if not os.path.isdir(srcDir):
			raise Exception("CopyContentsInto src is not a dir! (" + srcDir + ")")
		if not os.path.isdir(dstDir):
			raise Exception("CopyContentsInto dst is not a dir! (" + dstDir + ")")
		distutils.dir_util.copy_tree(srcDir, dstDir)

def PrintAndQuit(msg):
	print(msg)
	quit()

# Append an arg or args to existing command.
# - cmdOrArgs can be a string (like "rsync -a /source/path/") or arg array (like ["rsync", "-a", "/source/path/"]).
#def cmdAppendArg(cmdOrArgs, appendArg, prequoted=False):
#	if not isinstance(appendArg, str):
#		PrintAndQuit("If appendArg must be a string.")
#	if isinstance(cmdOrArgs, list):
#		#if not isinstance(appendArg, list):
#		#	PrintAndQuit("If cmdOrArgs is a list, appendArg(s) must be a list.")
#		output = cmdOrArgs + [appendArg]
#	elif isinstance(cmdOrArgs, str):
#		output = cmdOrArgs + " " + ('"' + appendArg.replace('"', '\\"') + '"')
#	else:
#		PrintAndQuit("Unsupported cmdOrArgs type.  Must be a string or list.")
#	return output


def Subprocess_run2(cmdOrArgs, cwd=None, hideOutput=False, addEnvs={}, expectedRC=None):
	# Quirks/notes:
	# - Virtualmin commandline interface doesn't do interactive shells.  subprocess.run() with shell=True output doesn't appear, and process has to finish.  Can't require user input.
	# - Behaves always like check=True, since we error/halt on returncode!=0.
	# - capture_output must be True, to do halt-on-error stuff.
	# - capture_output=True seems to cause the "Cannot establish connection to the host" error in Virtualmin.  Per https://docs.python.org/3/library/subprocess.html, "If you wish to capture and combine both streams into one, use stdout=PIPE and stderr=STDOUT instead of capture_output."
	# - On cmdOrArgs format and shell=True|False - https://stackoverflow.com/a/15109975
	#     - i.e. if cmd is str, shell must be True; if args, shell must be False.
	
	shell = False if isinstance(cmdOrArgs, list) else True
	
	my_env = None
	if addEnvs:
		my_env = os.environ.copy()
		my_env.update(addEnvs)
	try:
		cp = subprocess.run(cmdOrArgs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell, cwd=cwd, env=my_env)
	except Exception as exn: # Happens in windows "copy filename_DNE src dst".
		print("***Subprocess threw exception:")
		print("- cmd: " + str(cmdOrArgs) + "\n- (cwd: " + cwd + ") \n- " + str(exn))
		quit()

	# If expectedCode is a num && returnCode is different, print error.
	successRC = expectedRC if expectedRC is not None else 0
	#print("expectedRC:" + str(type(expectedRC)))
	#print("cp.returncode:" + str(type(cp.returncode)))
	if int(cp.returncode) != int(successRC):
		print("***Process returned unexpected returncode '" + str(cp.returncode) + "' (expected " + str(successRC) + ")...")
		print("* cmd: " + str(cmdOrArgs) + "\n- (cwd: " + cwd + ")")
		print('* returnCode:', cp.returncode)
		print('* stdout+stderr:', cp.stdout.decode())
		# Cannot quit here, too many edge cases. e.g. Robocopy success return code is 1, ugh.  Downstream check for empty destination dir will handle issues here.
		# Update: Quit out of caution.  Use expectedRC param to bypass.
		quit()
	else:
		if not hideOutput:
			if cp.stdout.decode():
				print(cp.stdout.decode().strip())
	return cp

#def CloneGitRepo(gitCmd, repoUrl, repoDir):
#    Subprocess_run2(gitCmd + ["clone", cloneUrl, repoUrl, repoName], cwd=(reposDir))
	
def PullCheckoutGitRepo(gitCmd, repoDir, branchName, cloneUrl):
	# Create dir & clone repo if DNE...
	if not os.path.isdir(repoDir):
		print("Repo dir '" + repoDir + "' DNE; attempting repo clone...")
		if not cloneUrl:
			PrintAndQuit("Error, repoDir DNE and cloneUrl unspecified.")
		if not os.path.isdir(os.path.realpath(repoDir + "/..")):
			PrintAndQuit("Error, repo parent dir missing (\"" + os.path.realpath(repoDir + "/..") + "\").  Create it, and run again.")

		Subprocess_run2(gitCmd + ["clone", cloneUrl, repoDir], cwd=(selfDir))

	if not os.path.isdir(repoDir + "/.git/"):
		PrintAndQuit("Error: repo dir \"" + repoDir + "\" does not appear to be a git repository.")

	# If on detached head from a previous hash-deployment, get back on the branch.
	# Required for subsequent pull if not yet on a branch.
	Subprocess_run2(gitCmd + ["checkout", branchName], cwd=(repoDir))

	Subprocess_run2(gitCmd + ["pull"], cwd=(repoDir))


def CheckoutGitHash(gitCmd, repoDir, commitHash):
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

def CommitVerStr(gitDate, gitHash): # Str to represent deployed ver e.g. "20230101_1a2b3c4d"
	commitVerStr = gitHash[0:8] + "(" + datetime.datetime.strftime(gitDate, '%Y%m%d') + ")"
	return commitVerStr

def LoadLastDeployedObj(appName):
	with open(lastDeploysFile) as file:
		ldObj = json.load(file)
	return ldObj[appName] if appName in ldObj else {}

def LoadLastDeployedVer(appName):
	aldObj = LoadLastDeployedObj(appName)
	return aldObj["commitVerStr"] if "commitVerStr" in aldObj else ""

def PrintLastNDeploys(appEnvName, n):
	appLogFile = logsDir + "/" + appEnvName + ".log"
	with open(appLogFile) as file:
		lines = file.readlines()
	lastN = lines[-n:]
	for line in lastN:
		print("  " + line.strip())


def ListDeployables():
	appEnvNames = []
	for filename in os.listdir(configsDir):
		if filename.startswith("config__") and filename.endswith(".json"):
			appEnv = filename[8:len(filename)-5]
			appEnvNames.append(appEnv)
	if not len(appEnvNames):
		print("No deployables configured.  Create 'config__xxxx.json' file in configs/.")
		return
	maxLen = len(max(appEnvNames, key=len)) # https://www.geeksforgeeks.org/python-longest-string-in-list/
	maxLen = max(maxLen, 13) # Ensure at least wide enough for headers.
	print("")
	print("DEPLOYABLE_NAME" + ("." * (maxLen-10)) + "LAST_DEPLOYMENT")
	for appEnv in appEnvNames:
		deployStr = LoadLastDeployedVer(appEnv)
		deployStr = deployStr if deployStr else "NO_DATA"
		print("* " + appEnv + ("." * (maxLen+3-len(appEnv))) + deployStr)
	#print("")

def DeployApp(appEnvName, commitHash, checkSum):
	if not appEnvName:
		PrintAndQuit("Error: missing appEnvName. (" + str(appEnvName) + ")")

	# Load config-xxx.json file
	#configPath = configsDir + "/config__" + appName + "__" + envName + ".json"
	configPath = configsDir + "/config__" + appEnvName + ".json"
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
	deployToDir = os.path.join(selfDir, os.path.expanduser(config1["deployToDir"])) # Rel paths not recommended, but would be rel to selfDir.
	cloneUrl = config1["cloneUrl"] if "cloneUrl" in config1 else None
	gitCmd = config1["gitCmd"] if "gitCmd" in config1 else ["git"]
	expectedRC = config1["buildCmd_successCode"] if "buildCmd_successCode" in config1 else None
	repoDir = os.path.join(selfDir, os.path.expanduser(config1["repoDir"])) # Note join() handles repoDir abs/rel well.

	# Pull,checkout latest version from git repo.
	print("Pull/checkout latest version from repo...")
	PullCheckoutGitRepo(gitCmd, repoDir, branchName, cloneUrl)
	if commitHash:
		CheckoutGitHash(gitCmd, repoDir, commitHash)

	# Interrogate latest commit info.
	gitHash = GitHash(gitCmd, repoDir)
	gitSubject = GitCommitSubject(gitCmd, repoDir)
	gitDateIso1 = GitDateIso(gitCmd, repoDir)
	gitDate = datetime.datetime.strptime(gitDateIso1, '%Y-%m-%d %H:%M:%S %z')
	gitDateIso2 = gitDate.isoformat()
	lastDeployObj = LoadLastDeployedObj(appEnvName)
	deployedTime = lastDeployObj["timeNowIso"] if "timeNowIso" in lastDeployObj else "??"
	print("")
	print("Last deployed ver: \"" + str(LoadLastDeployedVer(appEnvName)) + "\" - deployed at " + deployedTime)
	print("")
	print("Latest commit:")
	print("  - Commit-msg: \"" + gitSubject + "\"")
	print("  - Commit-date: " + gitDateIso1)
	print("  - Commit-hash: " + gitHash)
	# TODO: warn if age of last commit is > a few days old.?
	if printLog:
		print("")
		print("Recent deployments (10):")
		PrintLastNDeploys(appEnvName, 10)

	print("")
	#print("DEPLOY the above commit to \"" + deployToDir + "\"?") # Disabled: can't ask for user input, in non-interactive-shell environment (Webmin/Virtualmin).
	#answer = input("Type hash[0:3] to deploy... ")
	#if answer.lower() != hash[0:3]:
	#    PrintAndQuit("Deploy cancelled.")
	if (not checkSum):
		PrintAndQuit("To deploy latest commit, supply additional argument [1st-3-chars-of-hash].")
	if (checkSum != gitHash[0:3] and checkSum != "NOCHECK"):
		PrintAndQuit("hash.left(3) argument does not match current repo; aborting!")

	# Create build, per project build command, passing tempDir as first partameter (build destination, by convention).
	tempDir = tempfile.TemporaryDirectory()
	buildDir = tempDir.name
	print("Creating build in \"" + buildDir + "\"...")
	Subprocess_run2(createBuildCmd, addEnvs={"BUILD_TEMP_DIR": buildDir }, cwd=repoDir, expectedRC=expectedRC)

	# Sanity-check that createBuildCmd actually populated the build dir.
	if not os.path.isdir(buildDir) or len(os.listdir(buildDir)) == 0:
		PrintAndQuit("Build dir DNE is is empty (" + buildDir + "); aborting!")

	# DEPLOY to live deployDir, form temporary build dir.
	print("")
	print("* DEPLOYING build to deployDir \"" + deployToDir + "\"...")
	utils1.copyContentsIntoExisting(buildDir, deployToDir)

	# Log the deployment.
	# If log file DNE, create.
	timeNowIso = datetime.datetime.now().replace(microsecond=0).isoformat()
	#logFilePath = logsDir + "/" + appName + "__" + envName + ".log"
	logFilePath = logsDir + "/" + appEnvName + ".log"
	with open (logFilePath, "a+") as file1:
		commitVerStr = CommitVerStr(gitDate, gitHash)
		gitSubjShort = gitSubject[0:40] + ("..." if len(gitSubject) > 40 else "")
		logLine = timeNowIso + "\tdeploy\t" + commitVerStr + "\t\"" + gitSubjShort + "\""
		file1.write(logLine + "\n")
	print("* Deployment logged in \"" + os.path.relpath(logFilePath, start=selfDir) + "\"")

	# Log to lastDeploys file.
	with open(lastDeploysFile) as file:
		ldObj = json.load(file)
	ldObj.update({ appEnvName: { "lastLog": logLine, "timeNowIso": timeNowIso, "commitVerStr": commitVerStr, "gitSubjShort": gitSubjShort, "gitDate": str(gitDate), "gitHash": gitHash } })
	#ldObj.update({ appEnvName: { "lastLog": logLine } })
	with open(lastDeploysFile, 'w') as outfile:
		json.dump(ldObj, outfile)

	print("Deploy complete!")



# Require Python 3+.
if sys.version_info[0] < 3:
	PrintAndQuit("Must be run with Python 3+")

#selfDir = os.path.dirname(sys.argv[0]) + "/"
selfDir = os.path.abspath(os.path.dirname(__file__)) # abspath for linux where dirname(__file__) is relative path thus can be "".
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

lastDeploysFile = logsDir + "/_lastdeploys.json" # Init lastDeploys.
if not os.path.isfile(lastDeploysFile):
	with open(lastDeploysFile, 'w') as file:
		json.dump({}, file)

# When run directly.
if __name__ == "__main__":
	#buildsDir = selfDir + "/../builds/"
	#buildIdStr = "litapp2"

	appEnvName = ""
	commitHash = ""
	checkSum = ""
	nocheck = False
	execMode = ""
	printLog = False
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hv", ["hash=", "help", "nocheck", "skipcheck", "status", "printlogexp", "version"])
	except getopt.GetoptError as err:
		# print help information and exit:
		print("getopt error: " + str(err))  # will print something like "option -a not recognized"
		#getopt.getopt.usage()
		sys.exit(2)
	for o, a in opts:
		if o in ("-h", "--help"):
			execMode = "help"
		elif o in ("-v", "--version"):
			execMode = "version"
		elif o in ("--status"):
			execMode = "status"
		else:
			if o in ("-s", "--hash"):
				commitHash = a
			if o in ("--skipcheck", "--nocheck"): # bypass hash.left(3) check.
				checkSum = "NOCHECK"
			if o in ("--printlogexp"):
				printLog = True
		#else:
		#	print("opts error.") #assert False, "unhandled option"
	if len(args) > 0:
		appEnvName = args[0]
	if len(args) > 1:
		checkSum = args[1]

	if execMode == "help":
		print("Usage: DEPLOY.py [options] [deployablename] [hash3chrs]")
		print("")
		print("Options:")
		print("  -h, --help    Show this message")
		print("  -v, --version Output DEPLOY.py version only")
		print("  --hash=xxxx   Deploy a specific hash (default:latest).")
		print("  --skipcheck   Bypass hash.left(3) check.")
		print("  --printlogexp (experimental) output 10 recent deployments from log")
		print("")
		PrintAndQuit("To configure deployables, and more info, see " + HOME_URL)
	elif execMode == "version":
		PrintAndQuit(VERSION)
	elif execMode == "status" or (not appEnvName):
		if execMode != "status":
			print("DEPLOY.py version " + VERSION + " -- for options, `DEPLOY.py --help`")
			#print("Supply additional 'deployable_name' argrment. Configured deployables follow.")
			#print("For more options, `DEPLOY.py --help`")
		ListDeployables()
		print("")
		print("To make a deployment, supply additional argument [deployablename].")
	else:
		DeployApp(appEnvName, commitHash, checkSum)

