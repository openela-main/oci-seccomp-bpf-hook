%global with_debug 1

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

# use the same arch definitions as present in the bcc package
ExclusiveArch:  x86_64 %{power64} aarch64 s390x armv7hl

Name: oci-seccomp-bpf-hook
Version: 1.2.11
License: Apache-2.0 and BSD-2-Clause and BSD-3-Clause and ISC and MIT
Release: 2%{?dist}
ExclusiveArch: %{golang_arches_future}
Summary: OCI Hook to generate seccomp json files based on EBF syscalls used by container
URL: https://github.com/containers/oci-seccomp-bpf-hook
# Tarball fetched from upstream
Source0: https://github.com/containers/oci-seccomp-bpf-hook/archive/v%{version}.tar.gz
BuildRequires: golang
BuildRequires: go-md2man
BuildRequires: go-rpm-macros
BuildRequires: glib2-devel
BuildRequires: glibc-devel
BuildRequires: bcc-devel
BuildRequires: git
BuildRequires: gpgme-devel
BuildRequires: libseccomp-devel
BuildRequires: make
Requires: bcc
Enhances: podman
Enhances: cri-o
# vendored libraries
# awk '{print "Provides: bundled(golang("$1")) = "$2}' go.mod | sort | uniq | sed -e 's/-/_/g' -e '/bundled(golang())/d' -e '/bundled(golang(go\|module\|replace\|require))/d'
Provides: bundled(golang(github.com/iovisor/gobpf)) = v0.2.0
Provides: bundled(golang(github.com/opencontainers/runtime_spec)) = v1.0.3_0.20200728170252_4d89ac9fbff6
Provides: bundled(golang(github.com/seccomp/containers_golang)) = v0.6.0
Provides: bundled(golang(github.com/seccomp/libseccomp_golang)) = v0.9.1
Provides: bundled(golang(github.com/sirupsen/logrus)) = v1.8.1
Provides: bundled(golang(github.com/stretchr/testify)) = v1.4.0

%description
%{summary}
%{name} provides a library for applications looking to use
the Container Pod concept popularized by Kubernetes.

%package tests
Summary: Tests for %{name}

Requires: %{name} = %{version}-%{release}
Requires: podman

%description tests
%{summary}

This subpackage contains system tests for %{name}. It's only meant for gating
tests. End user / customer usage cases are not supported.

%prep
%autosetup -Sgit -n %{name}-%{version}
sed -i 's;HOOK_BIN_DIR;%{_libexecdir}/oci/hooks.d;' %{name}.json
sed -i '/$(HOOK_DIR)\/%{name}.json/d' Makefile

%build
%set_build_flags
export CGO_CFLAGS=$CFLAGS
# These extra flags present in $CFLAGS have been skipped for now as they break the build
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-flto=auto//g')
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-Wp,D_GLIBCXX_ASSERTIONS//g')
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-specs=\/usr\/lib\/rpm\/redhat\/redhat-annobin-cc1//g')

%ifarch x86_64
export CGO_CFLAGS+=" -m64 -mtune=generic -fcf-protection=full"
%endif

export GO111MODULE=off
export GOPATH=$(pwd):$(pwd)/_build

mkdir _build
cd _build
mkdir -p src/github.com/containers/
ln -s ../../../../ src/github.com/containers/oci-seccomp-bpf-hook
cd ..
ln -s vendor src

export GOPATH=$(pwd)/_build:$(pwd)
export LDFLAGS="-X main.version=%{version}"
%gobuild -o bin/%{name} github.com/containers/oci-seccomp-bpf-hook

cd docs
go-md2man -in %{name}.md -out %{name}.1
cd ..

%install
%{__make} DESTDIR=%{buildroot} PREFIX=%{_prefix} install-nobuild
%{__make} DESTDIR=%{buildroot} PREFIX=%{_prefix} GOMD2MAN=go-md2man -C docs install-nobuild

install -d -p %{buildroot}/%{_datadir}/%{name}/test/system
cp -pav test/. %{buildroot}/%{_datadir}/%{name}/test/system

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
# Since we aren't packaging up the vendor directory we need to link
# back to it somehow. Hack it up so that we can add the vendor
# directory from BUILD dir as a gopath to be searched when executing
# tests from the BUILDROOT dir.
ln -s ./ ./vendor/src # ./vendor/src -> ./vendor

