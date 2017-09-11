from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed, utils

class TestContract(AbstractTestContracts):
    """
    run test with python -m unittest tests.python.presale.test_presale
    """

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
        dutch_auction_address = accounts[2]
        crowdsale_controller_address = accounts[0]
        self.s.mine()
        # Create Omega token
        self.omega_token= self.create_contract('Tokens/OmegaToken.sol',
                                                  params=(dutch_auction_address, self.multisig_wallet.address))
        # Create presale
        self.presale= self.create_contract('Presale/Presale.sol',
                                                  params=())

        self.assertEqual(self.presale.MAX_PERCENT_OF_PRESALE(), 100 * 10 **18);
        self.assertEqual(self.presale.percentOfPresaleSold(), 0);
        self.assertEqual(utils.remove_0x_head(self.presale.crowdsaleController()), crowdsale_controller_address.hex())
        
        # Buyer can buy presale tokens as soon as it's initialized
        token_supply = 6300000 * 10 ** 18
        # Presale reverts if it doesn't have a token balance equal to the token_supply when setupClaim is called
        self.assertRaises(TransactionFailed, self.presale.setupClaim, token_supply, self.omega_token.address)
        # Omega team can allocate tokens to presale participants
        buyer_1 = 4
        # 5.5%
        percent_of_presale_1 = 55 * 10 ** 17
        self.s.mine()
        self.presale.usdContribution(accounts[buyer_1], percent_of_presale_1)
        self.assertEqual(self.presale.percentOfPresaleSold(), percent_of_presale_1)
        self.assertEqual(self.presale.presaleAllocations(accounts[buyer_1]), percent_of_presale_1)
        # Omega team cannot allocate more then 100% of presale tokens
        buyer_2 = 5
        percent_of_presale_2 = 95* 10 ** 18
        buyer_3 = 6
        # 94.5%
        percent_of_presale_3 = 945 * 10 ** 17
        self.presale.usdContribution(accounts[buyer_3], percent_of_presale_3)
        self.assertEqual(self.presale.percentOfPresaleSold(), percent_of_presale_1 + percent_of_presale_3)
        self.assertEqual(self.presale.presaleAllocations(accounts[buyer_3]), percent_of_presale_3)
        # Transfer necessary funds to the presale
        self.omega_token.transfer(self.presale.address, token_supply, sender=keys[2])
        # Setup the presale
        self.presale.setupClaim(token_supply, self.omega_token.address)
        self.assertEqual(utils.remove_0x_head(self.presale.omegaToken()), self.omega_token.address.hex());
        self.assertEqual(self.presale.totalSupply(), token_supply)
        # Buyers can claim there tokens (permissions will be in the crowdsale controller)
        self.presale.claimTokens(accounts[buyer_1])
        self.omega_token.balanceOf(accounts[buyer_1])
        self.presale.claimTokens(accounts[buyer_2])
        self.omega_token.balanceOf(accounts[buyer_2])
        self.omega_token.balanceOf(self.presale.address)

