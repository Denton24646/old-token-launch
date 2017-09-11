pragma solidity 0.4.15;
import "Tokens/AbstractToken.sol";

/// @title Presale contract
/// @author Karl Floersh - <karl.floersch@consensys.net>
/// @dev Percents are entered with 10 ** 16 e.g. 6.3% is 63 ** 10 ** 17 and 10% is 10 ** 10 ** 18
contract Presale {
    /*
     *  Constants
     */
    uint256 constant public MAX_PERCENT_OF_PRESALE = 100 * 10**18;

    /*
     * Storage
     */
    mapping (address => uint256) public presaleAllocations;
    uint256 public percentOfPresaleSold = 0; 
    uint256 public totalSupply;
    address public crowdsaleController;
    Token public omegaToken;
    
    /*
     *  Modifiers
     */
    modifier isCrowdsaleController() {
        require(msg.sender == crowdsaleController);
        _;
    }

    /*
     *  Public functions
     */
    /// @dev Contract constructor function sets crowdsale controller
    function Presale() 
        public
    {
        crowdsaleController = msg.sender;
    }

    /*
     * External functions
     */
    /// @dev Allows the Omega team to give presale participants a percent of the presale
    /// @param buyer The address a percentage of the presale is allocated to
    /// @param _presalePercent The percent of presale allocated in exchange for usd
    function usdContribution(address buyer, uint256 _presalePercent) 
        external
        isCrowdsaleController
    {
        require(_presalePercent != 0 && buyer != 0x0);
        uint256 presalePercent = _presalePercent;
        uint256 maxPercentLeft = MAX_PERCENT_OF_PRESALE - percentOfPresaleSold;
        // Only allows the max percent of presale left to be allocated
        if (presalePercent > maxPercentLeft)
            presalePercent = maxPercentLeft;
        presaleAllocations[buyer] += presalePercent;
        percentOfPresaleSold += presalePercent;
    }

    /// @dev Sets up token claims for when trading starts
    /// @param _totalSupply Total supply of tokens
    /// @param _omegaToken Omega token
    function setupClaim(uint256 _totalSupply, Token _omegaToken) 
        external
        isCrowdsaleController
    {
        require(_omegaToken.balanceOf(this) >= _totalSupply && totalSupply == 0 && address(omegaToken) == 0x0);
        totalSupply = _totalSupply;
        omegaToken = _omegaToken;
    }

    /// @dev Claims tokens for presale participant after sale, permissions are in crowdsale controller
    /// @param receiver Tokens will be assigned to this address if set
    function claimTokens(address receiver)
        external
        isCrowdsaleController
    {   
        uint tokenCount = presaleAllocations[receiver] * totalSupply / 10**20; // 10**20 accounts for percent
        presaleAllocations[receiver] = 0;
        omegaToken.transfer(receiver, tokenCount);
    }
}