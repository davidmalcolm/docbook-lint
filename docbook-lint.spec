Summary: Tool for testing DocBook XML sources
Name: docbook-lint
Version: 0.0.2
Release: 1%{?dist}
License: GPL
Group: Development/Tools
URL: https://fedorahosted.org/docbook-lint
Source0: docbook-lint-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
BuildRequires: python
Requires: python
Requires: python-enchant

%description
Tool for testing DocBook XML sources

%prep
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%setup -q

%build
python ./setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python ./setup.py install -O2 --root=$RPM_BUILD_ROOT --record=%{name}.files
rm -rf $RPM_BUILD_ROOT/%{_docdir}/docbooklint

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_bindir}/*
%{python_sitelib}/docbooklint/
%doc README
# TODO HACKING

%changelog
* Tue Apr  1 2008 David Malcolm <dmalcolm@redhat.com> - 0.0.2-1
- rename specfile; bump to 0.0.2

* Tue Dec  5 2006 David Malcolm <dmalcolm@redhat.com> - 0.0.1-2
- added requirement on python-enchant

* Mon Nov 13 2006 David Malcolm <dmalcolm@redhat.com> - 0.0.1-1
- initial packaging

