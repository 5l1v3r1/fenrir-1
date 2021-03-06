import os
import datetime

from django.shortcuts import render
from django.template import Context, loader
from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

#AUTH
from accounts.views import signin

#Database
from udc.models import *
from lib.ssh_connect import *
from lib.polyglot import *

#Fenrir
from engine import *
#from lib.getalert import syncalerts

@csrf_protect
@never_cache
def index(request):
   auth_profile = auth_profiles.objects.all()
   
   #Calculate Alert Severities
   extreme = 0
   high = 0
   elevated = 0
   moderate = 0
   low = 0
   for alert in alerts.objects.all():
      #print alert.severity
      if int(alert.severity) <= 3:
         low = low + 1
      elif int(alert.severity)> 3 and int(alert.severity) <= 6:
         moderate = moderate + 1
      elif int(alert.severity) > 6 and int(alert.severity) <= 9:
         elevated = elevated + 1
      elif int(alert.severity) > 9 and int(alert.severity) <= 12:
         high = high + 1
      elif int(alert.severity) > 12:
         extreme = extreme + 1
         
   #Calculate Agent Details
   online = 0
   active = 0
   for agent in agent_details.objects.all():
      active = active + 1
      lasttime = datetime.datetime.strptime(agent.last_check, "%Y-%m-%d %H:%M:%S.%f")
      if lasttime > datetime.datetime.utcnow() - datetime.timedelta(minutes=5):
         online = online + 1
   
   alert = alerts.objects.all().order_by('-time')[:25]
   rule = rules.objects.all()
   
      #Relay Template Variables
   return render_to_response("index.html", {
      "user"          :   request.user,
      "auth_profiles" :   auth_profile,
      "alerts"        :   alert,
      "extreme"       :   extreme,
      "high"          :   high,
      "elevated"      :   elevated,
      "moderate"      :   moderate,
      "low"           :   low,
      "online"        :   online,
      "active"        :   active,
      "rules"         :   rule,
   })

def configure(request):
   auth_profile = auth_profiles.objects.all()
   alert = alerts.objects.all()
   rule = rules.objects.all()
   
      #Relay Template Variables
   return render_to_response("configure.html", {
      "auth_profiles" :   auth_profile,
      "alerts"        :   alert,
      "rules"         :   rule,
   })

@csrf_exempt
def cmd(request):
   if request.is_ajax():
      try:
         host_profile = auth_profiles.objects.get(alias=request.POST["cmd"].split(" ")[0].strip("@"))
         profile = auth_profiles.objects.get(id=host_profile.id)
         
         sshAuth = {
         "system"   : profile.system,
         "host"     : profile.host,
         "user"     : profile.username,
         "pass"     : profile.password,
         "key"      : profile.authkey
         }
         
         command = request.POST["cmd"].split(" ")
         del command[0]
         command = ' '.join(command)
         
         
         retval = ssh_exec(sshAuth, command)
         
         f = open('cmd_retval','w')
         for object in retval:
            f.write(object)
         f.close()
         
      except:
         pass
      
@csrf_exempt
def addsys(request):
   if request.is_ajax():
      try:
         newsys = auth_profiles.objects.create(system = request.POST["system"], version = " ", alias = request.POST["alias"], host = request.POST["host"], username = request.POST["username"], password = request.POST["password"], authkey = " ")
         entry.auth_profiles.add(newsys)
         print request.POST["system"], request.POST["password"]
         
      except:
         pass
      
@csrf_exempt
def addrule(request):
   if request.is_ajax():
      try:
         #identify sensor
         #format rule
         command = lexicon(request.POST)
         
         #get auth info
         host_profile = auth_profiles.objects.get(alias=request.POST["system"])
         profile = auth_profiles.objects.get(id=host_profile.id)
         
         sshAuth = {
         "system"   : profile.system,
         "host"     : profile.host,
         "user"     : profile.username,
         "pass"     : profile.password,
         "key"      : profile.authkey
         }
         
         #exec command    
         retval = ssh_exec(sshAuth, command)
         
      except:
         pass


def retval(request):
      #If CMD
      try:
         f = open('cmd_retval', 'r')
         cmd_retval = f.read()
         f.close()
         os.remove("cmd_retval")
         print cmd_retval.split("\n")
      
            #Relay Template Variables
         return render_to_response("includes/udc.inc", {
            "retval" :   cmd_retval.split("\n"),
            "blah"   :   "wtf"
         })
      #Else check for additional info
      except:
         try:
            #syncalerts()
            pass
         except:
            print "Alert Syncing Failed"

         auth_profile = auth_profiles.objects.all()
         alert = alerts.objects.all().order_by('-time')[:100]
         rule = rules.objects.all()


         
            #Relay Template Variables
         return render_to_response("includes/sync.inc", {
            "auth_profiles" :   auth_profile,
            "alerts"        :   alert,
            "rules"         :   rule,
         })

    
def sensors(request):
   auth_profile = auth_profiles.objects.all()
   rule = rules.objects.all()
   
      #Relay Template Variables
   return render_to_response("sensors.html", {
      "auth_profiles" :   auth_profile,
      "rules"         :   rule,
   })
      
      
