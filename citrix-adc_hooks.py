#!/usr/bin/python3
#Automates the certificate renewal process for Netscaler via REST API and dehydrated (https://github.com/lukas2511/dehydrated)
#USE AT OWN RISK

# speed up, because not evrey hook type need to be executed
import sys
whattodo = sys.argv[1]
if not (whattodo == "deploy_challenge" or whattodo == "deploy_cert" or whattodo == "clean_challenge"):
   exit(0) 

#Imports
import os, json, requests, base64, importlib
from urllib.parse import quote_plus
# disable cert warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# get config file path
cfgfile = os.environ['CONFIG']

# loader function for config file 
def import_path(path):
    module_name = os.path.basename(path).replace('-', '_')
    spec = importlib.util.spec_from_loader(
        module_name,
        importlib.machinery.SourceFileLoader(module_name, path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

# load config file
cfg = import_path(cfgfile)

# populate Variables
# (ToDo: replace variables in function calls to get rid of this definition)
nitroNSIP = cfg.nitroNSIP
nitroUser = cfg.nitroUser
nitroPass = cfg.nitroPass
connectiontype = cfg.connectiontype
nspairname = cfg.nspairname
nschainname = cfg.nschainname
nscert = cfg.nscert
nskey = cfg.nskey
nschain = cfg.nschain
nscertpath = cfg.nscertpath
nsrespact = cfg.nsrespact
nsresppol = cfg.nsresppol
nstimeout = cfg.nstimeout
stringmapname = cfg.stringmapname

def getAuthCookie(connectiontype,timeout,nitroNSIP,nitroUser,nitroPass):
   url = '%s://%s/nitro/v1/config/login' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/vnd.com.citrix.netscaler.login+json'}
   json_string = {
       "login":{
       "username":nitroUser,
       "password":nitroPass,
       }
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   cookie = response.cookies['NITRO_AUTH_TOKEN']
   nitroCookie = 'NITRO_AUTH_TOKEN=%s' % cookie
   return nitroCookie

def logOut(connectiontype,timeout,nitroNSIP,authToken):
   url = '%s://%s/nitro/v1/config/logout' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/vnd.com.citrix.netscaler.logout+json','Cookie': authToken}
   json_string = {
       "logout":{}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   #print ("LOGOUT: %s" % response.reason)
   return response

def SaveNSConfig(connectiontype,timeout,nitroNSIP,authToken):
   url = '%s://%s/nitro/v1/config/nsconfig?action=save' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   json_string = {
       "nsconfig":{}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: save configuration - %s" % (sys.argv[0], response.reason))
   return response

def sendFile(connectiontype,timeout,nitroNSIP,authToken,nscert,localcert,nscertpath):
   url = '%s://%s/nitro/v1/config/systemfile' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/vnd.com.citrix.netscaler.systemfile+json','Cookie': authToken}
   f = open(localcert, 'rb')
   filecontent = base64.b64encode(f.read()).decode('utf-8')
   json_string = {
   "systemfile": {
       "filename": nscert,
       "filelocation": nscertpath,
       "filecontent": filecontent,
       "fileencoding": "BASE64",}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: upload certfile %s - %s" % (sys.argv[0], nscert, response.reason))
   return response

def respPol(connectiontype,timeout,nitroNSIP,authToken,nsresppol,token_filename):
   url = '%s://%s/nitro/v1/config/responderpolicy' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   buildrule = 'HTTP.REQ.URL.CONTAINS(\"well-known/acme-challenge/%s\")' % token_filename
   json_string = {
   "responderpolicy": {
       "name": nsresppol,
       "rule": buildrule,}
   }
   payload = json.dumps(json_string)
   response = requests.put(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: edit responder policy - %s" % (sys.argv[0], response.reason))
   return response

def stringmapEntryCreate (connectiontype,timeout,nitroNSIP,authToken,stringmapname,token_filename,token_value):
   url = '%s://%s/nitro/v1/config/policystringmap_pattern_binding' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   map_key = '/.well-known/acme-challenge/%s' % token_filename
   json_string = {
   "policystringmap_pattern_binding": {
       "name": stringmapname,
       "key": map_key,
       "value": token_value}
   }
   payload = json.dumps(json_string)
   response = requests.put(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: add stringmap entry into %s - %s" % (sys.argv[0], stringmapname, response.reason))
   return response

def stringmapEntryRemove(connectiontype,timeout,nitroNSIP,authToken,stringmapname,token_filename):
   # encode stringmap arguments for using in URL
   map_key = quote_plus('/.well-known/acme-challenge/%s' % token_filename)
   url = '%s://%s/nitro/v1/config/policystringmap_pattern_binding/%s?args=key:%s' % (connectiontype, nitroNSIP, stringmapname, map_key)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   response = requests.delete(url, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: remove stringmap entry from %s - %s" % (sys.argv[0], stringmapname, response.reason))
   return response


def respAct(connectiontype,timeout,nitroNSIP,authToken,nsrespact,token_value):
   url = '%s://%s/nitro/v1/config/responderaction' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   buildtarget = "\"HTTP/1.0 200 OK\" +\"\\r\\n\\r\\n\" + \"%s\"" % token_value
   json_string = {
   "responderaction": {
       "name": nsrespact,
       "target": buildtarget,}
   }
   payload = json.dumps(json_string)
   response = requests.put(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: edit responder action - %s" % (sys.argv[0], response.reason))

def removeFile(connectiontype,timeout,nitroNSIP,authToken,nscert,nscertpath):
   url = '%s://%s/nitro/v1/config/systemfile/%s?args=filelocation:%%2Fnsconfig%%2Fssl' % (connectiontype, nitroNSIP, nscert)
   headers = {'Content-type': 'application/vnd.com.citrix.netscaler.systemfile+json','Cookie': authToken}
   response = requests.delete(url, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: delete cert file %s - %s" % (sys.argv[0], nscert, response.reason))
   return response

def getSSL(connectiontype,timeout,nitroNSIP,authToken, nspairname):
   url = '%s://%s/nitro/v1/config/sslcertkey/%s' % (connectiontype, nitroNSIP, nspairname)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   response = requests.get(url, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: check for existing cert %s on ADC - %s" % (sys.argv[0], nspairname, response.reason))
   return response

def updateSSL(connectiontype,timeout,nitroNSIP,authToken, nscert, nskey, nspairname):
   url = '%s://%s/nitro/v1/config/sslcertkey?action=update' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   json_string = {
   "sslcertkey": {
       "certkey": nspairname,
       "cert": nscert,
       "key": nskey,
       "nodomaincheck": True,}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: update SSL cert %s - %s" % (sys.argv[0], nspairname, response.reason))
   return response

def createSSL(connectiontype,timeout,nitroNSIP,authToken, nscert, nspairname, nskey):
   url = '%s://%s/nitro/v1/config/sslcertkey' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   json_string = {
   "sslcertkey": {
       "certkey": nspairname,
       "cert": nscert,
       "key": nskey,}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: create SSL certkeypair %s - %s" % (sys.argv[0], nspairname, response.reason))
   return response

def createSSLCA(connectiontype,timeout,nitroNSIP,authToken,nscert,nspairname):
   url = '%s://%s/nitro/v1/config/sslcertkey' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   json_string = {
   "sslcertkey": {
       "certkey": nspairname,
       "cert": nscert,}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: create CA cert - %s" % (sys.argv[0], response.reason))

def linkSSL(connectiontype,timeout,nitroNSIP,authToken, nschainname, nspairname):
   url = '%s://%s/nitro/v1/config/sslcertkey?action=link' % (connectiontype, nitroNSIP)
   headers = {'Content-type': 'application/json','Cookie': authToken}
   json_string = {
   "sslcertkey": {
       "certkey": nspairname,
       "linkcertkeyname": nschainname,}
   }
   payload = json.dumps(json_string)
   response = requests.post(url, data=payload, headers=headers, verify=False, timeout=timeout)
   print (" ++ Hook %s: link cert to CA - %s" % (sys.argv[0], response.reason))
   return response

### MAIN procedure ###
# check what hook is called
if whattodo == "deploy_cert":
   authToken = getAuthCookie(connectiontype,nstimeout,nitroNSIP,nitroUser,nitroPass)
   localcert = sys.argv[4]
   localkey = sys.argv[3]
   localchain = sys.argv[6]
   certexist = getSSL(connectiontype,nstimeout,nitroNSIP,authToken, nspairname)
   if certexist.status_code == 200:
      print (" ++ Updating Certificate on ADC")
      removeFile(connectiontype,nstimeout,nitroNSIP,authToken,nscert,nscertpath)
      removeFile(connectiontype,nstimeout,nitroNSIP,authToken,nskey,nscertpath)
      sendFile(connectiontype,nstimeout,nitroNSIP,authToken,nscert,localcert,nscertpath)
      sendFile(connectiontype,nstimeout,nitroNSIP,authToken,nskey,localkey,nscertpath)
      updateSSL(connectiontype,nstimeout,nitroNSIP,authToken, nscert, nskey, nspairname)
      SaveNSConfig(connectiontype,nstimeout,nitroNSIP,authToken)
   else:
      print (" ++ Create certificate on ADC")
      sendFile(connectiontype,nstimeout,nitroNSIP,authToken,nscert,localcert,nscertpath)
      sendFile(connectiontype,nstimeout,nitroNSIP,authToken,nskey,localkey,nscertpath)
      sendFile(connectiontype,nstimeout,nitroNSIP,authToken,nschain,localchain,nscertpath)
      createSSL(connectiontype,nstimeout,nitroNSIP,authToken, nscert, nspairname, nskey)
      createSSLCA(connectiontype,nstimeout,nitroNSIP,authToken, nschain, nschainname)
      linkSSL(connectiontype,nstimeout,nitroNSIP,authToken, nschainname, nspairname)
      SaveNSConfig(connectiontype,nstimeout,nitroNSIP,authToken)
   # logout after work
   logOut(connectiontype,nstimeout,nitroNSIP,authToken)
elif whattodo == "deploy_challenge":
   authToken = getAuthCookie(connectiontype,nstimeout,nitroNSIP,nitroUser,nitroPass)
   # with HOOK_CHAIN=yes, some more to do
   if False: #cfg.HOOK_CHAIN == "yes":
      list = sys.argv
      # Remove app name
      list.pop(0)
      # Remove whattodo
      list.pop(0)
      # iterate through list schema 'domain' 'token_name' 'token_value'
      while len(list) != 0:
         stringmapEntryCreate(connectiontype,nstimeout,nitroNSIP,authToken,stringmapname,list[1],list[2])
   else:
      token_filename = sys.argv[3]
      token_value = sys.argv[4]

   #respPol(connectiontype,nstimeout,nitroNSIP,authToken,nsresppol,token_filename)
   #respAct(connectiontype,nstimeout,nitroNSIP,authToken,nsrespact,token_value)
      stringmapEntryCreate(connectiontype,nstimeout,nitroNSIP,authToken,stringmapname,token_filename,token_value)
   # logout after work
   logOut(connectiontype,nstimeout,nitroNSIP,authToken)
elif whattodo == "clean_challenge":
   authToken = getAuthCookie(connectiontype,nstimeout,nitroNSIP,nitroUser,nitroPass)
   # more to do to enable config chain
   if False: # cfg.HOOK_CHAIN == "yes":
      list = sys.argv
      # Remove app name
      list.pop(0)
      # Remove whattodo
      list.pop(0)
      # iterate through list schema 'domain' 'token_name' 'token_value'
      while len(list) != 0:
         stringmapEntryRemove(connectiontype,nstimeout,nitroNSIP,authToken,stringmapname,list[1])
   else:
      token_filename = sys.argv[3] 
      stringmapEntryRemove(connectiontype,nstimeout,nitroNSIP,authToken,stringmapname,token_filename)
   # logout after  work
   logOut(connectiontype,nstimeout,nitroNSIP,authToken)
