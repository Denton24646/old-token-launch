from ..abstract_test import AbstractTestContracts, accounts, keys, TransactionFailed

class TestContract(AbstractTestContracts):
    """
    run test with python -m unittest tests.python.crowdsale_controller.test_crowdsale_controller_math
    """

    BLOCKS_PER_DAY = 6000

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
                                                  params=(self.multisig_wallet.address, 62500 * 10**18, 78125000000000000))
        # Create Omega token
        self.crowdsale_controller = self.create_contract('CrowdsaleController/CrowdsaleController.sol', 
                                                        params=(self.multisig_wallet.address, self.dutch_auction, 2500000000000000))
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
        # Record current state
        snapshot = self.s.snapshot()
        # Math
        # Sets up dutch auction total received for presale math
        bidder_1 = 4
        total_received = 62500 * 10 ** 18 #  62.5k Ether
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 2000000 * 10**18)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *3
        total_received = 62500 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 2000000*10**18)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY * 5 - 1500
        self.dutch_auction.bid(sender=keys[bidder_1], value=62500 * 10**18)
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 2599485861182520710363923)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *1
        total_received = 20000 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *4
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 2022400000000002847539200)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *5-1000
        total_received = 62500 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 3234115138592752785592995)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *3
        total_received = 32500 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *2
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 3286400000000004629245124)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY * 5 -10
        self.dutch_auction.bid(sender=keys[bidder_1], value=30500 * 10**18)
        self.s.head_state.block_number += 10
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 3084160000000004342777963)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *3
        total_received = 32500 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *2
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 3286400000000004629245124)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *2
        total_received = 40500 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *3
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 4095360000000005767136537)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY * 5 - 500
        self.dutch_auction.bid(sender=keys[bidder_1], value=62500 * 10**18)
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 4278702397743304433741783)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *1
        total_received = 55000 * 10**18
        self.dutch_auction.bid(sender=keys[bidder_1], value=total_received)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY *4
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 5561600000000007834669522)
        self.s.revert(snapshot)
        self.s.head_state.block_number += self.BLOCKS_PER_DAY * 5 -10
        self.dutch_auction.bid(sender=keys[bidder_1], value=62500 * 10**18)
        self.dutch_auction.updateStage()
        # Check that the presale token supply is calculated correctly
        self.assertEqual(int(self.crowdsale_controller.calcPresaleTokenSupply()), 6260266622642294731968069)
