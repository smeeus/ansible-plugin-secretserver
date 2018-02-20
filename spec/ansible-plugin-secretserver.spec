# Global variables
# ================

# Install directory
%global ansible_plugins_dir %{_datadir}/ansible/plugins

# Ignore brp-python-bytecompile script errors
#%global _python_bytecompile_errors_terminate_build 0

# Turn off brp-python-bytecompile script
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')


# Package attributes
# ==================

Summary:   Ansible lookup plugin for Thycotic Secret Server
Name:      ansible-plugin-secretserver
Version:   0.2.0
Release:   1%{?dist}
License:   MIT
URL:       https://github.com/smeeus/ansible-plugin-secretserver
BuildArch: noarch

# Don't make a debuginfo package
%define debug_package %{nil}

# Source definitions
# ==================

Source0:   %{url}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz

# Requirements
# ============

Requires: ansible >= 2.0.0

# SPEC sections
# =============

%description
A custom Ansible lookup plugin to retrieve secret information from Thycotic Secret Server via the REST API.

%prep
%autosetup -N -n %{name}-%{version}

# End of prep
:;

%install
mkdir -p ${RPM_BUILD_ROOT}%{ansible_plugins_dir}/lookup
install -m644 $RPM_BUILD_DIR/%{name}-%{version}/lookup/secretserver.py ${RPM_BUILD_ROOT}%{ansible_plugins_dir}/lookup/secretserver.py

# End of install
:;

%clean
# Cleanup BUILD and BUILDROOT directory
if [ -d ${RPM_BUILD_ROOT} ]; then
	rm -rf ${RPM_BUILD_ROOT};
fi
rm -rf $RPM_BUILD_DIR/%{name}-%{release}

# End of clean
:;

%files
%defattr(-,root,root,-)
%{ansible_plugins_dir}/lookup/secretserver.py
%doc README.md LICENSE

# End of files

%changelog
* Tue Feb 20 2018 Sven Meeus <sven.meeus@framed.be> - 0.2.0-1
- Add RPM spec file to project
* Tue Feb 20 2018 Sven Meeus <sven.meeus@framed.be> - 0.1.0-1
- First release
