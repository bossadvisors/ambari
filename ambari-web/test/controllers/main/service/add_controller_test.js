/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var App = require('app');
require('controllers/wizard');
require('controllers/main/service/add_controller');
var addServiceController = null;

describe('App.AddServiceController', function() {

  beforeEach(function () {
    addServiceController = App.AddServiceController.create({});
  });

  describe('#installAdditionalClients', function() {

    var t = {
      additionalClients: {
        componentName: "TEZ_CLIENT",
        hostNames: ["hostName1", "hostName2"]
      },
      additionalClientsWithoutHosts: {
        componentName: "TEZ_CLIENT",
        hostNames: []
      },
      RequestInfo: {
        "context": Em.I18n.t('requestInfo.installHostComponent') + ' ' + App.format.role("TEZ_CLIENT"),
        "query": "HostRoles/component_name=TEZ_CLIENT&HostRoles/host_name.in(hostName1,hostName2)"
      },
      Body: {
        HostRoles: {
          state: 'INSTALLED'
        }
      }
    };

    beforeEach(function () {
      sinon.spy($, 'ajax');
      sinon.stub(App, 'get', function(k) {
        if ('clusterName' === k) return 'tdk';
        return Em.get(App, k);
      });
    });

    afterEach(function () {
      $.ajax.restore();
      App.get.restore();
    });

    it('send request to install client', function () {
      addServiceController.set("content.additionalClients", [t.additionalClients]);
      addServiceController.installAdditionalClients();
      expect($.ajax.calledOnce).to.equal(true);

      expect(JSON.parse($.ajax.args[0][0].data).Body).to.deep.eql(t.Body);
      expect(JSON.parse($.ajax.args[0][0].data).RequestInfo).to.eql(t.RequestInfo);
    });

    it('should not send request to install client', function () {
      addServiceController.set("content.additionalClients", [t.additionalClientsWithoutHosts]);
      expect($.ajax.called).to.be.false;
    });

  });

  describe('#generateDataForInstallServices', function() {
    var tests = [{
      selected: ["YARN","HBASE"],
      res: {
        "context": Em.I18n.t('requestInfo.installServices'),
        "ServiceInfo": {"state": "INSTALLED"},
        "urlParams": "ServiceInfo/service_name.in(YARN,HBASE)"
      }
    },
    {
      selected: ['OOZIE'],
      res: {
        "context": Em.I18n.t('requestInfo.installServices'),
        "ServiceInfo": {"state": "INSTALLED"},
        "urlParams": "ServiceInfo/service_name.in(OOZIE,HDFS,YARN,MAPREDUCE2)"
      }
    }];
    tests.forEach(function(t){
      it('should generate data with ' + t.selected.join(","), function () {
        expect(addServiceController.generateDataForInstallServices(t.selected)).to.be.eql(t.res);
      });
    });
  });

  describe('#saveServices', function() {
    beforeEach(function() {
      sinon.stub(addServiceController, 'setDBProperty', Em.K);
    });

    afterEach(function() {
      addServiceController.setDBProperty.restore();
    });

    var tests = [
      {
        appService: [
          Em.Object.create({ serviceName: 'HDFS' }),
          Em.Object.create({ serviceName: 'KERBEROS' })
        ],
        stepCtrlContent: Em.Object.create({
          content: Em.A([
            Em.Object.create({ serviceName: 'HDFS', isInstalled: true, isSelected: true }),
            Em.Object.create({ serviceName: 'YARN', isInstalled: false, isSelected: true })
          ])
        }),
        e: {
          selected: ['YARN'],
          installed: ['HDFS', 'KERBEROS']
        }
      },
      {
        appService: [
          Em.Object.create({ serviceName: 'HDFS' }),
          Em.Object.create({ serviceName: 'STORM' })
        ],
        stepCtrlContent: Em.Object.create({
          content: Em.A([
            Em.Object.create({ serviceName: 'HDFS', isInstalled: true, isSelected: true }),
            Em.Object.create({ serviceName: 'YARN', isInstalled: false, isSelected: true }),
            Em.Object.create({ serviceName: 'MAPREDUCE2', isInstalled: false, isSelected: true })
          ])
        }),
        e: {
          selected: ['YARN', 'MAPREDUCE2'],
          installed: ['HDFS', 'STORM']
        }
      }
    ];

    var message = '{0} installed, {1} selected. Installed list should be {2} and selected - {3}';
    tests.forEach(function(test) {
      var installed = test.appService.mapProperty('serviceName');
      var selected = test.stepCtrlContent.get('content').filterProperty('isSelected', true)
        .filterProperty('isInstalled', false).mapProperty('serviceName');
      it(message.format(installed, selected, test.e.installed, test.e.selected), function() {
        sinon.stub(App.Service, 'find').returns(test.appService);
        addServiceController.saveServices(test.stepCtrlContent);
        App.Service.find.restore();
        var savedServices = addServiceController.setDBProperty.withArgs('services').args[0][1];
        expect(savedServices.selectedServices).to.have.members(test.e.selected);
        expect(savedServices.installedServices).to.have.members(test.e.installed);
      });
    });
  });
});
