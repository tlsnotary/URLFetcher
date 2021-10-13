#!/bin/bash

#this is the main entrypoint of the nitro-cli container

# add nitro-cli's dir to the path
PATH=$PATH:/aws-nitro-enclaves-cli-8af39b8cdcda6cc50549dee0d3f5c5c89d940e67/target/release
./app/make_enclave.sh