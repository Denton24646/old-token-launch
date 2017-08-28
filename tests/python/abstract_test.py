from ethereum import utils
from ethereum.tools.tester import keys, accounts, TransactionFailed, ABIContract
from ethereum.tools import _solidity, tester as t
from ethereum.abi import ContractTranslator
# standard libraries
from unittest import TestCase
import os
import string

OWN_DIR = os.path.dirname(os.path.realpath(__file__))

class AbstractTestContracts(TestCase):

    def __init__(self, *args, **kwargs):
        super(AbstractTestContracts, self).__init__(*args, **kwargs)
        self.s = t.Chain({account: {'balance': 10**30}for account in t.accounts})
        t.gas_limit = 4712388
        

    @staticmethod
    def is_hex(s):
        return all(c in string.hexdigits for c in s)

    def assert_tx_failed(self, function_to_test, exception=TransactionFailed):
        snapshot = self.s.snapshot()
        self.assertRaises(exception, function_to_test)
        self.s.revert(snapshot)

    def get_dirs(self, path):
        abs_contract_path = os.path.realpath(os.path.join(OWN_DIR, '..', '..', 'contracts'))
        sub_dirs = [x[0] for x in os.walk(abs_contract_path)]
        extra_args = ' '.join(['{}={}'.format(d.split('/')[-1], d) for d in sub_dirs])
        path = '{}/{}'.format(abs_contract_path, path)
        return path, extra_args

    def contract_at(self, address, abi):
        return ABIContract(self.s, abi, address)

    def create_abi(self, path):
        path, extra_args = self.get_dirs(path)
        abi = _solidity.compile_last_contract(path, combined='abi', extra_args=extra_args)['abi']
        return ContractTranslator(abi)

    def create_contract(self, path, params=None, libraries=None, sender=None):
        contract_name = path.split('/')[1]
        contract_name += ':' + contract_name.split('.')[0]
        path, extra_args = self.get_dirs(path)
        if params:
            params = [x.address if isinstance(x, ABIContract) else x for x in params]
        compiler = t.languages['solidity']
        combined = _solidity.compile_file(path, combined='bin,abi', optimize=True, extra_args=extra_args)
        abi = combined[contract_name]['abi']
        ct = ContractTranslator(abi)
        code = combined[contract_name]['bin'] + (ct.encode_constructor_arguments(params) if params else b'')
        address = self.s.tx(sender=keys[sender if sender else 0], to=b'', value=0, startgas=4700000, data=code)
        return ABIContract(self.s, abi, address)
