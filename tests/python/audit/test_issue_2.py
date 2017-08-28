from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed

class TestContract(AbstractTestContracts):
    """
    The file has to be placed in tests/python/audit/test_issue_2.py
    run test with python -m unittest tests.python.audit.test_issue_2

    """

    BLOCKS_PER_DAY = 6000
    AUCTION_DURATION_IN_BLOCKS = 30000

    def __init__(self, *args, **kwargs):
        super(TestContract, self).__init__(*args, **kwargs)

    def test(self):
        owner = 0
        # Create wallet
        required_accounts = 1
        wa_1 = 1
        constructor_parameters = (
            [accounts[wa_1]],
            required_accounts
        )
        self.multisig_wallet = self.create_contract('Wallets/MultiSigWallet.sol',
                                                    params=constructor_parameters)
        self.s.mine()
        # Create dutch auction with ceiling of 2 billion and price factor of 200,000
        self.dutch_auction = self.create_contract('DutchAuction/DutchAuction.sol',
                                                    params=(self.multisig_wallet.address, 62500 * 10 ** 18, 78125000000000000, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS))
        self.s.mine()
        # Create crowdsale controller
        self.crowdsale_controller = self.create_contract('CrowdsaleController/CrowdsaleController.sol', 
                                                        params=(self.multisig_wallet.address, self.dutch_auction, 2500000000000000))
        self.s.mine()
        # Get the omega token contract that the crowdsale controller deployed
        presale_address = self.crowdsale_controller.presale()
        presale_abi = self.create_abi('Presale/Presale.sol')
        self.presale = self.contract_at(presale_address, presale_abi)

        self.crowdsale_controller.startPresale()

        buyer_1 = 3
        # 10%
        percent_of_presale_1 = 10 * 10 ** 18
        self.crowdsale_controller.usdContribution(accounts[buyer_1], percent_of_presale_1)
        # Second call with the same value, after this we have
        # presale.presaleAllocations[buyer_1] == 10 * 10 ** 18
        # but presale.totalSupply = 20 * 10 **18 (20%)
        self.crowdsale_controller.usdContribution(accounts[buyer_1], percent_of_presale_1)

        buyer_2 = 4
        # 90%
        percent_of_presale_2 = 90 * 10 ** 18
        # As it remains 80% in maxPercentLeft, the buyer 2 will have 80%
        self.crowdsale_controller.usdContribution(accounts[buyer_2], percent_of_presale_2)

        # Real value for the buyer_1 (10%)
        p1 = self.presale.presaleAllocations(accounts[buyer_1])
        # Real value for the buyer_2 (80%)
        p2 = self.presale.presaleAllocations(accounts[buyer_2])

        # the asseration fails
        # self.presale.percentOfPresaleSold() = 100%
        # p1 + p2 = 90%
        self.assertEqual(self.presale.percentOfPresaleSold(), p1 + p2)
