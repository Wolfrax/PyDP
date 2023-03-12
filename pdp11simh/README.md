This is how to simulate a PDP 11/40 running UNIX v6
The procedure to setup the environment is described, as well as copying information to the PDP 11/40 UNIX environment.

References

* http://decuser.blogspot.com/2015/11/installing-and-using-research-unix.html (Primary source)
* https://gunkies.org/wiki/Installing_UNIX_v6_(PDP-11)_on_SIMH
* http://squoze.net/UNIX/v6/installation
* http://doc.cat-v.org/unix/v6/operating-systems-lecture-notes/script/chapt1.1
* http://doc.cat-v.org/unix/v6/operating-systems-lecture-notes/v6/ (link to distribution tape)

Simh is installed through a debian package on the host:

    $ sudo apt-get install simh

Now the PDP 11 simulator can be started by

    $ pdp11

    PDP-11 simulator V3.8-1
    sim>
    sim> q
    Goodbye
    $

The file `tboot.ini` (tboot == tape boot) have the SimH commands needed to intialize the environment for using the unixv6-tape.
Start the simulator with `$ pdp11 tboot.ini`

    PDP-11 simulator V3.8-1
    Disabling XQ
    RK: creating new file
    RK: creating new file
    RK: creating new file
    RK: creating new file

Press ctrl-E:

    Simulation stopped, PC: 100012 (BR 100012)
    =

Now use the `tmrk` utility by typing `tmrk` at the `=` prompt, then add figures for disk offset, tape offset and count
like so,

    =tmrk
    disk offset
    0
    tape offset
    100
    count
    1
    =

Then continue with a new `tmrk` command and adding figures,

    =tmrk
    disk offset
    1
    tape offset
    101
    count
    3999

Then press ctrl-E again and get the `sim>` prompt and quit SimH by typing q.

Notes:

* set tto 7b - set the terminal output to 7 bits, which is compatible with Unix v6.
* attach rk3 rk3 - added an extra disk that we can use later... or not...
* attach ptr paperin - added a paper tape reader virtual device which will come in handy to transfer files from the host to v6.
* attach ptp paperout - added a paper tape punch virtual device which will be useful for transferring files from v6 to the host.
* attach lpt lpt.txt - added a virtual line printer that will allow us to print things to the host from v6
* dep system sr 173030 - Unix will boot the system in single user mode (xref, man 8 boot procedures in v6)
* boot rk0 - boot using the disk that we installed a boot loader and root filesystem to

Now start with `dboot.ini`

    $ pdp11 dboot.ini

    PDP-11 simulator V3.8-1
    Disabling XQ
    LPT: creating new file
    PTP: creating new file
    @

Type `rkunix`at the @-prompt, Unix v6 is now running and the command prompt is #.
Type `STTY -LCASE`, to reset the terminal to use lower case.

Now some configuration and installation of a new kernel.

    # chdir /usr/sys/conf
    # cc mkconf.c
    # mv a.out mkconf

Run mkconf and tell it about our attached devices - rk05's, tape reader and tape punch, magtape, DECtape, serial 
terminals, and line printer:

    # ./mkconf
    rk
    pc
    tm
    tc
    8dc
    lp
    done
    # 

Now compile the kernel and move it:

    # as m40.s
    # mv a.out m40.o
    # cc -c c.c
    # as l.s
    # ld -x a.out m40.o c.o ../lib1 ../lib2
    # mv a.out /unix
    # ls -l /unix
    -rwxrwxrwx  1 root    30942 Oct 10 12:38 /unix

Now create special files and change attributes

    # /etc/mknod /dev/rk0 b 0 0
    # /etc/mknod /dev/rk1 b 0 1
    # /etc/mknod /dev/rk2 b 0 2
    # /etc/mknod /dev/rk3 b 0 3
    # /etc/mknod /dev/mt0 b 3 0
    # /etc/mknod /dev/tap0 b 4 0
    # /etc/mknod /dev/rrk0 c 9 0
    # /etc/mknod /dev/rrk1 c 9 1
    # /etc/mknod /dev/rrk2 c 9 2
    # /etc/mknod /dev/rrk3 c 9 3
    # /etc/mknod /dev/rmt0 c 12 0
    # /etc/mknod /dev/ppt c 1 0
    # /etc/mknod /dev/ptr c 1 1
    # /etc/mknod /dev/lp0 c 2 0
    # /etc/mknod /dev/tty0 c 3 0
    # /etc/mknod /dev/tty1 c 3 1
    # /etc/mknod /dev/tty2 c 3 2
    # /etc/mknod /dev/tty3 c 3 3
    # /etc/mknod /dev/tty4 c 3 4
    # /etc/mknod /dev/tty5 c 3 5
    # /etc/mknod /dev/tty6 c 3 6
    # /etc/mknod /dev/tty7 c 3 7
    # chmod 640 /dev/*rk*
    # chmod 640 /dev/*pp*
    # chmod 640 /dev/ptr
    # chmod 640 /dev/*lp*
    # chmod 640 /dev/*mt*
    # chmod 640 /dev/*tap*
    # chmod 640 /dev/*tty*

Restore doc and source from rk05s and mount them:

    # dd if=/dev/rmt0 of=/dev/rrk1 count=4000 skip=4100
    4000+0 records in
    4000+0 records out
    # dd if=/dev/rmt0 of=/dev/rrk2 count=4000 skip=8100
    3999+1 records in
    3999+1 records out
    # sync
    # sync
    # mkdir /usr/doc
    # /etc/mount /dev/rk1 /usr/source
    # /etc/mount /dev/rk2 /usr/doc

Mount this permanently by updating `/etc/rc`:

    # cat /etc/rc
    rm -f /etc/mtab
    /etc/update
    # cat >> /etc/rc
    /etc/mount /dev/rk1 /usr/source
    /etc/mount /dev/rk2 /usr/doc
    ctrl-D
    # cat /etc/rc
    rm -f /etc/mtab
    /etc/update
    /etc/mount /dev/rk1 /usr/source
    /etc/mount /dev/rk2 /usr/doc

Modify tty using ed:

    # ed /etc/ttys
    1,8s/^0/1/p
    w
    112
    q
    # sync
    # sync
    
Quit SimH through ctrl-E and `q`.
Now we create `nboot.ini` (normal boot) with this content:

    set cpu 11/40
    set cpu idle
    set tto 7b
    set tm0 locked
    attach rk0 rk0
    attach rk1 rk1
    attach rk2 rk2
    attach rk3 rk3
    attach ptr ptr.txt
    attach ptp ptp.txt
    attach lpt lpt.txt
    set dci en
    set dci lines=8
    set dco 7b
    att dci 5555
    boot rk0

Use this as:

    # pdp11 nboot.ini

    PDP-11 simulator V3.8-1
    Disabling XQ
    PTR: creating new file
    PTP: creating new file
    LPT: creating new file
    Listening on port 5555 (socket 11)
    @unix
    
    login: root
    #

Now device files can be used for copying files from/to PDP 11 environment.
To copy out, do for example:

    # cat /etc/rc > /dev/lp0

Then check the file lpt.txt on the host.

To copy in, on the host copy some file to `ptr.txt`, on PDP 11 do (this works for binary files also):

    # cat > myfile < /dev/ppt
    # cat myfile
    Line 1
    Line 2
    And
    EOF
    # 

See more on the primary reference.

In essence, the a.out file creted by my python implementation of the as-assember can be transferred to PDP 11
environment by copying this to `ptr.txt` and then using above commands.

Note that telnet is available, on host try (remember that escape char for telnet is ctrl-])

    $ telnet localhost 5555
