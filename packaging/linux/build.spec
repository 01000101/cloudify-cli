%define _rpmdir /tmp

Name:           cloudify-%{DISTRO}-%{RELEASE}-cli
Version:        %{VERSION}
Release:        %{PRERELEASE}_b%{BUILD}
Summary:        Cloudify's CLI
Group:          Applications/Multimedia
License:        Apache 2.0
URL:            https://github.com/cloudify-cosmo/cloudify-cli
Vendor:         Gigaspaces Inc.
Prefix:         %{_prefix}
Packager:       Gigaspaces Inc.
BuildRoot:      %{_tmppath}/%{name}-root


%description

Cloudify's Command-Line Interface.



%prep

set +e
pip=$(which pip)
set -e

[ ! -z $pip ] || sudo curl --show-error --silent --retry 5 https://bootstrap.pypa.io/get-pip.py | sudo python2.7 &&
sudo pip install setuptools==18.1
sudo pip install wheel==0.24.0
sudo yum -y install git python-devel gcc
sudo curl http://cloudify-public-repositories.s3.amazonaws.com/cloudify-manager-blueprints/%{CORE_TAG_NAME}/cloudify-manager-blueprints.tar.gz -o /tmp/cloudify-manager-blueprints.tar.gz &&

alias python=python2.7


%build
%install

# Download or create wheels of all dependencies

