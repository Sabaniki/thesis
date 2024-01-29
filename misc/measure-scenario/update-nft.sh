#!/bin/zsh
num=$1
ssh d2 "sudo ./update-nft.sh $num"
