#!/usr/bin/env bash
set -e
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH


Get_Dist_Name()
{
    if grep -Eqi "CentOS" /etc/issue || grep -Eq "CentOS" /etc/*-release; then
        DISTRO='CentOS'
        PM='yum'
    elif grep -Eqi "Red Hat Enterprise Linux Server" /etc/issue || grep -Eq "Red Hat Enterprise Linux Server" /etc/*-release; then
        DISTRO='RHEL'
        PM='yum'
    elif grep -Eqi "Aliyun" /etc/issue || grep -Eq "Aliyun" /etc/*-release; then
        DISTRO='Aliyun'
        PM='yum'
    elif grep -Eqi "Fedora" /etc/issue || grep -Eq "Fedora" /etc/*-release; then
        DISTRO='Fedora'
        PM='yum'
    elif grep -Eqi "Amazon Linux AMI" /etc/issue || grep -Eq "Amazon Linux AMI" /etc/*-release; then
        DISTRO='Amazon'
        PM='yum'
    elif grep -Eqi "Debian" /etc/issue || grep -Eq "Debian" /etc/*-release; then
        DISTRO='Debian'
        PM='apt'
    elif grep -Eqi "Ubuntu" /etc/issue || grep -Eq "Ubuntu" /etc/*-release; then
        DISTRO='Ubuntu'
        PM='apt'
    elif grep -Eqi "Raspbian" /etc/issue || grep -Eq "Raspbian" /etc/*-release; then
        DISTRO='Raspbian'
        PM='apt'
    elif grep -Eqi "Deepin" /etc/issue || grep -Eq "Deepin" /etc/*-release; then
        DISTRO='Deepin'
        PM='apt'
    else
        DISTRO='unknow'
    fi

}


install_dep(){
if [ "$PM" = "yum" ]; then
    $PM makecache
	$PM install -y epel-release
	$PM makecache
    $PM install -y python-pip cron
    pip install setuptools psutil requests py-cpuinfo
elif [ "$PM" = "apt" ]; then
	$PM update
    $PM install -y python-pip cron
    pip install setuptools psutil requests py-cpuinfo
fi

}



echo -e "|\n|   ServerSan Installer\n|   ===================\n|"

# Check if user is root
if [ $(id -u) != "0" ]; then
    echo "Error: You must be root to run this script, please switch to root."
    exit 1
fi

# Parameters required
if [ $# -lt 1 ]
then
	echo -e "|   Usage: bash $0 'token'\n|"
	exit 1
fi

# Attempt to delete previous agent
if [ -f /etc/serversan/ss-agent.py ]
then
	# Remove agent dir
	rm -Rf /etc/serversan
	# Remove cron entry and user
	if id -u serversan >/dev/null 2>&1
	then
		(crontab -u serversan -l | grep -v "/etc/serversan/ss-agent.py") | crontab -u serversan - && userdel serversan
	else
		(crontab -u root -l | grep -v "/etc/serversan/ss-agent.py") | crontab -u root -
	fi
fi

# Create agent dir
mkdir -p /etc/serversan

# install dependent
Get_Dist_Name
install_dep

# download agent
echo -e "|   Downloading ss-agent.py to /etc/serversan\n|\n|   + $(wget -nv -o /dev/stdout -O /etc/serversan/ss-agent.py --no-check-certificate https://raw.githubusercontent.com/BennyThink/ServerSan/master/ss-agent.py)"

if [ -f /etc/serversan/ss-agent.py ]
then
	# Create auth file
	echo "$1" > /etc/serversan/ss-auth.log

	# Create user
	useradd serversan -r -d /etc/serversan -s /bin/false

	# Modify user permissions
	chown -R serversan:serversan /etc/serversan && chmod -R 700 /etc/serversan

	# Modify ping permissions
	chmod +s `type -p ping`

	# Configure cron
	crontab -u serversan -l 2>/dev/null | { cat; echo "*/3 * * * * /usr/bin/python /etc/serversan/ss-agent.py > /etc/serversan/ss-cron.log 2>&1"; } | crontab -u serversan -

	# Show success
	echo -e "|\n|   Success: The serversan agent has been installed\n|"

	# Attempt to delete installation script
	if [ -f $0 ]
	then
		rm -f $0
	fi
else
	# Show error
	echo -e "|\n|   Error: The serversan agent could not be installed\n|"
fi