sudo pip wheel virtualenv==13.1.0 --wheel-dir %{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-rest-client@%{CORE_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-dsl-parser@%{CORE_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-plugins-common@%{CORE_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-script-plugin@%{PLUGINS_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-fabric-plugin@%{PLUGINS_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-openstack-plugin@%{PLUGINS_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-aws-plugin@%{PLUGINS_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://%{GITHUB_USERNAME}:%{GITHUB_PASSWORD}@github.com/cloudify-cosmo/cloudify-vsphere-plugin@%{PLUGINS_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://%{GITHUB_USERNAME}:%{GITHUB_PASSWORD}@github.com/cloudify-cosmo/cloudify-softlayer-plugin@%{PLUGINS_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&
sudo pip wheel git+https://github.com/cloudify-cosmo/cloudify-cli@%{CORE_TAG_NAME} --wheel-dir=%{buildroot}/var/wheels/%{name} --find-links=%{buildroot}/var/wheels/%{name} &&

# Make directories
sudo mkdir -p %{buildroot}/cfy/cloudify/types &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins/fabric-plugin &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins/openstack-plugin &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins/diamond-plugin &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins/vsphere-plugin &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins/softlayer-plugin &&
sudo mkdir -p %{buildroot}/cfy/cloudify/plugins/aws-plugin &&
sudo mkdir -p %{buildroot}/cfy/cloudify/scripts &&
sudo mkdir -p %{buildroot}/cfy/cloudify-manager-blueprints-commercial &&

# Copy LICENSE file
sudo cp /vagrant/LICENSE %{buildroot}/cfy/ &&

# Download manager-blueprints
sudo tar -zxvf /tmp/cloudify-manager-blueprints.tar.gz --strip-components=1 -C %{buildroot}/cfy/cloudify-manager-blueprints-commercial &&

# Download/Copy plugin.yaml files to local plugins folder
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-fabric-plugin/%{PLUGINS_TAG_NAME}/plugin.yaml -o %{buildroot}/cfy/cloudify/plugins/fabric-plugin/plugin.yaml &&
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-openstack-plugin/%{PLUGINS_TAG_NAME}/plugin.yaml -o %{buildroot}/cfy/cloudify/plugins/openstack-plugin/plugin.yaml &&
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-diamond-plugin/%{PLUGINS_TAG_NAME}/plugin.yaml -o %{buildroot}/cfy/cloudify/plugins/diamond-plugin/plugin.yaml &&
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-aws-plugin/%{PLUGINS_TAG_NAME}/plugin.yaml -o %{buildroot}/cfy/cloudify/plugins/aws-plugin/plugin.yaml &&
sudo cp /tmp/cloudify-vsphere-plugin/plugin.yaml %{buildroot}/cfy/cloudify/plugins/vsphere-plugin &&
sudo cp /tmp/cloudify-softlayer-plugin/plugin.yaml %{buildroot}/cfy/cloudify/plugins/softlayer-plugin &&

# Download types.yaml
sudo curl http://getcloudify.org.s3.amazonaws.com/spec/cloudify/%{CORE_TAG_NAME}/types.yaml -o %{buildroot}/cfy/cloudify/types/types.yaml &&

# Download scripts
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/fs/mkfs.sh -o %{buildroot}/cfy/cloudify/scripts/mkfs.sh
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/fs/fdisk.sh -o %{buildroot}/cfy/cloudify/scripts/fdisk.sh
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/fs/mount.sh -o %{buildroot}/cfy/cloudify/scripts/mount.sh
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/fs/unmount.sh -o %{buildroot}/cfy/cloudify/scripts/unmount.sh
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/policies/host_failure.clj -o %{buildroot}/cfy/cloudify/scripts/host_failure.clj
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/policies/threshold.clj -o %{buildroot}/cfy/cloudify/scripts/threshold.clj
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/policies/ewma_stabilized.clj -o %{buildroot}/cfy/cloudify/scripts/ewma_stabilized.clj
sudo curl https://raw.githubusercontent.com/cloudify-cosmo/cloudify-manager/%{CORE_TAG_NAME}//resources/rest-service/cloudify/triggers/execute_workflow.clj -o %{buildroot}/cfy/cloudify/scripts/execute_workflow.clj

%pre
%post

if ! which virtualenv >> /dev/null; then
    pip install --use-wheel --no-index --find-links=/var/wheels/%{name} virtualenv
fi
virtualenv /cfy/env &&
/cfy/env/bin/pip install --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify --pre &&
/cfy/env/bin/pip install --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify-vsphere-plugin --pre &&
/cfy/env/bin/pip install --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify-softlayer-plugin --pre &&
/cfy/env/bin/pip install --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify-fabric-plugin --pre &&
/cfy/env/bin/pip install --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify-openstack-plugin --pre &&
/cfy/env/bin/pip install --use-wheel --no-index --find-links=/var/wheels/%{name} cloudify-aws-plugin --pre &&

# replace all https links at types.yaml to local paths for offline usage
sudo sed -i -e 's/https:\/\/raw\.githubusercontent\.com\/cloudify-cosmo\/cloudify-manager\/.*\/resources\/rest-service\/cloudify\/.*\//file:\/cfy\/cloudify\/scripts\//g' /cfy/cloudify/types/types.yaml &&

# Add import resolver configuration section to the Cloudify configuration file (config.yaml)
cat <<EOT >> /cfy/env/lib/python2.7/site-packages/cloudify_cli/resources/config.yaml &&

import_resolver:
  parameters:
    rules:
    - {'http://www.getcloudify.org/spec/cloudify/%{CORE_TAG_NAME}/types.yaml': 'file:/cfy/cloudify/types/types.yaml'}
    - {'http://www.getcloudify.org/spec/fabric-plugin/%{PLUGINS_TAG_NAME}': 'file:/cfy/cloudify/plugins/fabric-plugin'}
    - {'http://www.getcloudify.org/spec/openstack-plugin/%{PLUGINS_TAG_NAME}': 'file:/cfy/cloudify/plugins/openstack-plugin'}
EOT



echo "You can now source /cfy/env/bin/activate to start using Cloudify."

%preun
%postun

rm -rf /cfy
rm -rf /var/wheels/${name}


%files

%defattr(-,root,root)
/var/wheels/%{name}/*.whl
/cfy/LICENSE
/cfy/cloudify-manager-blueprints-commercial
/cfy/cloudify/types
/cfy/cloudify/scripts
/cfy/cloudify/plugins
# /cfy/cloudify/plugins/fabric-plugin/plugin.yaml
# /cfy/cloudify/plugins/openstack-plugin/plugin.yaml
# /cfy/cloudify/plugins/diamond-plugin/yaml
# /cfy/cloudify/plugins/vsphere-plugin/
# /cfy/cloudify/plugins/softlayer-plugin/
# /cfy/cloudify/plugins/aws-plugin/

