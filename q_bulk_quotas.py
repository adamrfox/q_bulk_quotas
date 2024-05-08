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
    sys.stderr.write("Usage: q_bulk_quotas.py [-hDv] [-c creds] [-t token] [-e exceptions] qumulo:path quota \n")
    sys.stderr.write("-h | --help : Show help/usage\n")
    sys.stderr.write('-v | --verbose: Print out each path name along the way\n')
    sys.stderr.write('-D | --DEBUG : dump debug info.  Also enables verbose\n')
    sys.stderr.write('-c | --creds : Login credentials format user:password\n')
    sys.stderr.write('-t | --token : Use an auth token\n')
    sys.stderr.write('-e | --exceptions : Read exceptions from a given file\n')
    sys.stderr.write('qumulo:path : Name or IP address of a Qumulo node and the parent path of the quotas [colon separated]\n')
    sys.stderr.write('quota : Default quota to be applied.  Can use K, M, G, P, or T [case insensitive]\n')
    exit(0)

def dprint(message):
    if DEBUG:
        dfh = open('debug.out', 'a')
        dfh.write(message + "\n")
        dfh.close()

def vprint(message):
    if VERBOSE:
        print(message)
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
    dprint("AUTH_HEADERS: " + str(auth_headers))
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

def qumulo_put(addr, api, body):
    dprint("API_PUT: " + api + " : " + str(body))
    dprint("BODY: " + str(body))
    good = False
    while not good:
        good = True
        try:
            res = requests.put('https://' + addr + '/api' + api, headers=auth, data=body, verify=False, timeout=timeout)
        except requests.exceptions.ConnectionError:
            print("Connection Errror: Retrying....")
            time.sleep(5)
            good = False
    results = json.loads(res.content.decode('utf-8'))
    if res.status_code == 200:
        return (results)
    else:
        sys.stderr.write("API ERROR: " + str(res.status_code) + '\n')
        exit(3)

def load_exceptions(file):
    with open(file, 'r') as fp:
        for n, line in enumerate(fp):
            line = line.rstrip()
            if line == "" or line.startswith('#'):
                continue
            (edir,elimit) = line.split(',')
            elimit = compute_quota(elimit)
            if not edir.endswith('/'):
                edir = edir + '/'
            exceptions[edir] = int(elimit)
    fp.close()
    return(exceptions)
def qumulo_post(addr, api, body):
    dprint("API_POST: " + api + " : " + str(body))
    good = False
    while not good:
        good = True
        try:
            res = requests.post('https://' + addr + '/api' + api, headers=auth, data=body, verify=False, timeout=timeout)
        except requests.exceptions.ConnectionError:
            print("Connection Error: Retrying....")
            time.sleep(5)
            good = False
    results = json.loads(res.content.decode('utf-8'))
    if res.status_code == 200:
        return (results)
    else:
        sys.stderr.write("API ERROR: " + str(res.status_code) + '\n')
        exit(3)

def qumulo_delete(addr, api):
    dprint("API_DELETE: " + api)
    good = False
    while not good:
        good = True
        try:
            res = requests.delete('https://' + addr + '/api' + api, headers=auth, verify=False, timeout=timeout)
        except requests.exceptions.ConnectionError:
            print("Connection Error...Retrying...")
            time.sleep(5)
            good = False
    if res.status_code == 200:
        return(res)
    else:
        sys.stderr.write("API ERROR: " + str(res.status_code) + '\n')
        exit(3)
def get_node_addr(addr_list):
    return(randrange(len(addr_list)))

def compute_quota (quota):
    if quota[-1].isalpha():
        unit = quota[-1]
        size = int(quota[:-1])
        if unit in ('g','G'):
            size = size * 1000000000
        elif unit in ('t', 'T'):
            size = size * 1000000000000
        elif unit in ('p', 'P'):
            size = size * 1000000000000000
        elif unit in ('m', 'M'):
            size = size * 1000000
        elif unit in ('k', 'K'):
            size = size * 1000
        else:
            sys.stderr.write("Acceptable unit sizes are 'K', 'M', 'G', 'T', 'P' case insensitive")
            exit(1)
    else:
        size = int(quota)
    dprint("QUOTA SIZE = " + str(size))
    return(size)

if __name__ == "__main__":
    DEBUG = False
    VERBOSE = False
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

    optlist, args = getopt.getopt(sys.argv[1:],'hDt:c:e:v', ['help', 'DEBUG', 'token=', 'creds',
                                                            'exceptions=', 'verbose'])
    for opt, a in optlist:
        if opt in ['-h', '--help']:
            usage()
        if opt in ('-D', '--DEBUG'):
            DEBUG = True
            VERBOSE = True
        if opt in ('-v', '--verbose'):
            VERBOSE = True
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
    quota = compute_quota(quota)
    if exceptions_file:
        exceptions = load_exceptions(exceptions_file)
    dprint("EXCEPTIONS: " + str(exceptions))
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
        if quota_list['quotas'] == []:
            break
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
#    pp.pprint(dir_list)
    for d in dir_list.keys():
        vprint("Checking " + d)
        body = json.dumps({'id': str(dir_list[d]['id']), 'limit': str(quota)})
        if dir_list[d]['id'] in quotas.keys():
            if d in exceptions.keys():
                if exceptions[d] < 0:
                    print('Deleting quota from ' + d)
                    qumulo_delete(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/quotas/' + dir_list[d]['id'])
                    continue
                elif int(quotas[dir_list[d]['id']]) != exceptions[d]:
                    print("Updating quota on " + d)
                    body = json.dumps({'id': str(dir_list[d]['id']), 'limit': str(exceptions[d])})
                    qumulo_put(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/quotas/' + dir_list[d]['id'],body)
                    continue
                else:
                    continue
            elif int(quotas[dir_list[d]['id']]) == quota:
                continue
            if quota >= 0:
                print("Updating quota on " + d)
                qumulo_put(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/quotas/' + dir_list[d]['id'], body)
            else:
                print("Deleting quota from " + d)
                qumulo_delete(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/quotas/' + dir_list[d]['id'])
        else:
            if d in exceptions.keys():
                if exceptions[d] >= 0:
                    body = json.dumps({'id': str(dir_list[d]['id']), 'limit': str(exceptions[d])})
                else:
                    continue
            if quota >= 0:
                print("Adding quota to " + d)
                qumulo_post(addr_list[get_node_addr(addr_list)]['address'], '/v1/files/quotas/', body)




