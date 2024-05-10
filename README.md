# q_bulk_quotas
A project to do bulk quota adds on a Qumulo Cluster.

This is a simple Python sctipt to allow bulk changes to directory quotas for all directories directly under a given path.
A quota of 0 cuts off all writes, a quota of less than 0 means no quota and any quota on that path will be deleted.

<pre>
Usage: q_bulk_quotas.py [-hDv] [-c creds] [-t token] [-e exceptions] qumulo:path quota \n"
-h | --help : Show help/usage
-v | --verbose: Print out each path name along the way
-D | --DEBUG : dump debug info.  Also enables verbose
-c | --creds : Login credentials format user:password
-f | --file_token : Use a token file generated from qq auth_create_token-t | --token : Use an auth token
-e | --exceptions : Read exceptions from a given file
qumulo:path : Name or IP address of a Qumulo node and the parent path of the quotas [colon separated]
quota : Default quota to be applied.  Can use K, M, G, P, or T [case insensitive]
</pre>

Exceptions can be granted with an CSV file and the -e option.  An example is included.  

## Using Tokens from a file
If you want to run the script non-interactively, you can generate an access token using the qq command:
<pre>
  qq --host [your-host] auth_create_access_token -f [file] [user]
</pre>

This file can then be used as the argument to the -f flag.

## Restricted User Role
It may be desireable to have the script run as a user with the least required priviledges.  This can be done by 
generating a role with the following permissions
<ul>
  <li>FS_ATTRIBUTES_READ</li>
  <li>NETWORK_READ</li>
  <li>QUOTA_READ</li>
  <li>QUOTA_WRITE</li>
</ul>
