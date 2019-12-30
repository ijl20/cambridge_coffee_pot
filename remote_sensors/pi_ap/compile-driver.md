# Compile driver for 3.10.y version of kernel. To compile for an older version you will need
# to set up the correct commits of linux and firmware to comply with the version of linux you
# need the driver for.

# Compiles 8188eu driver for 3.10.y without needing to compile the whole linux kernel. Requires
# driver firmware, rtl8188eufw.bin, which can be found in the driver source tree.


# Initialise kernel and driver source code for the first time for compiling drivers
-----------------------------------------------------------------------------------

# jump to home directory - /home/pi
cd
 
# make directory to hold source data
mkdir src

# enter source directory - /home/pi/src
cd src

# clone rtl8188eu source code repository - this will automatically generate a
# directory "rtl8188eu" at /home/pi/src/rtl8188eu.
git clone git://github.com/lwfinger/rtl8188eu.git

# clone Raspberry Pi firmware repository - this will automatically generate a
# directory "firmware" at /home/pi/src/firmware - setting depth avoids downloading
# the whole repository but allows reverting to some previous revisions if necessary.
# Do not use git clone if it has already been used - use git pull to update the code.
git clone --depth 10 git://github.com/raspberrypi/firmware.git

# clone Raspberry Pi linux source code - this will automatically generate a 
# directory "linux" at /home/pi/src/linux -  setting depth avoids downloading 
# the whole repository but allows reverting to some previous revisions if
# necessary. Do not use git clone if it has already been used - use git pull
# to update the code.
git clone --depth 235 git:github.com/raspberrypi/linux.git


# Updating source code for compiling drivers if code is already installed and
# newer code is available
-----------------------------------------------------------------------------

# if rtl8188eu directory has already been generated it can be update with the
# latest code using git pull. enter rtl8188eu directory, run command then revert
# back to src directory
cd rtl8188eu
git pull
cd ../

# if firmware directory has already been generated it can be update with the
# latest code using git pull enter firmware directory, run command then revert
# back to src directory. Use depth option or git pull may load the whole of
# the repository from way back 2011 or whenever
cd firmware
git pull --depth 2
cd ../

# if linux directory has already been generated it can be update with the latest
# code using git pull. enter linux directory, run command then revert back to 
# src directory. Use depth option or git pull may load the whole of the repository 
# from way back 2011 or whenever ~ 3 Million+ files
cd linux
git pull --depth 2
cd ../


# Select a specific version of linux/firmware to compile driver for if required
-------------------------------------------------------------------------------

# adjust firmware version required for kernel version driver is to be used with
# view commit ID's at https://github.com/raspberrypi/firmware/commits/master
# not required if driver is being compiled for most recent version kernel
# unless it has previously been set to use an older version of code
cd firmware
git checkout "branch"
git checkout "commit ID"
cd ../

# enter linux source directory and adjust linux code version to use
# adjust to version required for kernel version driver is to be used with
# view commit ID's at https://github.com/raspberrypi/linux/commits/
# not required if driver being compiled for most recent version kernel
cd linux
git checkout "branch"
git checkout "commit ID"
cd ../


# To compile for latest code I use the following commands
---------------------------------------------------------

# enter linux source directory
cd linux

# clean linux source directory tree
make mrproper

# generate .config using bcmrpi_defconfig which can be used to make .config for any
# version of linux without requiring to copying .config from a working version of code 
# as suggested in many tutorials making life a little easier.
make bcmrpi_defconfig

# prepare source for module compile
make modules_prepare

# copy Module.symvers file from firmware tree to linux directory
cp ../firmware/extra/Module.symvers .

# enter 8188eu driver source directory
cd ../rtl8188eu

# clean rtl8188eu source directory tree
make clean

# compile driver file 8188eu.ko
CONFIG_RTL8188EU=m make -C /home/pi/src/linux M=`pwd`

# Install the driver
--------------------

# install driver firmware if not already installed, install driver and reboot
sudo cp rtl8188eufw.bin /lib/firmware/rtlwifi
sudo install -p -m 644 8188eu.ko /lib/modules/$(uname -r)/kernel/drivers/net/wireless

# insmod command should run without any error response if driver module is compiled OK
sudo insmod /lib/modules/$(uname -r)/kernel/drivers/net/wireless/8188eu.ko
sudo depmod -a
sudo reboot

Hope this makes sense
