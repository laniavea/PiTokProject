// SPDX-License-Identifier: MIT
// pragma solidity >=0.8.0 <0.9.0;
pragma solidity 0.8.17;

import "./IERC20.sol";

contract PiContr {
    struct SequenceInfo {
        address owner;
        uint256 startIndex;
        uint256 endIndex;
        bytes32 txHash;
        string value;
    }

    uint public price;
    uint public blockSize = 1000;

    IERC20 public token;

    mapping(string => SequenceInfo) public sequences;
    mapping(uint => SequenceInfo[]) public blockToSequences;

    event SequenceBought(address indexed buyer, string sequence, uint256 startIndex, uint256 endIndex);

    constructor(address tokenAddress, uint tokenPrice) {
        token = IERC20(tokenAddress);
        price = tokenPrice;
    }

    function buySequence(string memory justSequence, string memory seqToMap, uint256 startIndex) public payable {
        uint256 length = bytes(justSequence).length;
        require(length >= 3 && length <= 8, "Length must be 3-8");
        require(sequences[seqToMap].owner == address(0), "Already owned");
        require(startIndex < 1_000_000, "Index is too big or small");

        require(token.balanceOf(msg.sender) >= price, "Not enought tokens");
        require(token.transferFrom(msg.sender, address(this), price), "Token transfer failed");

        uint256 endIndex = startIndex + length - 1;
        uint256 startBlock = startIndex / blockSize;
        uint256 endBlock = endIndex / blockSize;

        _checkOverlap(startBlock, startIndex, endIndex);

        if (endBlock != startBlock) {
            _checkOverlap(endBlock, startIndex, endIndex);
        }

        SequenceInfo memory info = SequenceInfo({
            owner: msg.sender,
            startIndex: startIndex,
            endIndex: endIndex,
            txHash: keccak256(abi.encodePacked(block.number, msg.sender, justSequence)),
            value: justSequence
        });

        sequences[seqToMap] = info;
        blockToSequences[startBlock].push(info);
        if (endBlock != startBlock) {
            blockToSequences[endBlock].push(info);
        }

        emit SequenceBought(msg.sender, justSequence, startIndex, endIndex);
    }

    function getSequenceInfo(string memory sequence) public view returns (
        address owner,
        uint256 startIndex,
        uint256 endIndex,
        bytes32 txHash,
        string memory value
    ) {
        SequenceInfo memory info = sequences[sequence];
        return (info.owner, info.startIndex, info.endIndex, info.txHash, info.value);
    }

    function _checkOverlap(uint blockIdx, uint startIndex, uint endIndex) internal view {
        SequenceInfo[] storage blockSequences = blockToSequences[blockIdx];
        for (uint i = 0; i < blockSequences.length; i++) {
            SequenceInfo storage s = blockSequences[i];
            if (!(endIndex < s.startIndex || startIndex > s.endIndex)) {
                revert("Overlap detected, Your sequence as a part of another sequence");
            }
        }
    }

    function checkSequence(string memory justSequence, string memory seqToMap, uint256 startIndex) public view returns (address, uint256, string memory) {
        uint256 length = bytes(justSequence).length;
        require(length >= 3 && length <= 8, "Length must be 3-8");
        require((startIndex < 1_000_000 || startIndex == 0), "Index is too big or small");

        SequenceInfo memory temp_seq = sequences[seqToMap];
        if (sequences[seqToMap].owner != address(0)) {
            return (temp_seq.owner, temp_seq.startIndex, temp_seq.value);
        }

        uint256 endIndex = startIndex + length - 1;
        uint256 startBlock = startIndex / blockSize;
        uint256 endBlock = endIndex / blockSize;

        (address owner, uint256 startSeqIndex, string memory value) = _checkOverlapWR(startBlock, startIndex, endIndex);

        if ((endBlock != startBlock) && (owner == address(0)) && (startSeqIndex == 0)){
            (owner, startSeqIndex, value) = _checkOverlapWR(endBlock, startIndex, endIndex);
        }

        return (owner, startSeqIndex, value);
    }

    function _checkOverlapWR(uint blockIdx, uint startIndex, uint endIndex) internal view returns (address, uint256, string memory) {
        SequenceInfo[] storage blockSequences = blockToSequences[blockIdx];
        for (uint i = 0; i < blockSequences.length; i++) {
            SequenceInfo storage s = blockSequences[i];
            if (!(endIndex < s.startIndex || startIndex > s.endIndex)) {
                return (s.owner, s.startIndex, s.value);
            }
        }

        return (address(0), 0, "");
    }
}