export GOPATH=%{buildroot}/%{gopath}:$(pwd)/vendor:%{gopath}

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest github.com/containers/oci-seccomp-bpf-hook/src/%{name}
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE
%doc README.md
%dir %{_libexecdir}/oci/hooks.d
%{_libexecdir}/oci/hooks.d/%{name}
%{_datadir}/containers/oci/hooks.d/%{name}.json
%{_mandir}/man1/%{name}.1*

%files tests
%license LICENSE
%{_datadir}/%{name}/test

%changelog
* Tue Jul 07 2026 Jindrich Novy <jnovy@redhat.com> - 1.2.11-2
- rebuild for CVE-2026-33811
  Resolves: RHEL-187325

* Wed Apr 09 2025 Jindrich Novy <jnovy@redhat.com> - 1.2.11-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.11
- simplify spec
- Resolves: RHEL-86603

* Wed Dec 04 2024 Jindrich Novy <jnovy@redhat.com> - 1.2.10-3
- rebuild
- Resolves: RHEL-69918

* Thu Aug 15 2024 Jindrich Novy <jnovy@redhat.com> - 1.2.10-2
- rebuild
- Resolves: RHEL-35939

* Fri Oct 20 2023 Jindrich Novy <jnovy@redhat.com> - 1.2.10-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.10
- Related: RHEL-2112

* Wed Apr 19 2023 Jindrich Novy <jnovy@redhat.com> - 1.2.9-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.9
- Related: #2176063

* Tue Oct 18 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.8-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.8
- Related: #2124478

* Tue Jul 12 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.6-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.6
- Related: #2061316

* Wed May 11 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.5-2
- BuildRequires: /usr/bin/go-md2man
- Related: #2061316

* Wed Mar 16 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.5-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.5
- Related: #2061316

* Fri Oct 01 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.3-5
- perform only sanity/installability tests for now
- Related: #2000051

* Wed Sep 29 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.3-4
- add gating.yaml
- Related: #2000051

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 1.2.3-3
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Tue Jun 22 2021 Mohan Boddu <mboddu@redhat.com> - 1.2.3-2
- Rebuilt for RHEL 9 BETA for openssl 3.0
  Related: rhbz#1971065

* Mon Jun 14 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.3-1
- convert crun dependency to a conflict
- Related: #1970747

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1.2.1-2
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Fri Feb 19 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.1-1
- update to
  https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.1
- require crun >= 0.17

* Thu Jan 28 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.0-6
- revert back to 1.2.0 due to build issues

* Thu Jan 28 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.1-1
- update to
  https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.1

* Tue Dec 08 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-5
- use go_arches macro

* Fri Oct 02 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-4
- use the same arch definitions as present in the bcc package

* Fri Oct 02 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-3
- exclude also armv7hl arch as bcc is not built there

* Wed Sep 30 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-2
- fix spec file to accommodate the new upstream release

* Wed Sep 30 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-1
- update to
  https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.0

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-3
- Second attempt - Rebuilt for
  https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 17 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.1-1
- update to
  https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.1.1

* Fri Jul 17 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.0-2
- switch to mainline releases

* Tue May 19 2020 Lokesh Mandvekar <lsm5@fedoraproject.org> - 1.1.0-1.1.git05a82a1
- bump version
- reuse Makefile targets

* Mon Feb 17 2020 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.0.1-0.6.gitba7bbb16
- Resolves: #1799105 - solve ftbfs and build latest upstream commit

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.0.1-0.5.git3baa603a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Tue Nov 05 2019 Jindrich Novy <jnovy@redhat.com> - 0.0.1-0.4.git3baa603a
- limit arches to only those supported by bcc so that this can be built

* Mon Nov 04 2019 Jindrich Novy <jnovy@redhat.com> - 0.0.1-0.3.git3baa603a
- fix the license - should be ASL 2.0
- use %%gobuild

* Mon Nov 04 2019 Jindrich Novy <jnovy@redhat.com> - 0.0.1-0.2.git3baa603a
- pull in golang deps as BR

* Mon Sep 23 2019 Jindrich Novy <jnovy@redhat.com> - 0.0.1-0.1.git3baa603a
- fix spec file and build

* Sun Sep 22 2019 Dan Walsh <dwalsh@redhat.com> - 0.0.1
- Initial Version
