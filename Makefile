SPECFILE=docbook-lint.spec
NAME=$(shell awk '/Name:/ { print $$2 }' $(SPECFILE))
VERSION=$(shell awk '/Version:/ { print $$2 }' $(SPECFILE))
RELEASE=$(shell sed -e 's/%/ /' $(SPECFILE) | awk -F' ' '/Release:/ { print $$2 }')


ifndef WORKDIR
WORKDIR := $(shell pwd)
endif
SRCRPMDIR ?= $(WORKDIR)
BUILDDIR ?= $(WORKDIR)
RPMDIR ?= $(WORKDIR)
ifndef SOURCEDIR
SOURCEDIR := $(shell pwd)/dist
endif

ifndef RPM_DEFINES
RPM_DEFINES = --define "_sourcedir $(SOURCEDIR)" \
		--define "_builddir $(BUILDDIR)" \
		--define "_srcrpmdir $(SRCRPMDIR)" \
		--define "_rpmdir $(RPMDIR)" \
                $(DIST_DEFINES)
endif

all: local-rpm

local-rpm: $(NAME)-$(VERSION)-$(RELEASE).noarch.rpm

local-srpm: $(NAME)-$(VERSION)-$(RELEASE).src.rpm

tarball:
	python setup.py sdist

$(NAME)-$(VERSION)-$(RELEASE).noarch.rpm: $(SPECFILE)
	rpmbuild -ba $(RPM_DEFINES) $(SPECFILE)

$(NAME)-$(VERSION)-$(RELEASE).src.rpm: $(SPECFILE)
	rpmbuild -bs $(RPM_DEFINES) $(SPECFILE)

