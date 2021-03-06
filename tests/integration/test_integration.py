# coding: utf-8

# Copyright 2018 www.privaz.io Valletech AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import ssl
import os
from pyone import HOST_STATES, HOST_STATUS, OneException, OneAuthenticationException

# Note that we import a TesterServer that has extends with record/replay fixtures
from pyone.tester import OneServerTester as OneServer

# Deprecated utility, testing backward compatibility
from pyone.util import one2dict

# Select whether to record or replay fixtures

fixture_replay = True

# Capture OpenNebula Session parameters from environment or hardcoded...
test_session = os.getenv("PYONE_SESSION", "oneadmin:onepass")
test_endpoint = os.getenv("PYONE_ENDPOINT", 'https://192.168.121.55/RPC2')

# Testing mode: replay or record fixtures, and fixture path

fixture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')

# Disable SSL checks for TEST environment only, and deal with Centos, see issue #13
if "PYTHONHTTPSVERIFY" in os.environ:
    one = OneServer(test_endpoint, fixture_path=fixture_path, fixture_replay=fixture_replay, session=test_session)
else:
    one = OneServer(test_endpoint, fixture_path=fixture_path, fixture_replay=fixture_replay, session=test_session, context=ssl._create_unverified_context())


class IntegrationTests(unittest.TestCase):

    def setUp(self):
        """
        Will define test resources from the pool
        anyone should do
        :return:
        """
        if not hasattr(self, 'testHostAId'):
            one.set_fixture_unit_test("setup")
            hosts = one.hostpool.info()
            self.testHostAId = hosts.HOST[0].ID
            self.testHostBId = hosts.HOST[1].ID
            vms = one.vmpool.info(-2, -1, -1, -1)
            self.testVMAid = vms.VM[0].ID

    def test_pool_info(self):
        one.set_fixture_unit_test("test_pool_info")
        hostpool = one.hostpool.info()
        self.assertGreater(len(hostpool.HOST), 0)
        host = hostpool.HOST[0]
        self.assertIn(HOST_STATES(host.STATE), [HOST_STATES.MONITORED, HOST_STATES.INIT])

    def test_auth_error(self):
        with self.assertRaises(OneAuthenticationException):
            one.set_fixture_unit_test("test_auth_error")
            # Disable SSL checks for TEST environment only, and deal with Centos, see issue #13
            if "PYTHONHTTPSVERIFY" in os.environ:
                xone = OneServer(test_endpoint, fixture_path=fixture_path, fixture_replay=fixture_replay, session="oneadmin:invalidpass")
            else:
                xone = OneServer(test_endpoint, fixture_path=fixture_path, fixture_replay=fixture_replay, session="oneadmin:invalidpass", context=ssl._create_unverified_context())
            xone.hostpool.info()

    def test_market_info(self):
        one.set_fixture_unit_test("test_market_info")
        marketpool = one.marketpool.info()
        self.assertGreater(len(marketpool.MARKETPLACE), 0)
        m0 = marketpool.MARKETPLACE[0]
        self.assertEqual(m0.NAME, "OpenNebula Public")

    def test_vm_pool(self):
        one.set_fixture_unit_test("test_vm_pool")
        vmpool = one.vmpool.info(-2, -1, -1, -1)
        vm0 = vmpool.VM[0]
        self.assertEqual(vm0.UNAME, "oneadmin")

    def test_invalid_method(self):
        with self.assertRaises(OneException):
            one.set_fixture_unit_test("test_invalid_method")
            one.invalid.api.call()

    def test_template_attribute_vector_parameter(self):
        one.set_fixture_unit_test("test_template_attribute_vector_parameter")
        one.host.update(self.testHostAId,  {"LABELS": "HD,LOWPOWER"}, 1)
        host = one.host.info(self.testHostAId)
        self.assertEqual(host.TEMPLATE['LABELS'], u"HD,LOWPOWER")

    def test_xml_template_parameter(self):
        one.set_fixture_unit_test("test_xml_template_parameter")
        one.host.update(self.testHostBId,
            {
                'TEMPLATE': {
                    'LABELS': 'SSD',
                    'MAX_CPU': '176'
                }
            }, 1)
        host = one.host.info(self.testHostBId)
        self.assertEqual(host.TEMPLATE['LABELS'], u"SSD")
        self.assertEqual(host.TEMPLATE['MAX_CPU'], u"176")

    def test_empty_dictionary(self):
        with self.assertRaises(Exception):
            one.set_fixture_unit_test("test_empty_dictionary")
            one.host.update(self.testHostAId, {}, 1)

    def test_retrieve_template_as_DOM_no_longer_working(self):
        with self.assertRaises(AttributeError):
            one.set_fixture_unit_test("test_retrieve_template_as_DOM_no_longer_working")
            host = one.host.info(self.testHostAId)
            template = host.TEMPLATE.toDOM()
            arch = template.getElementsByTagName('ARCH')[0].firstChild.nodeValue
            self.assertEqual(arch, 'x86_64')

    def test_retrieve_template_as_deprecated_dict(self):
        one.set_fixture_unit_test("test_retrieve_template_as_deprecated_dict")
        host = one.host.info(self.testHostAId)
        tdict = one2dict(host.TEMPLATE)
        arch = tdict['TEMPLATE']['ARCH']
        self.assertEqual(arch, 'x86_64')

    def test_retrieve_template_as_new_dict(self):
        one.set_fixture_unit_test("test_retrieve_template_as_new_dict")
        host = one.host.info(self.testHostAId)
        arch = host.TEMPLATE['ARCH']
        self.assertEqual(arch, 'x86_64')

    def test_international_characters_issue_006(self):
        one.set_fixture_unit_test("test_international_characters_issue_006")
        one.host.update(self.testHostAId,
            {
                'TEMPLATE': {
                    'NOTES': 'Hostname is: ESPAÑA',
                }
            }, 1)
        host = one.host.info(self.testHostAId)
        self.assertIn(host.TEMPLATE['NOTES'], [u"Hostname is: ESPAÑA"])

    def test_modify_template(self):
        one.set_fixture_unit_test("test_modify_template")
        host = one.host.info(self.testHostAId)
        host.TEMPLATE["NOTES"]=u"Hostname is: España"
        one.host.update(self.testHostAId, host.TEMPLATE, 1)
        host2 = one.host.info(self.testHostAId)
        self.assertIn(host2.TEMPLATE['NOTES'], [u"Hostname is: España"])


    def test_vm_info(self):
        one.set_fixture_unit_test("test_vm_info")
        vm = one.vm.info(self.testVMAid)
        labels = vm.USER_TEMPLATE.get('LABELS', "")
        culsterId = vm.TEMPLATE['DISK']['CLUSTER_ID']
        self.assertEqual(vm.ID,self.testVMAid)

    def test_market_info(self):
        one.set_fixture_unit_test("test_market_info")
        markets = one.marketpool.info()
        self.assertEqual(markets.MARKETPLACE[0].NAME, "OpenNebula Public")

    def test_maketplace_app_info(self):
        one.set_fixture_unit_test("test_maketplace_app_info")
        maketplace_apps= one.marketapppool.info(-2, -1, -1)
        self.assertEqual(maketplace_apps.MARKETPLACEAPP[0].GNAME, 'oneadmin')

    def test_app_export(self):
        one.set_fixture_unit_test("test_app_export")
        one.marketapp.export(6)

    def test_datastore_info(self):
        one.set_fixture_unit_test("test_datastore_info")
        datastores = one.datastorepool.info()
        self.assertEqual(datastores.DATASTORE[0].GNAME,"oneadmin")


    def test_marshalling_enums(self):
        one.set_fixture_unit_test("test_marshalling_enums")
        self.assertTrue(one.host.status(self.testHostAId, HOST_STATUS.ENABLED))
