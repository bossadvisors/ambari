#!/usr/bin/env python

'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from mock.mock import MagicMock, call, patch
from stacks.utils.RMFTestCase import *
import os
import  resource_management.libraries.functions

origin_exists = os.path.exists
@patch.object(resource_management.libraries.functions, "check_process_status", new = MagicMock())
@patch.object(os.path, "exists", new=MagicMock(
    side_effect=lambda *args: origin_exists(args[0])
    if args[0][-2:] == "j2" else True))
class TestAppTimelineServer(RMFTestCase):
  COMMON_SERVICES_PACKAGE_DIR = "YARN/2.1.0.2.0/package"
  STACK_VERSION = "2.0.6"

  def test_configure_default(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/application_timeline_server.py",
                       classname="ApplicationTimelineServer",
                       command="configure",
                       config_file="default.json",
                       hdp_stack_version = self.STACK_VERSION,
                       target = RMFTestCase.TARGET_COMMON_SERVICES
    )

    self.assert_configure_default()
    self.assertNoMoreResources()

  def test_start_default(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/application_timeline_server.py",
                       classname="ApplicationTimelineServer",
                       command="start",
                       config_file="default.json",
                       hdp_stack_version = self.STACK_VERSION,
                       target = RMFTestCase.TARGET_COMMON_SERVICES
    )

    self.assert_configure_default()

    pid_check_cmd = 'ls /var/run/hadoop-yarn/yarn/yarn-yarn-timelineserver.pid >/dev/null 2>&1 && ps -p `cat /var/run/hadoop-yarn/yarn/yarn-yarn-timelineserver.pid` >/dev/null 2>&1'
    self.assertResourceCalled('File', '/var/run/hadoop-yarn/yarn/yarn-yarn-timelineserver.pid',
                              not_if=pid_check_cmd,
                              action=['delete'])

    self.assertResourceCalled('Execute', 'ulimit -c unlimited; export HADOOP_LIBEXEC_DIR=/usr/lib/hadoop/libexec && /usr/lib/hadoop-yarn/sbin/yarn-daemon.sh --config /etc/hadoop/conf start timelineserver',
                              not_if=pid_check_cmd,
                              user='yarn')
    self.assertResourceCalled('Execute', pid_check_cmd,
                              initial_wait=5,
                              not_if=pid_check_cmd,
                              user='yarn')
    self.assertNoMoreResources()

  def test_stop_default(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/application_timeline_server.py",
                       classname="ApplicationTimelineServer",
                       command="stop",
                       config_file="default.json",
                       hdp_stack_version = self.STACK_VERSION,
                       target = RMFTestCase.TARGET_COMMON_SERVICES
    )

    self.assertResourceCalled('Execute', 'export HADOOP_LIBEXEC_DIR=/usr/lib/hadoop/libexec && /usr/lib/hadoop-yarn/sbin/yarn-daemon.sh --config /etc/hadoop/conf stop timelineserver',
                              user='yarn')

    self.assertResourceCalled('File', '/var/run/hadoop-yarn/yarn/yarn-yarn-timelineserver.pid',
                              action=['delete'])
    self.assertNoMoreResources()

  def assert_configure_default(self):
    self.assertResourceCalled('Directory', '/var/run/hadoop-yarn',
                              owner = 'yarn',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/run/hadoop-yarn/yarn',
                              owner = 'yarn',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/log/hadoop-yarn/yarn',
                              owner = 'yarn',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/run/hadoop-mapreduce',
                              owner = 'mapred',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/run/hadoop-mapreduce/mapred',
                              owner = 'mapred',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/log/hadoop-mapreduce',
                              owner = 'mapred',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/log/hadoop-mapreduce/mapred',
                              owner = 'mapred',
                              group = 'hadoop',
                              recursive = True,
                              )
    self.assertResourceCalled('Directory', '/var/log/hadoop-yarn',
                              owner = 'yarn',
                              recursive = True,
                              ignore_failures = True,
                              )
    self.assertResourceCalled('XmlConfig', 'core-site.xml',
                              owner = 'hdfs',
                              group = 'hadoop',
                              mode = 0644,
                              conf_dir = '/etc/hadoop/conf',
                              configurations = self.getConfig()['configurations']['core-site'],
                              configuration_attributes = self.getConfig()['configuration_attributes']['core-site']
                              )
    self.assertResourceCalled('XmlConfig', 'mapred-site.xml',
                              owner = 'yarn',
                              group = 'hadoop',
                              mode = 0644,
                              conf_dir = '/etc/hadoop/conf',
                              configurations = self.getConfig()['configurations']['mapred-site'],
                              configuration_attributes = self.getConfig()['configuration_attributes']['mapred-site']
                              )
    self.assertResourceCalled('XmlConfig', 'yarn-site.xml',
                              owner = 'yarn',
                              group = 'hadoop',
                              mode = 0644,
                              conf_dir = '/etc/hadoop/conf',
                              configurations = self.getConfig()['configurations']['yarn-site'],
                              configuration_attributes = self.getConfig()['configuration_attributes']['yarn-site']
                              )
    self.assertResourceCalled('XmlConfig', 'capacity-scheduler.xml',
                              owner = 'yarn',
                              group = 'hadoop',
                              mode = 0644,
                              conf_dir = '/etc/hadoop/conf',
                              configurations = self.getConfig()['configurations']['capacity-scheduler'],
                              configuration_attributes = self.getConfig()['configuration_attributes']['capacity-scheduler']
                              )
    self.assertResourceCalled('Directory', '/var/log/hadoop-yarn/timeline',
                              owner = 'yarn',
                              group = 'hadoop',
                              recursive = True,
                              recursive_permission = True
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/yarn.exclude',
                              owner = 'yarn',
                              group = 'hadoop',
                              )
    self.assertResourceCalled('File', '/etc/security/limits.d/yarn.conf',
                              content = Template('yarn.conf.j2'),
                              mode = 0644,
                              )
    self.assertResourceCalled('File', '/etc/security/limits.d/mapreduce.conf',
                              content = Template('mapreduce.conf.j2'),
                              mode = 0644,
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/yarn-env.sh',
                              content = InlineTemplate(self.getConfig()['configurations']['yarn-env']['content']),
                              owner = 'yarn',
                              group = 'hadoop',
                              mode = 0755,
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/mapred-env.sh',
                              content = InlineTemplate(self.getConfig()['configurations']['mapred-env']['content']),
                              owner = 'hdfs',
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/taskcontroller.cfg',
                              content = Template('taskcontroller.cfg.j2'),
                              owner = 'hdfs',
                              )
    self.assertResourceCalled('XmlConfig', 'mapred-site.xml',
                              owner = 'mapred',
                              group = 'hadoop',
                              conf_dir = '/etc/hadoop/conf',
                              configurations = self.getConfig()['configurations']['mapred-site'],
                              configuration_attributes = self.getConfig()['configuration_attributes']['mapred-site']
                              )
    self.assertResourceCalled('XmlConfig', 'capacity-scheduler.xml',
                              owner = 'hdfs',
                              group = 'hadoop',
                              conf_dir = '/etc/hadoop/conf',
                              configurations = self.getConfig()['configurations']['capacity-scheduler'],
                              configuration_attributes = self.getConfig()['configuration_attributes']['capacity-scheduler']
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/fair-scheduler.xml',
                              owner = 'mapred',
                              group = 'hadoop',
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/ssl-client.xml.example',
                              owner = 'mapred',
                              group = 'hadoop',
                              )
    self.assertResourceCalled('File', '/etc/hadoop/conf/ssl-server.xml.example',
                              owner = 'mapred',
                              group = 'hadoop',
                              )


  def test_status(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/application_timeline_server.py",
                       classname="ApplicationTimelineServer",
                       command="status",
                       config_file="default.json",
                       hdp_stack_version = self.STACK_VERSION,
                       target = RMFTestCase.TARGET_COMMON_SERVICES
    )

    self.assertResourceCalled('Execute', 'mv /var/run/hadoop-yarn/yarn/yarn-yarn-historyserver.pid /var/run/hadoop-yarn/yarn/yarn-yarn-timelineserver.pid',
        only_if = 'test -e /var/run/hadoop-yarn/yarn/yarn-yarn-historyserver.pid',
    )
    self.assertNoMoreResources()
