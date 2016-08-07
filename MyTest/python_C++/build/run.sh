mv run.sh ../
rm -rf *
cmake ..
make clean
make
./../bin/Test a
mv ../run.sh ./
