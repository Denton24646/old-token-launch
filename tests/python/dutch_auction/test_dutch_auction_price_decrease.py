from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed

class TestContract(AbstractTestContracts):
    """
    run test with python -m unittest tests.python.dutch_auction.test_dutch_auction_price_decrease
    """

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
        # Create dutch auction with ceiling of 62.5k Ether and price factor of 78125000000000000 (start price in wei per token for duch)
        self.dutch_auction = self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 62500 * 10**18,  78125000000000000, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS))
        self.s.mine()
        # Create crowdsale controller to get Omega token
        self.crowdsale_controller = self.create_contract('CrowdsaleController/CrowdsaleController.sol', 
                                                        params=(self.multisig_wallet.address, self.dutch_auction, 2500000000000000))
        self.s.mine()
        # Get the omega token contract that the crowdsale controller deployed
        omega_token_address = self.crowdsale_controller.omegaToken()
        omega_token_abi = self.create_abi('Tokens/OmegaToken.sol')
        self.omega_token = self.contract_at(omega_token_address, omega_token_abi)
        # Setup dutch auction
        self.dutch_auction.setup(self.omega_token.address, self.crowdsale_controller.address)
        # Start the presale from crowdsale controller
        self.crowdsale_controller.startPresale()
        # Finish the presale
        self.crowdsale_controller.usdContribution(accounts[8], 100*10**18)
        # Start auction
        start_auction_data = self.dutch_auction.translator.encode('startAuction', [])
        self.multisig_wallet.submitTransaction(self.dutch_auction.address, 0, start_auction_data, sender=keys[wa_1])
        # Auction decreases in final valuation value by ~ 180 million each day
        # Change per day in wei
        decrease_per_day =  15097573839662448
        # Check the token price
        day_0_token_price = self.dutch_auction.calcTokenPrice()
        self.assertEqual(day_0_token_price, 78125000000000000)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY
        # Check the token price
        day_1_token_price = self.dutch_auction.calcTokenPrice()
        self.assertEqual(day_1_token_price, 78125000000000000 - decrease_per_day)
        bidder_1 = 3
        value_1 = 10 * 10**18 # 10K Ether
        self.dutch_auction.bid(sender=keys[bidder_1], value=value_1)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY
        # Check the token price
        day_2_token_price = self.dutch_auction.calcTokenPrice() 
        self.assertEqual(day_2_token_price, 78125000000000000 - decrease_per_day * 2)
        bidder_2 = 4
        value_2 = 10 * 10**18 # 10K Ether
        self.dutch_auction.bid(sender=keys[bidder_2], value=value_2)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY
        # self.s.chain.state.block_number = self.s.head_state.block_number
        # Check the token price
        day_3_token_price = self.dutch_auction.calcTokenPrice() 
        self.assertEqual(day_3_token_price, 78125000000000000 - decrease_per_day * 3)
        bidder_3 = 5
        value_3 = 10 * 10**18 # 10K Ether
        self.dutch_auction.bid(sender=keys[bidder_3], value=value_3)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY
        # Check the token price
        day_4_token_price = self.dutch_auction.calcTokenPrice() 
        self.assertEqual(day_4_token_price, 78125000000000000 - decrease_per_day * 4)
        bidder_4 = 6
        value_4 = 10 * 10**18 # 10K Ether
        self.dutch_auction.bid(sender=keys[bidder_4], value=value_4)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY
        # Check the token price
        day_5_token_price = self.dutch_auction.calcTokenPrice()
        self.assertEqual(day_5_token_price, 78125000000000000 - decrease_per_day * 5)  
        # Auction ends after 5 days and no more bids are accepted
        bidder_5 = 7
        value_5 = 10 * 10**18 # 10K Ether
        self.assert_tx_failed(lambda: self.dutch_auction.bid(sender=keys[bidder_5], value=value_5))
        self.assertEqual(self.dutch_auction.calcTokenPrice(), self.dutch_auction.calcStopPrice())
        # Sale is over
        self.dutch_auction.updateStage()
        self.assertEqual(self.dutch_auction.stage(), 3)
        self.assertEqual(self.crowdsale_controller.stage(), 4)
        # Bidders claim their tokens throught the crowdsale controller after the waiting period is over
        self.s.head_state.timestamp += self.WAITING_PERIOD + 1
        self.crowdsale_controller.claimTokens(accounts[bidder_1])
        self.crowdsale_controller.claimTokens(accounts[bidder_2])
        self.crowdsale_controller.claimTokens(accounts[bidder_3])
        self.crowdsale_controller.claimTokens(accounts[bidder_4])
        self.assertEqual(round(int(self.omega_token.balanceOf(accounts[bidder_1])),-7),
                         round(int(value_1 * 10 ** 18 / self.dutch_auction.finalPrice()), -7))
        self.assertEqual(round(int(self.omega_token.balanceOf(accounts[bidder_2])),-7),
                         round(int(value_2 * 10 ** 18 / self.dutch_auction.finalPrice()), -7))
        self.assertEqual(round(int(self.omega_token.balanceOf(accounts[bidder_3])),-7),
                         round(int(value_3 * 10 ** 18 / self.dutch_auction.finalPrice()), -7))
        self.assertEqual(round(int(self.omega_token.balanceOf(accounts[bidder_4])),-7),
                         round(int(value_4 * 10 ** 18 / self.dutch_auction.finalPrice()), -7))
        
