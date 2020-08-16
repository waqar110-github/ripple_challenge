# import useful libraries
import requests as rq
import os
import sched
from datetime import datetime
import time as t

# Setting variables
polling_interval = 2 # defined POLLING INTERVAL in SECONDS
time_interval = 60 # polling executes in defined TIME INTERVAL in SECONDS
# API variables
target_rippled_url = "http://s1.ripple.com:51234/"
json_req_data = {"method": "server_info","params": [{"api_version": 1}]}
# data file to records information for plotting
plot_file = "Plot_datafile_" + str(datetime.utcnow().microsecond) + ".dat"
print("plot file created " + plot_file)
# initializing global variables with dummy values
dummy_time = datetime.strptime("2000-Aug-01 21:03:19.698082 UTC", '%Y-%b-%d %H:%M:%S.%f UTC')
min_time = dummy_time
max_time = dummy_time
curr_UTC = dummy_time
prev_UTC = dummy_time
first_UTC = dummy_time
t_diff = dummy_time
prev_validated_ledger_seq = 0
first_iteration = True

def RPC_ServerInfo(sc):
 global prev_validated_ledger_seq
 global curr_UTC
 global prev_UTC
 global first_UTC
 global t_diff

 # calling jsonrpc to get response in dictionary type
 rpc_res = rq.post(url=target_rippled_url,json=json_req_data).json()

 # get sequence number, UTC of validated ledger
 valdated_ledger_seq = rpc_res.get("result").get("info").get("validated_ledger").get("seq")
 UTC = rpc_res.get("result").get("info").get("time")
 line = UTC + "  " + str(valdated_ledger_seq)

 # Record data in file
 # Only record unique validated sequence numbers
 if os.path.isfile(plot_file)==False:
  prev_validated_ledger_seq = valdated_ledger_seq
  first_UTC = datetime.strptime(UTC, '%Y-%b-%d %H:%M:%S.%f UTC')
  curr_UTC = first_UTC
  prev_UTC = first_UTC

  with open(plot_file, "w") as file:
   file.write(line + " " + "00:00:00" +'\n')

 elif os.path.isfile(plot_file)==True:
  if prev_validated_ledger_seq != valdated_ledger_seq:
   t_diff = calculate_min_max_avg(UTC,valdated_ledger_seq)

   with open(plot_file, "a") as file:
    file.write(line + " " + str(t_diff) + '\n')

 # schedule to call server_info on defined polling interval
 event = sc.enter(polling_interval, 1, RPC_ServerInfo, (sc,))
 sch_cancel(event,sc)

def calculate_min_max_avg(UTC,valdated_ledger_seq):
 global prev_validated_ledger_seq
 global curr_UTC
 global prev_UTC
 global first_iteration
 global min_time
 global max_time

 curr_UTC = datetime.strptime(UTC, '%Y-%b-%d %H:%M:%S.%f UTC')
 t_diff = curr_UTC - prev_UTC

 if first_iteration == True:
  min_time = t_diff
  max_time = t_diff
  first_iteration = False
 else:
  if t_diff < min_time:
   min_time = t_diff
  elif t_diff > max_time:
   max_time = t_diff

 prev_UTC = curr_UTC
 prev_validated_ledger_seq = valdated_ledger_seq

 return t_diff

def sch_cancel(event,sc):
 # scheduler executes API till defined time interval then cancel the calling event
 diff = curr_UTC - first_UTC
 if diff.total_seconds() > time_interval and event:
  sc.cancel(event)

  avg_time = (min_time + max_time)/2
  with open(plot_file + "validated_time.txt", "w") as file:
   file.write("min interval " + str(min_time) + '\n')
   file.write("max interval " + str(max_time) + '\n')
   file.write("avg interval " + str(avg_time) + '\n')

def main():
 s = sched.scheduler(t.time, t.sleep)
 RPC_ServerInfo(s)
 s.run()

# code execution start
main()
