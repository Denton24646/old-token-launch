pragma solidity 0.4.15;
import "Tokens/AbstractToken.sol";

/// @title Abstract open window contract
/// @author Karl - <karl.floersch@consensys.net>
contract OpenWindow {
    /*
     * Public functions
     */
    function buy(address receiver) public payable;
    function claimTokens(address receiver) public;
}