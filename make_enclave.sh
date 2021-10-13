#!/bin/bash

echo "asking docker for image urlfetcher..."
tmp_dir1=$(mktemp -d)
docker save urlfetcher > $tmp_dir1/urlfetcher.tar
tmp_dir2=$(mktemp -d)
tar -xvf $tmp_dir1/urlfetcher.tar -C $tmp_dir2
configId=$(cat $tmp_dir2/manifest.json | awk -F 'Config\":\"' '{print $2}' | awk -F '.json' '{print $1}')
configPath=$tmp_dir2/$configId.json
dirlist=$(find $tmp_dir2 -mindepth 1 -maxdepth 1 -type d)
for dir in $dirlist
do
    # extract layer into a new dir
    id=$(echo $dir | cut -f4 -d/)
    mkdir $tmp_dir1/$id
    tar -xvf $dir/layer.tar -C $tmp_dir1/$id
    # remove non-deterministic data
    find $tmp_dir1/$id -type d -iname __pycache__ -exec rm -rv {} +
    rm -rf $tmp_dir1/$id/root
    rm -rf $tmp_dir1/$id/var
    # replace orig layer with a deterministic one and change hash in config
    tar --mtime='UTC 2020-01-01' -cf $tmp_dir1/$id.tar -C $tmp_dir1/$id .
    oldSha=$(sha256sum $dir/layer.tar | cut -f1 -d' ')
    newSha=$(sha256sum $tmp_dir1/$id.tar | cut -f1 -d' ')
    cp $tmp_dir1/$id.tar $dir/layer.tar
    sed -i "s/$oldSha/$newSha/" $configPath
done
tar -cf $tmp_dir1/deterministic.tar -C $tmp_dir2/ .
docker image rm urlfetcher
docker load -i $tmp_dir1/deterministic.tar
nitro-cli build-enclave --docker-uri urlfetcher --output-file /tmp/urlfetcher.eif
echo "Please make sure that PCR0 PCR1 PCR2 are deterministic"
rm -rf $tmp_dir1 $tmp_dir2



