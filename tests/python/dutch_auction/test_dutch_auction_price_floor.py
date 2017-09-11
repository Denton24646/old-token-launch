from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed

class TestContract(AbstractTestContracts):
    """
    run test with python -m unittest tests.python.dutch_auction.test_dutch_auction_price_floor
    """

    BLOCKS_PER_DAY = 6000
    AUCTION_DURATION_IN_BLOCKS = 30000
    FINAL_PRICE_MIN = 2637130801687760
    MIN_PRESALE_TOKENS = 2000000;
    DUTCH_AUCTION_USD_VALUE_CAP = 25000000;
    PRESALE_USD_VALUE_CAP = 5000000;
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
        # Create dutch auction
        self.dutch_auction = self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, self.FUNDING_GOAL+1 , self.START_PRICE+1, self.FINAL_PRICE_MIN+1, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS))
        self.s.mine()
        # Create crowdsale controller
        self.crowdsale_controller = self.create_contract('CrowdsaleController/CrowdsaleController.sol', 
                                                        params=(self.multisig_wallet.address, self.dutch_auction, self.MIN_PRESALE_TOKENS, self.DUTCH_AUCTION_USD_VALUE_CAP, self.PRESALE_USD_VALUE_CAP))
        self.s.mine()
        # Get the omega token contract that the crowdsale controller deployed
        omega_token_address = self.crowdsale_controller.omegaToken()
        omega_token_abi = self.create_abi('Tokens/OmegaToken.sol')
        self.omega_token = self.contract_at(omega_token_address, omega_token_abi)
        # Setup dutch auction
        self.dutch_auction.setup(self.omega_token.address, self.crowdsale_controller.address)
        # Run presale
        self.crowdsale_controller.startPresale()
        buyer_1 = 5
        # 100%
        percent_of_presale_1 = 100 * 10 ** 18
        self.crowdsale_controller.usdContribution(accounts[buyer_1], percent_of_presale_1)
        # Start auction
        start_auction_data = self.dutch_auction.translator.encode('startAuction', [])
        self.multisig_wallet.submitTransaction(self.dutch_auction.address, 0, start_auction_data, sender=keys[wa_1])
        old_block_number = self.s.head_state.block_number
        self.s.head_state.block_number += self.BLOCKS_PER_DAY * 5
        self.dutch_auction.updateStage()
        assert self.dutch_auction.stage() == 3
        self.omega_token.balanceOf(self.dutch_auction.address) == 23700000*10**18
        self.crowdsale_controller.presaleTokenSupply() == 6300000*10**18
        self.s.head_state.block_number = old_block_number
        self.crowdsale_controller.stage() == 4
        self.s.head_state.timestamp += self.WAITING_PERIOD + 1
        self.crowdsale_controller.updateStage()
        assert self.crowdsale_controller.stage() == 5
        before_allowance = self.omega_token.allowance(self.dutch_auction.address, self.crowdsale_controller.address)
        assert before_allowance == 23700000*10**18
        self.crowdsale_controller.forwardTokensToWallet()
        after_allowance = self.omega_token.allowance(self.dutch_auction.address, self.crowdsale_controller.address)
        assert after_allowance == 0
        assert self.omega_token.balanceOf(self.multisig_wallet.address) == 93700000*10**18
        assert self.omega_token.balanceOf(self.dutch_auction.address) == 0 
