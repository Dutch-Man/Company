mv run.sh ../
rm -rf *
cmake ..
make clean
make
./../bin/Test
mv ../run.sh ./
