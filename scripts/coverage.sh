#! /bin/bash

output=$(nc -z localhost 8545; echo $?)
[ $output -eq "0" ] && trpc_running=true
if [ ! $trpc_running ]; then
  echo "Starting our own testrpc node instance"
  # Gives accounts enough ether to reach cap
  testrpc   --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201270,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201271,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201272,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201273,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201274,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201275,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201276,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201277,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201278,1000000000000000000000000"\
  --account="0xcad046afe14c18c9e7b28fead5d81ac733e5105a16ae514b63c083c186201279,1000000000000000000000000"\
  --gasLimit "0xfffffffffff" --gasPrice "0x01" -p "8555"\
  > /dev/null &
  trpc_pid=$!
  ./node_modules/.bin/solidity-coverage
fi
./node_modules/truffle/cli.js test -r blanket -R html-cov > coverage.html
if [ ! $trpc_running ]; then
  kill -9 $trpc_pid
fi