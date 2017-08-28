from ..abstract_test import AbstractTestContracts, utils, accounts, keys, TransactionFailed

class TestContract(AbstractTestContracts):
    """
    run test with python -m unittest tests.python.open_window.test_open_window
    """

    def __init__(self, *args, **kwargs):
        super(TestContract, self).__init__(*args, **kwargs)
        
    def test(self):
        token_supply = 14200000 * 10 ** 18
        dutch_auction_address = accounts[2]
        crowdsale_controller_address = accounts[0]
        price = 1 * 10**16# .01 Ether per token
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
        self.omega_token= self.create_contract('Tokens/OmegaToken.sol',
                                                  params=(dutch_auction_address, self.multisig_wallet.address))
        self.s.mine()
        self.open_window = self.create_contract('OpenWindow/OpenWindow.sol')
        # Transfer necessary funds to the open window sale
        self.omega_token.transfer(self.open_window.address, token_supply, sender=keys[2])
        # Setup the open window sale
        self.open_window.setupSale(token_supply, price, self.multisig_wallet.address, self.omega_token.address)
        # Open window contract initializes with the correct values
        self.assertEqual(utils.remove_0x_head(self.open_window.crowdsaleController()), crowdsale_controller_address.hex())
        self.assertEqual(utils.remove_0x_head(self.open_window.wallet()), self.multisig_wallet.address.hex())
        self.assertEqual(self.open_window.tokenSupply(), token_supply)
        self.s.mine()
        self.assertEqual(self.open_window.price(), price)
        # Buyer 1 can buy tokens (through crowdsale controller)
        # max eth is 14,200,000
        bidder_1 = 2
        value_1 = 60000 * 10 ** 18 # 60k Ether
        self.open_window.buy(accounts[bidder_1], value=value_1)
        self.s.mine()
        # Token supply decreases
        self.assertEqual(self.open_window.tokenSupply(), token_supply - (60000 * 10 ** 20))
        # Tokens are stored in tokens bought mapping until they're claimed
        self.assertEqual(self.open_window.tokensBought(accounts[bidder_1]), 6000000 * 10 ** 18)
        # Token price doesn't change
        self.assertEqual(self.open_window.price(), price)
        # Only the crowdsale controller can buy tokens
        self.s.mine()
        self.assertRaises(
            TransactionFailed, self.open_window.buy, accounts[bidder_1], sender=keys[bidder_1], value=value_1)
        self.s.mine()
        # Buyer 2 buys tokens through the crowdsale controller finishing the token sale
        bidder_2 = 3
        value_2 = 120000 * 10 ** 18 # 120k Ether
        # Set crowdsale controlle balance to value_2, accounts for gas costs
        self.s.head_state.set_balance(accounts[bidder_2], 0)
        self.open_window.buy(accounts[bidder_2], value=value_2)
        # Open window gives a refund if when it runs out of tokens to sell
        self.assertEqual(self.s.head_state.get_balance(accounts[bidder_2]), 38000 * 10 ** 18)
        # Token supply decreases to 0
        self.assertEqual(self.open_window.tokenSupply(), 0)
        self.assertEqual(self.open_window.tokensBought(accounts[bidder_2]), 8200000 * 10 ** 18)
        # Token price doesn't change
        self.assertEqual(self.open_window.price(), price)
