pragma solidity 0.4.15;
import "Tokens/OmegaToken.sol";
import "CrowdsaleController/AbstractCrowdsaleController.sol";
import "Math/SafeMath.sol";

/// @title Dutch auction contract - distribution of Omega tokens using an auction
/// @author Karl Floersh - <karl.floersch@consensys.net>
/// Based on code by Stefan George: https://github.com/gnosis/gnosis-contracts/blob/dutch_auction/contracts/solidity/DutchAuction/DutchAuction.sol
contract DutchAuction {
    using SafeMath for uint;
    /*
     *  Events
     */
    event BidSubmission(address indexed sender, uint256 amount);

    /*
     *  Constants
     */
    uint256 constant public RATE_OF_DECREASE_PER_DAY = 15097573839662448;

    /*
     *  Storage
     */
    OmegaToken public omegaToken;
    CrowdsaleController public crowdsaleController;
    address public wallet;
    address public owner;
    uint256 public ceiling;
    uint256 public priceFactor;
    uint256 public startBlock;
    uint256 public blocksPerDay;
    uint256 public auctionDurationInBlocks;
    uint256 public totalReceived = 0;
    uint256 public finalPrice;
    mapping (address => uint) public bids;
    Stages public stage;

    enum Stages {
        AuctionDeployed,
        AuctionSetUp,
        AuctionStarted,
        AuctionEnded
    }

    /*
     *  Modifiers
     */
    modifier atStage(Stages _stage) {
        require(stage == _stage);
        _;
    }

    modifier isOwner() {
        require(msg.sender == owner);
        _;
    }

    modifier isCrowdsaleController() {
        require(msg.sender == address(crowdsaleController));
        _;
    }

    modifier isWallet() {
        // Only wallet is allowed to proceed
        require(msg.sender == wallet);
        _;
    }

    modifier isValidPayload(address receiver) {
         // Payload length has to have correct length and receiver should not be dutch auction or omega token contract
        require((msg.data.length == 4 || msg.data.length == 36)
            && receiver != address(this)
            && receiver != address(omegaToken));
        _;
    }

    modifier timedTransitions() {
        // Ends the sale after the stop price has been reached
        if (stage == Stages.AuctionStarted && calcTokenPrice() <= calcStopPrice())
            finalizeSale();
        _;
    }

    /*
     *  Public functions
     */
    /// @dev Contract constructor function sets owner
    /// @param _wallet Omega wallet
    /// @param _ceiling Auction ceiling
    /// @param _priceFactor Auction price factor
    function DutchAuction(address _wallet, uint256 _ceiling, uint256 _priceFactor, uint256 _blocksPerDay, uint256 _auctionDurationInBlocks)
        public
    {
        // Check for null arguments
        require(_wallet != 0x0 && _ceiling != 0 && _priceFactor != 0 && _blocksPerDay != 0 && _auctionDurationInBlocks != 0);
        owner = msg.sender;
        wallet = _wallet;
        ceiling = _ceiling;
        priceFactor = _priceFactor;
        blocksPerDay = _blocksPerDay;
        auctionDurationInBlocks = _auctionDurationInBlocks;
        stage = Stages.AuctionDeployed;
    }

    /// @dev Setup function sets external contracts' addresses
    /// @param _omegaToken Omega token initialized in crowdsale controller
    /// @param _crowdsaleController Crowdsaler controller
    function setup(OmegaToken _omegaToken, CrowdsaleController _crowdsaleController)
        public
        isOwner
        atStage(Stages.AuctionDeployed)
    {
        // Check for null arguments
        require(address(_omegaToken) != 0x0 && address(_crowdsaleController) != 0x0);
        omegaToken = _omegaToken;
        crowdsaleController = _crowdsaleController;
        // Validate token balance
        require(omegaToken.balanceOf(this) >= omegaToken.DUTCH_AUCTION_ALLOCATION());
        stage = Stages.AuctionSetUp;
    }

    /// @dev Starts auction and sets startBlock (only works if crowdsale controller is on MainSale stage)
    function startAuction()
        public
        isWallet
        atStage(Stages.AuctionSetUp)
    {   
        // Makes sure that the presale has already occurred
        require(crowdsaleController.stage() == CrowdsaleController.Stages.MainSale);
        stage = Stages.AuctionStarted;
        startBlock = block.number;
    }

    /// @dev Changes auction ceiling and start price factor before auction is started
    /// @param _ceiling Updated auction ceiling
    /// @param _priceFactor Updated start price factor
    function changeSettings(uint256 _ceiling, uint256 _priceFactor)
        public
        isWallet
        atStage(Stages.AuctionSetUp)
    {
        require(_ceiling > 0 && _priceFactor > 0);
        ceiling = _ceiling;
        priceFactor = _priceFactor;
    }

    /// @dev Calculates current token price
    /// @return Returns token price
    function calcCurrentTokenPrice()
        public
        timedTransitions
        returns (uint256)
    {
        if (stage == Stages.AuctionEnded)
            return finalPrice;
        return calcTokenPrice();
    }

    /// @dev Returns correct stage, even if a function with timedTransitions modifier has not yet been called yet
    /// @return Returns current auction stage
    function updateStage()
        public
        timedTransitions
        returns (Stages)
    {
        return stage;
    }

    /// @dev Allows to send a bid to the auction
    /// @param receiver Bid will be assigned to this address if set
    function bid(address receiver)
        public
        payable
        isValidPayload(receiver)
        timedTransitions
        atStage(Stages.AuctionStarted)
        returns (uint256 amount)
    {
        // If a bid is done on behalf of a user via ShapeShift, the receiver address is set
        if (receiver == 0x0)
            receiver = msg.sender;
        amount = msg.value;
        require(amount > 0);
        // Prevent that more than 90% of tokens are sold. Only relevant if cap not reached
        uint maxWei = omegaToken.DUTCH_AUCTION_ALLOCATION() * calcTokenPrice() / 10**omegaToken.DECIMALS() - totalReceived;
        uint maxWeiBasedOnTotalReceived = ceiling - totalReceived;
        if (maxWeiBasedOnTotalReceived < maxWei)
            maxWei = maxWeiBasedOnTotalReceived;
        // Only invest maximum possible amount
        if (amount > maxWei)
            amount = maxWei;
        // Forward funding to ether wallet
        wallet.transfer(amount);
        bids[receiver] = bids[receiver].add(amount);
        totalReceived = totalReceived.add(amount);
        if (amount == maxWei) {
            // When maxWei is equal to the big amount the auction is ended and finalizeSale is triggered
            finalizeSale();
            // Send change back to receiver address. In case of a ShapeShift bid the user receives the change back directly
            receiver.transfer(msg.value - amount);
        }
        BidSubmission(receiver, amount);
    }

    /// @dev Claims tokens for bidder after auction, permissions are in crowdsale controller
    /// @param receiver Tokens will be assigned to this address if set
    function claimTokens(address receiver)
        public
        isCrowdsaleController
    {
        uint256 tokenCount = (bids[receiver] * 10**omegaToken.DECIMALS()).div(finalPrice);
        bids[receiver] = 0;
        omegaToken.transfer(receiver, tokenCount);
    }

    /// @dev Calculates stop price
    /// @return Returns stop price
    function calcStopPrice()
        constant
        public
        returns (uint256)
    {
        // Blocks after 5 days
        // uint256 rate_of_decrease = RATE_OF_DECREASE_PER_DAY * auctionDurationInBlocks / blocksPerDay;
        // return priceFactor - rate_of_decrease; 
        return priceFactor.sub(RATE_OF_DECREASE_PER_DAY * auctionDurationInBlocks / blocksPerDay);
    }

    /// @dev Calculates token price
    /// @return Returns token price
    function calcTokenPrice()
        constant
        public
        returns (uint)
    {   
        // Calculated at 6,000 blocks mined per day
        // Auction calculated to stop after 5 days
        // uint256 block_diff = block.number - startBlock;
        // uint256 rate_of_decrease = RATE_OF_DECREASE_PER_DAY * block_diff / blocksPerDay;
        // return priceFactor - rate_of_decrease;
        uint256 numberOfBlocks = block.number - startBlock; 
        if (numberOfBlocks > auctionDurationInBlocks)
            numberOfBlocks = auctionDurationInBlocks - 1;
        return priceFactor.sub(RATE_OF_DECREASE_PER_DAY * (numberOfBlocks).div(blocksPerDay));
    }

    /*
     *  Private functions
     */
    /// @dev Finishes dutch auction and finalizes the token sale or starts the open window sale depending on how it ends
    function finalizeSale()
        private
    {
        stage = Stages.AuctionEnded;
        finalPrice = calcTokenPrice();
        uint256 tokensLeft = omegaToken.DUTCH_AUCTION_ALLOCATION().sub((totalReceived * 10**omegaToken.DECIMALS()).div(finalPrice));
        // Auction contract transfers all unsold tokens to the crowdsale controller
        omegaToken.transfer(address(crowdsaleController), tokensLeft);
        if (totalReceived == ceiling)
            crowdsaleController.startOpenWindow(tokensLeft, finalPrice);
        else
            crowdsaleController.finishFromDutchAuction();
    }
}
