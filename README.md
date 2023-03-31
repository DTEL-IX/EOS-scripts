# EOS-scripts
Here custom scripts for Arista EOS devices written by DTEL-IX are placed.

Please, note, all those scripts are tested on 7800R3 device (although they has to work on other Arista boxes
running EOS as well).

* **show_int_brief.py** - easy way to troubleshoot links fast - you see customer's interfaces status, media,
  load and signal levels at a glance:
```sh
switch#sh int br flow
Interface State/ Description                  Type              TX/RX                             TX/RX signal power, dBm
          Proto                                               load, %       Lane 1       Lane 2       Lane 3       Lane 4

Et9/48    C/U    sFlow to flow:eno33np0       10GBASE-LR          0/0     0.8/-1.7                             
Et10/48   C/U    sFlow to flow:eno34np1       10GBASE-LR          0/0     0.8/-0.8                             
Po1000    C/U    sFlow to flow:bond0          LAG-20G             0/0

### Or matching interface name with regexp:

switch#sh int br "(9|10)/48"
Interface State/ Description                  Type              TX/RX                             TX/RX signal power, dBm
          Proto                                               load, %       Lane 1       Lane 2       Lane 3       Lane 4

Et9/48    C/U    sFlow to flow:eno33np0       10GBASE-LR          0/0     0.8/-1.7                             
Et10/48   C/U    sFlow to flow:eno34np1       10GBASE-LR          0/0     0.8/-0.8
```
