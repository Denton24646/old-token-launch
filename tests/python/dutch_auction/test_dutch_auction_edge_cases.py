from ..abstract_test import AbstractTestContracts, accounts, keys

class TestContract(AbstractTestContracts):
    """
    run test with python -m unittest tests.python.dutch_auction.test_dutch_auction_edge_cases
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
        # Fails if funding goal is 0
        self.assert_tx_failed(lambda: self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 0,  78125000000000000, self.FINAL_PRICE_MIN, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS)))
        # Fails if start price is 0
        self.assert_tx_failed(lambda: self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 625000*10**18,  0, self.FINAL_PRICE_MIN, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS)))
        # Fails if final price min is 0
        self.assert_tx_failed(lambda: self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 625000*10**18,  78125000000000000, 0, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS)))
        # Fails if blocks per day is great then auction duration in blocks
        self.assert_tx_failed(lambda: self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 625000*10**18,  78125000000000000, self.FINAL_PRICE_MIN, 5, 1)))
        # Fails if final price min is greater then start price
        self.assert_tx_failed(lambda: self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 625000*10**18,  78125000000000000, 78125000000000000 + 1, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS)))
        # Fails if final price min is equal to start price
        self.assert_tx_failed(lambda: self.create_contract('DutchAuction/DutchAuction.sol',
                                                  params=(self.multisig_wallet.address, 625000*10**18,  78125000000000000, 78125000000000000, self.BLOCKS_PER_DAY, self.AUCTION_DURATION_IN_BLOCKS)))
