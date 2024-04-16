# q_bulk_quotas
A project to do bulk quota adds on a Qumulo Cluster.

This is a simple Python sctipt to allow bulk changes to directory quotas for all directories directly under a given path.
A quota of 0 cuts off all writes, a quota of less than 0 means no quota and any quota on that path will be deleted.

<format>
Usage: q_bulk_quotas.py [-hD] [-c creds] [-t token] [-e exceptions] qumulo:path quota
-h | --help : Show help/usage
-D | --DEBUG : dump debug info
-c | --creds : Login credentials format user:password
-t | --token : Use an auth token
-e | --exceptions : Read exceptions from a given file
qumulo:path : Name or IP address of a Qumulo node and the parent path of the quotas [colon speparted]
quota : Default quota to be applied.  Can use K, M, G, P, or T [case insensitive]
</format>

Exceptions can be granted with an CSV file and the -e option.  An example is included.  
