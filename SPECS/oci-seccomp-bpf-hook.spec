%global with_check 0

%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0

# https://bugzilla.redhat.com/show_bug.cgi?id=1904567
%global _lto_cflags %%{nil}

%if 0%{?rhel} > 7 && ! 0%{?fedora}
%define gobuild(o:) \
go build -buildmode pie -compiler gc -tags="rpm_crashtraceback libtrust_openssl ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-} -linkmode=external -compressdwarf=false -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags'" -a -v %{?**};
%else
%if ! 0%{?gobuild:1}
%define gobuild(o:) GO111MODULE=off go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-} -linkmode=external -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '-Wl,-z,relro -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld '" -a -v %{?**};
%endif
%endif

%global provider github
%global provider_tld com
%global project containers
%global repo oci-seccomp-bpf-hook
# https://github.com/containers/oci-seccomp-bpf-hook
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path %{provider_prefix}
%global git0 https://%{provider}.%{provider_tld}/%{project}/%{repo}

# https://fedoraproject.org/wiki/PackagingDrafts/Go#Go_Language_Architectures
ExclusiveArch: %{go_arches}

Name: oci-seccomp-bpf-hook
Version: 1.2.8
Release: 1%{?dist}
Summary: OCI Hook to generate seccomp json files based on EBF syscalls used by container
License: ASL 2.0
URL: %{git0}
Source0: %{git0}/archive/v%{version}.tar.gz
BuildRequires: golang
BuildRequires: /usr/bin/go-md2man
BuildRequires: glib2-devel
BuildRequires: glibc-devel
BuildRequires: bcc-devel
BuildRequires: git
BuildRequires: gpgme-devel
BuildRequires: libseccomp-devel
BuildRequires: make
Conflicts: crun < 0.17
Enhances: podman
Enhances: cri-o

%description
%{summary}
%{repo} provides a library for applications looking to use
the Container Pod concept popularized by Kubernetes.

%prep
%autosetup -Sgit
sed -i '/$(MAKE) -C docs install/d' Makefile
sed -i 's/HOOK_BIN_DIR/\%{_usr}\/libexec\/oci\/hooks.d/' %{name}.json
sed -i '/$(HOOK_DIR)\/%{name}.json/d' Makefile

%build
export GO111MODULE=off
export GOPATH=$(pwd):$(pwd)/_build
export CGO_CFLAGS="%{optflags} -D_GNU_SOURCE -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64"

mkdir _build
pushd _build
mkdir -p src/%{provider}.%{provider_tld}/%{project}
ln -s ../../../../ src/%{import_path}
popd
ln -s vendor src

export GOPATH=$(pwd)/_build:$(pwd)
export LDFLAGS="-X main.version=%{version}"
%gobuild -o bin/%{name} %{import_path}

pushd docs
go-md2man -in %{name}.md -out %{name}.1
popd

%install
%{__make} DESTDIR=%{buildroot} PREFIX=%{_prefix} install-nobuild
%{__make} DESTDIR=%{buildroot} PREFIX=%{_prefix} GOMD2MAN=go-md2man -C docs install-nobuild

%check
%if 0%{?with_check}
# Since we aren't packaging up the vendor directory we need to link
# back to it somehow. Hack it up so that we can add the vendor
# directory from BUILD dir as a gopath to be searched when executing
# tests from the BUILDROOT dir.
ln -s ./ ./vendor/src # ./vendor/src -> ./vendor

export GOPATH=%{buildroot}/%{gopath}:$(pwd)/vendor:%{gopath}

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest %{import_path}/src/%{name}
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

%changelog
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
