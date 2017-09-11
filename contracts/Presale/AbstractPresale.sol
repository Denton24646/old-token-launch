pragma solidity 0.4.15;
import 'Tokens/OmegaToken.sol';

/// @title Abstract presale contract
/// @author Karl Floersh - <karl.floersch@consensys.net>
contract Presale {
    /*
     *  Public functions
     */
    function setupClaim(uint256 _totalSupply, Token _omegaToken) external;
    function usdContribution(address buyer, uint256 presalePercent) external;
    function claimTokens(address receiver) external;
}
