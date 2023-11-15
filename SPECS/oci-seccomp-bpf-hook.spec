%global with_check 0

%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0

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
Version: 1.2.9
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
* Mon Apr 24 2023 Jindrich Novy <jnovy@redhat.com> - 1.2.9-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.9
- Related: #2176055

* Thu Mar 09 2023 Jindrich Novy <jnovy@redhat.com> - 1.2.8-2
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.8
- Related: #2176055

* Tue Oct 18 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.8-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.8
- Related: #2123641

* Mon Oct 17 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.7-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.7
- Related: #2123641

* Tue Jul 12 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.6-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.6
- Related: #2061390

* Wed May 11 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.5-2
- BuildRequires: /usr/bin/go-md2man
- Related: #2061390

* Wed Mar 16 2022 Jindrich Novy <jnovy@redhat.com> - 1.2.5-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.5
- Related: #2061390

* Wed May 26 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.3-3
- change runc dependency to conflict
- Related: #1934415

* Wed May 19 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.3-2
- remove unneeded patch
- Related: #1934415

* Wed May 19 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.3-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.3
- fix build
- Related: #1934415

* Mon Feb 22 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.0-2
- revert back to 1.2.0 - build issues
- Related: #1883490

* Fri Feb 19 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.1-1
- update to
  https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.1
- require crun >= 0.17
- Related: #1883490

* Thu Jan 28 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.0-1
- revert back to 1.2.0 due to build issues
- Related: #1883490

* Thu Jan 28 2021 Jindrich Novy <jnovy@redhat.com> - 1.2.1-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.2.1
- Related: #1883490

* Tue Dec 08 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-2
- sync with RHEL8 devel branch
- Related: #1883490

* Wed Oct 21 2020 Jindrich Novy <jnovy@redhat.com> - 1.2.0-1
- synchronize with stream-container-tools-rhel8
- Related: #1883490

* Tue Aug 11 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.2-3
- propagate proper CFLAGS to CGO_CFLAGS to assure code hardening and optimization
- Related: #1821193

* Thu Jul 23 2020 Lokesh Mandvekar <lsm5@fedoraproject.org> - 1.1.2-2
- Resolves: #1857606

* Fri Jul 17 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.2-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.1.2
- Related: #1821193

* Thu Jun 18 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.1-1
- update to https://github.com/containers/oci-seccomp-bpf-hook/releases/tag/v1.1.1
- Related: #1821193

* Tue May 12 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.0-2
- exclude i686 arch as bcc, the build dependency is not built
  for it
- Related: #1821193

* Tue May 12 2020 Jindrich Novy <jnovy@redhat.com> - 1.1.0-1
- initial build for container-tools-rhel8
- Related: #1821193
