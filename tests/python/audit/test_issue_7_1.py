from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed

class TestContract(AbstractTestContracts): 
    """
    run test with python ­-m unittest tests.python.audit.test_issue_7_1
    This test case shows the integer underflow in the token left computation
    """

    # constant from tests/python/ducht_auction/test_dutch_auction.py
    BLOCKS_PER_DAY = 6000
    AUCTION_DURATION_IN_BLOCKS = 30000
    TOTAL_TOKENS = 100000000 * 10**18 # 100 million
    MAX_TOKENS_SOLD = 23700000 # 30 million
    WAITING_PERIOD = 60*60*24*7
    FUNDING_GOAL = 62500 * 10**18 # 62,500 Ether ~ 25 million dollars
    PRICE_FACTOR = 78125000000000000
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
                                                    params=(self.multisig_wallet.address,
        self.dutch_auction, 2500000000000000))
        self.s.mine()
        # Get the omega token contract that the crowdsale controller deployed
        omega_token_address = self.crowdsale_controller.omegaToken()
        omega_token_abi = self.create_abi('Tokens/OmegaToken.sol')
        self.omega_token = self.contract_at(omega_token_address, omega_token_abi)
        # Setup dutch auction
        self.dutch_auction.setup(self.omega_token.address, self.crowdsale_controller.address)
        self.crowdsale_controller.startPresale()
        buyer_1 = 1
        # Finish the presale
        self.crowdsale_controller.usdContribution(buyer_1, 100*10**18)
        # Start auction
        start_auction_data = self.dutch_auction.translator.encode('startAuction', [])
        self.multisig_wallet.submitTransaction(self.dutch_auction.address, 0, start_auction_data, sender=keys[wa_1])
        buyer_1 = 1
        value_1 = 1000000 * 10**18  # 1M Ether
        self.s.head_state.set_balance(accounts[buyer_1], value_1 * 2) # gives enough ether to the buyer
        self.dutch_auction.bid(sender=keys[buyer_1], value=value_1)
        # 5 days + 4 hours
        # 24 hours = 6000 blocks, 4 hours = (6000/24)*4 = 1000 
        self.s.head_state.block_number += self.BLOCKS_PER_DAY*5 + 1000
        
        # compute the token left
        finalPrice = self.dutch_auction.calcTokenPrice()
        totalReceived = self.dutch_auction.totalReceived()
        dutch_MAX_TOKENS_SOLD = self.omega_token.DUTCH_AUCTION_ALLOCATION()
        
        print('tokensLeft = '+str(dutch_MAX_TOKENS_SOLD - totalReceived * 10 **18 / finalPrice))

        # MAX_TOKENS_SOLD < totalReceived * 10 **18 / finalPrice
        # thereby there is an underflow in the computation of tokenLeft
        self.assertGreater(dutch_MAX_TOKENS_SOLD, totalReceived * 10 **18 / finalPrice)