pragma solidity 0.4.15;
import "Tokens/OmegaToken.sol";
import "Math/SafeMath.sol";

/// @title Open window contract
/// @author Karl Floersh - <karl.floersch@consensys.net>
contract OpenWindow {
    using SafeMath for uint;
    /*
     * Events
     */
    event PurchasedTokens(address indexed purchaser, uint amount);

    /*
     *  Constants
     */
    uint256 constant public SALE_LENGTH = 30 days;

    /*
     * Storage
     */
    address public wallet;
    address public crowdsaleController;
    OmegaToken public omegaToken;
    uint256 public price;
    uint256 public startTime;
    uint256 public tokenSupply;
    mapping (address => uint) public tokensBought;

    /*
     * Modifiers
     */
    modifier isCrowdsaleController() {
        require(msg.sender == crowdsaleController);
        _;
    }

    modifier timedTransitions() {
        // Ends the sale after 30 days
        if (now > startTime + SALE_LENGTH)
            finalizeSale();
        _;
    }

    /*
     * Public functions
     */
    /// @dev Contract constructor function sets crowdsale controller
    function OpenWindow()
        public
    {
        crowdsaleController = msg.sender;
    }

    /// @dev Sets up the open window sale
    /// @param _tokenSupply The number of OMT available to sell
    /// @param _price Price of the token in Wei (OMT/Wei pair price)
    /// @param _wallet The sale's beneficiary address 
    /// @param _omegaToken Omega token
    function setupSale(uint256 _tokenSupply, uint256 _price, address _wallet, OmegaToken _omegaToken) 
        public
        isCrowdsaleController
    {
        require(_tokenSupply != 0 && _price != 0 && _wallet != 0x0 && address(_omegaToken) != 0x0);
        tokenSupply = _tokenSupply;
        price = _price;
        wallet = _wallet;
        omegaToken = _omegaToken;
        startTime = now;
    }

    /// @dev Exchanges ETH for OMT (sale function)
    /// @notice You're about to purchase the equivalent of `msg.value` Wei in OMT tokens
    function buy(address receiver)
        public
        payable
        timedTransitions
        isCrowdsaleController
    {   
        // Check that msg.value is not 0
        uint256 amount = msg.value;
        require(amount != 0);
        uint256 maxWei = tokenSupply.mul(price) / 10**omegaToken.DECIMALS();
        //Cannot purchase more tokens than this contract has available to sell
        if (amount > maxWei) {
            amount = maxWei;
            // Send change back to receiver address. In case of a ShapeShift bid the user receives the change back directly
            receiver.transfer(msg.value.sub(amount));
        }
        uint256 tokenPurchase = (amount * 10**omegaToken.DECIMALS()).div(price);
        // Forward received ether to the wallet
        wallet.transfer(amount);
        // Transfer the sum of tokens tokenPurchase to the msg.sender
        tokenSupply = tokenSupply.sub(tokenPurchase);
        tokensBought[receiver] = tokensBought[receiver].add(tokenPurchase);
        if (maxWei == amount)
            finalizeSale();
        PurchasedTokens(msg.sender, tokenPurchase);
    }

    /// @dev Claims tokens for buyer after sale, permissions are in crowdsale controller
    /// @param receiver Tokens will be assigned to this address if set
    function claimTokens(address receiver)
        public
        isCrowdsaleController
    {
        uint tokenCount = tokensBought[receiver];
        tokensBought[receiver] = 0;
        omegaToken.transfer(receiver, tokenCount);
    }

    /*
     *  Private functions
     */
    /// @dev Finishes the open window and then the overall token sale
    function finalizeSale()
        private
    {
        // Finalizes the token sale
        omegaToken.transfer(crowdsaleController, tokenSupply);
        tokenSupply = 0;
    }
}
