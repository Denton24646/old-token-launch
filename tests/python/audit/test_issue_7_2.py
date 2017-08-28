from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed
class TestContract(AbstractTestContracts): 
    """
    run test with python ­-m unittest tests.python.audit.test_issue_7_2
    This test case shows the integer underflow in calcTokenPrice
    """

    # constants from tests/python/ducht_auction/test_dutch_auction.py
    BLOCKS_PER_DAY = 6000
    AUCTION_DURATION_IN_BLOCKS = 30000
    TOTAL_TOKENS = 100000000 * 10**18 # 100 million
    MAX_TOKENS_SOLD = 23700000 # 30 million
    WAITING_PERIOD = 60*60*24*7
    FUNDING_GOAL = 62500 * 10**18 # 62,500 Ether ~ 25 million dollars
    START_PRICE = 78125000000000000
    MAX_GAS = 150000  # Kraken gas limit

    def __init__(self, *args, **kwargs):
        super(TestContract, self).__init__(*args, **kwargs)

    def test(self):
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
        # Create dutch auction with ceiling of 62.5k Ether and price factor of 78125000000000000
        self.dutch_auction = self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 62500 * 10** 18, 78125000000000000, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS))
        self.s.mine()
        # Create crowdsale controller
        self.crowdsale_controller = self.create_contract('CrowdsaleController/CrowdsaleController.sol',
                                                    params=(self.multisig_wallet.address, self.dutch_auction, 2500000000000000))
        self.s.mine()
        # Get the omega token contract that the crowdsale controller deployed
        omega_token_address = self.crowdsale_controller.omegaToken()
        omega_token_abi = self.create_abi('Tokens/OmegaToken.sol')
        self.omega_token = self.contract_at(omega_token_address, omega_token_abi)
        # Setup dutch auction
        self.dutch_auction.setup(self.omega_token.address, self.crowdsale_controller.address)
        self.crowdsale_controller.startPresale()
        # Finish the presale
        self.crowdsale_controller.usdContribution(accounts[8], 100*10**18)
        # Start auction
        start_auction_data = self.dutch_auction.translator.encode('startAuction', [])
        self.multisig_wallet.submitTransaction(self.dutch_auction.address, 0, start_auction_data, sender=keys[wa_1])
        # After auction started, funding goal cannot be changed anymore
        self.assertEqual(self.dutch_auction.ceiling(), self.FUNDING_GOAL)
        # First price
        price_day_0 = self.dutch_auction.calcTokenPrice()
        # After 5 days and 5 hours (1 hour = 250 block)
        # startPrice ­ (15097573839662448 * (block.number ­ startBlock) / 6000);
        # will underflow
        self.s.head_state.block_number += self.BLOCKS_PER_DAY*5 + 1250
        price_final_price = self.dutch_auction.calcTokenPrice()
        print("First price: "+str(price_day_0)) 
        print("Final price: "+str(price_final_price))
        # Overflow, price day 0 < price_final_price self.assertGreater(price_day_0, price_final_price)
        self.assertGreater(price_day_0, price_final_price)
