# Coisas pro tf-pose-estimation
sudo apt-get install libllvm-7-ocaml-dev libllvm7 llvm-7 llvm-7-dev llvm-7-doc llvm-7-examples llvm-7-runtime
echo "export LLVM_CONFIG=/usr/bin/llvm-config-7" >> ~/.bashrc
sudo apt-get install swig

cd tf_pose_estimation
sudo -H pip3 install -r requirements.txt
cd tf_pose/pafprocess
swig -python -c++ pafprocess.i && python3 setup.py build_ext --inplace

cd ../../../

# coisas para o 3d-pose-baseline
mkdir data
cd data
wget https://www.dropbox.com/s/e35qv3n6zlkouki/h36m.zip
unzip h36m.zip
cd ..
FILEID=0BxWzojlLp259MF9qSFpiVjl0cU0
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=$FILEID" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=$FILEID" -O experiments.tar.gz && rm -rf /tmp/cookies.txt
tar xvzf experiments.tar.gz

# coisas gerais
sudo apt-get install opencv
sudo pip3 install opencv opencv-python opencv-contrib-python

echo "pronto!"
