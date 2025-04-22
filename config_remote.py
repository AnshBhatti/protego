###
### config_remote.py - configuration for remote servers
###

# NODES = [
#     "hp021.utah.cloudlab.us",
#     "hp004.utah.cloudlab.us",
#     "hp079.utah.cloudlab.us",
#     "hp125.utah.cloudlab.us",
#     "hp146.utah.cloudlab.us",
#     "hp042.utah.cloudlab.us",
#     "hp138.utah.cloudlab.us",
#     "hp123.utah.cloudlab.us",
#     "hp023.utah.cloudlab.us",
#     "hp102.utah.cloudlab.us",
#     "hp040.utah.cloudlab.us"
# ]
NODES = ["hp113.utah.cloudlab.us", 
         "hp114.utah.cloudlab.us", 
         "hp038.utah.cloudlab.us", 
         "hp107.utah.cloudlab.us", 
         "hp023.utah.cloudlab.us", 
         "hp101.utah.cloudlab.us", 
         "hp079.utah.cloudlab.us", 
         "hp004.utah.cloudlab.us", 
         "hp040.utah.cloudlab.us", 
         "hp021.utah.cloudlab.us", 
         "hp102.utah.cloudlab.us"
         ]

# "hp024.utah.cloudlab.us" seems to be the issue? And has been before I think?

# Public domain or IP of server
SERVERS = NODES[0:1]
# Public domain or IP of intemediate
INTNODES = []
# Public domain or IP of client and agents
CLIENTS = NODES[1:]
# Public domain or IP of client
CLIENT = CLIENTS[0]
AGENTS = CLIENTS[1:]

# Public domain or IP of monitor
MONITOR = ""

# Username and SSH credential location to access
# the server, client, and agents via public IP
USERNAME = "ylai"
# KEY_LOCATION = "/home/eric/.ssh/id_rsa"        # using my cloudlab account but eric's ssh, might be clapped
KEY_LOCATION = "/home/eric/.ssh/cloudlab_ylai_rsa"
# Location of Shenango to be installed. With "", Shenango
# will be installed in the home direcotry
ARTIFACT_PARENT = ""

# Network RTT between client and server (in us)
# since I redefined this in the run scripts, I don't think this actually applies?
NET_RTT = 10

KERNEL_NAME = "caladan"

### End of config ###

ARTIFACT_PATH = ARTIFACT_PARENT
if ARTIFACT_PATH != "":
    ARTIFACT_PATH += "/"
ARTIFACT_PATH += "bw_caladan"

PARAM_EXP_FLAG = False
