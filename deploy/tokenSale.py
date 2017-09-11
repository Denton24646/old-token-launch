import json

# MULTISIG WALLET PARAMS
OWNER_ADDRESSES = [
        "9f7dfab2222a473284205cddf08a677726d786a0",
        "5210c4dcd7eb899a1274fd6471adec9896ae05aa",
        "1d805bC00b8fa3c96aE6C8FA97B2FD24B19a9801",
        "AcA7bD07A8c207f7964261c2Cf1e0FbFcff37836"
      ]
REQUIRED = 2

# DUTCH AUCTION PARAMS
DUTCH_AUCTION_FUNDING_GOAL = 62500*10**18
START_PRICE = 78125000000000000
FINAL_PRICE_MIN = 2637130801687760
BLOCKS_PER_DAY = 6000
AUCTION_DURATION_IN_BLOCKS = 30000

# CROWDSALE CONTROLLER PARAMS
MIN_PRESALE_TOKENS = 2000000;
DUTCH_AUCTION_USD_VALUE_CAP = 25000000;
PRESALE_USD_VALUE_CAP = 5000000;

token_sale_json = [
  {
    "type": "deployment",
    "file": "Wallets/MultiSigWallet.sol",
    "label": "MULTISIG_OMEGA",
    "params": [
      OWNER_ADDRESSES,
      REQUIRED
    ]
  },
  {
    "type": "deployment",
    "file": "DutchAuction/DutchAuction.sol",
    "label": "Dutch_Auction",
    "params": [
        "MULTISIG_OMEGA",
        DUTCH_AUCTION_FUNDING_GOAL,
        START_PRICE,
        FINAL_PRICE_MIN,
        BLOCKS_PER_DAY,
        AUCTION_DURATION_IN_BLOCKS
    ]
  },
  {
    "type": "deployment",
    "file": "CrowdsaleController/CrowdsaleController.sol",
    "label": "Crowdsale",
    "params": [
        "MULTISIG_OMEGA",
        "Dutch_Auction",
        MIN_PRESALE_TOKENS,
        DUTCH_AUCTION_USD_VALUE_CAP,
        PRESALE_USD_VALUE_CAP
    ]
  }
]

