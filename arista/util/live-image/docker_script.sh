#! /bin/bash

kernel_version=$1
centos_stream_number=$2
grub_cfg_file=grub.cfg

# Set up the live image environment under /centos
dnf -y --nogpgcheck --releasever=$centos_stream_number --installroot=/centos groups install 'Minimal Install'
dnf -y --nogpgcheck --releasever=$centos_stream_number --installroot=/centos install dracut-tools dracut-live
cp /etc/resolv.conf /centos/etc/.
mkdir /centos/kernel_RPMs
cp /app/kernel_RPMs/* /centos/kernel_RPMs
cp /app/installation_script.sh /centos/
# installation_script.sh installs kernel RPMs and FBOSS dependencies in the live image environment
chroot /centos/ /bin/bash installation_script.sh
# Set up admin user access and passwordless SSH in the file system and disable SELinux
echo "root:arastra" | chpasswd -R /centos
chroot /centos adduser admin
chroot /centos passwd -d admin
chroot /centos usermod -aG wheel admin
echo -e "\nPermitEmptyPasswords yes" | chroot /centos tee -a /etc/ssh/sshd_config
echo -e "\nPermitRootLogin yes" | chroot /centos tee -a /etc/ssh/sshd_config
chroot /centos sed -i 's/^SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

rm -rf /app/build/boot
mkdir -p /app/build/boot
mkdir /app/build/boot/overlayfs
mkdir /app/build/boot/ovlwork

# grub.cfg used for LOCAL boot
printf "set timeout=5\n" >> $grub_cfg_file
printf "serial --speed=9600 --unit=0 --word=8 --parity=no --stop=1\n" >> $grub_cfg_file
printf "terminal_input console serial\n" >> $grub_cfg_file
printf "terminal_output console serial\n\n" >> $grub_cfg_file
printf "menuentry 'CentOS ($kernel_version)' --unrestricted {\n" >> $grub_cfg_file
printf "  search --set=root --label eos_flash\n" >> $grub_cfg_file
printf "  linux /boot/vmlinuz-$kernel_version rw root=live:LABEL=eos_flash rd.live.dir=/boot rd.live.overlay.overlayfs rd.live.overlay=LABEL=eos_flash:/boot/overlayfs biosdevname=0 crashkernel=128M fsck.repair=yes systemd.gpt_auto=0 console=ttyS0,9600 8250.nr_uarts=4 loglevel=5 printk.console_no_auto_verbose=1 nopat net.ifnames=0 msr.allow_writes=on swiotlb=4096 cma=512M@0-4G scd.lpc_irq=7 scd.lpc_res_addr=0xb0000000 scd.lpc_res_size=0x10000\n" >> $grub_cfg_file
printf "  initrd /boot/initramfs.live-$kernel_version.img\n" >> $grub_cfg_file
printf "}\n\n" >> $grub_cfg_file

# Generate an initramfs with live boot capabilities
echo dracut --no-hostonly --add \"dmsquash-live url-lib livenet squash\" --xz /boot/initramfs.live-$kernel_version.img $kernel_version > create_initramfs.sh
cp create_initramfs.sh /centos/
chroot /centos/ /bin/bash create_initramfs.sh

# Copy vmlinuz, initramfs, and grub.cfg to a separate build directory containing a boot subdirectory
cp /centos/boot/initramfs.live-$kernel_version.img /app/build/boot/
cp centos/boot/vmlinuz-$kernel_version /app/build/boot/
cp grub.cfg /app/build/boot/

# Create SquashFS used in the live image
dnf -y --nogpgcheck --releasever=$centos_stream_number install squashfs-tools
mksquashfs /centos /app/build/boot/squashfs.img -no-progress

cd /app/build
tar -cvf centos${centos_stream_number}_${kernel_version}_live.tar boot/
