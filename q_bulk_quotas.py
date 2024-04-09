#!/usr/bin/python3
from __future__ import print_function
import sys
import getopt
import getpass
import requests
import urllib.parse
import json
import urllib3
urllib3.disable_warnings()
from random import randrange
import pprint
pp = pprint.PrettyPrinter(indent=4)


def usage():
    print("Usage goes here!")
    exit(0)

def dprint(message):
    if DEBUG:
        dfh = open('debug.out', 'a')
        dfh.write(message + "\n")
        dfh.close()

def api_login(qumulo, user, password, token):
    headers = {'Content-Type': 'application/json'}
    if not token:
        if not user:
            user = input("User: ")
        if not password:
            password = getpass.getpass("Password: ")
        payload = {'username': user, 'password': password}
        payload = json.dumps(payload)
        autht = requests.post('https://' + qumulo + '/api/v1/session/login', headers=headers, data=payload,
                              verify=False, timeout=timeout)
        dprint(str(autht.ok))
        auth = json.loads(autht.content.decode('utf-8'))
        dprint(str(auth))
        if autht.ok:
            auth_headers = {'accept': 'application/json', 'Content-type': 'application/json', 'Authorization': 'Bearer ' + auth['bearer_token']}
        else:
            sys.stderr.write("ERROR: " + auth['description'] + '\n')
            exit(2)
    else:
        auth_headers = {'accept': 'application/json', 'Content-type': 'application/json', 'Authorization': 'Bearer ' + token}
    return(auth_headers)

def qumulo_get(addr, api):
    dprint("API_GET: " + api)
    good = False
    while not good:
        good = True
        try:
            res = requests.get('https://' + addr + '/api' + api, headers=auth, verify=False, timeout=timeout)
        except requests.exceptions.ConnectionError:
            print("Connection Error: Retrying..")
            time.sleep(5)
            good = False
    if res.status_code == 200:
        results = json.loads(res.content.decode('utf-8'))
#        pp.pprint("RES [" + api + " ] : " + str(results))
        return(results)
    elif res.status_code == 404:
        return("404")
    else:
        sys.stderr.write("API ERROR: " + str(res.status_code) + "\n")
        sys.stderr.write(str(res.content) + "\n")
        exit(3)

def get_node_addr(addr_list):
    return(randrange(len(addr_list)))

if __name__ == "__main__":
    DEBUG = False
    token = ""
    user = ""
    password = ""
    headers = {}
    timeout = 360
    exceptions_file = ""
    exceptions = {}
    addr_list = []
    dir_list = {}
    quotas = {}
    q = {}

    optlist, args = getopt.getopt(sys.argv[1:],'hDt:c:e:', ['--help', '--DEBUG', '--token=', '--creds',
                                                            '--exceptions='])
    for opt, a in optlist:
        if opt in ['-h', '--help']:
            usage()
        if opt in ('-D', '--DEBUG'):
            DEBUG = 1
        if opt in ('-t', '--token'):
            token = a
        if opt in ('-c', '--creds'):
            (user, password) = a.split(':')
        if opt in ('-e', '--exceptions'):
            exceptions_file = a
    try:
        (qumulo, path) = args[0].split(':')
    except:
        usage()
    try:
        quota = args[1]
    except:
        usage()
    auth = api_login(qumulo, user, password, token)
    dprint(str(auth))
    net_data = requests.get('https://' + qumulo + '/v2/network/interfaces/1/status/', headers=auth,
                            verify=False, timeout=timeout)
    dprint(str(net_data.content))
    net_info = json.loads(net_data.content.decode('utf-8'))
    for node in net_info:
        if node['interface_details']['cable_status'] == "CONNECTED" and node['interface_details'][
            'interface_status'] == "UP":
            for ints in node['network_statuses']:
                addr_list.append({'name': node['node_name'], 'address': ints['address']})
    done = False
    next = ''
    while not done:
        if not next:
            quota_list = qumulo_get(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/quotas/?limit=500')
        else:
            quota_list = qumulo_get(addr_list[get_node_addr(addr_list)]['address'], next)
        for q in quota_list['quotas']:
            quotas[q['id']] = q['limit']
            try:
                next = top_dir['paging']['next']
                if not next:
                    done = True
            except:
                done = True
    dir_info = qumulo_get(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/' + urllib.parse.quote(path, safe='') + '/info/attributes')
#    pp.pprint(dir_info)
    if dir_info == "404":
        print('GOT 404 in dir_info')
    dprint(str(dir_info))
    top_id = dir_info['id']
    done = False
    next = ''
    while not done:
        if not next:
            top_dir = qumulo_get(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/' + top_id + '/entries/?limit=500')
            if top_dir == "404":
                print('GOT 404 in next loop: ' + top_id)
                break
        else:
            top_dir = qumulo_get(addr_list[get_node_addr(addr_list)]['address'], next)
            if top_dir == "404":
                print("GOT 404 in else loop: " + + top_id)
#        pp.pprint(top_dir)
        for dirent in top_dir['files']:
            if dirent['type'] == "FS_FILE_TYPE_DIRECTORY":
                dir_list[dirent['path']] = {'name': dirent['name'], 'id': dirent['id']}
        try:
            next = top_dir['paging']['next']
            if not next:
                done = True
        except:
            done = True
    pp.pprint(dir_list)