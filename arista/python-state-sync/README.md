python-state-sync
-----------------

Step 1. To generate the python bindings from thrift, run (within the docker build container)

```
cd /var/FBOSS/fboss.git/arista/python-state-sync
./manage setup
```

Step 2. The necessary files can then be copied (and used) on a dut by running (outside the container)

```
./manage copy <dut1> <dut2>
```

Files are copied to `/tmp`

`ssh-keygen + ssh-copy-id` makes copying files over easier.

Step 3. Running the script on the dut (in /tmp)

```
./state-sync.py --get vpr104 vpr105
```

Fetches the state from vpr104 and vpr105. Note that you do NOT want to get the state from the local device (and set it in the remote path)

```
./state-sync.py --get vpr104 vpr105 --set
```

Fetches (from vpr104, vpr105) and updates the state of the local viper switch.
